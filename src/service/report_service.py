from src.database.postgres_client import SessionLocal
from src.models.reports import Report
from src.repository.analysis_repository import Analysis_Repository
from src.service.analysis_service import Analysis_Service
from src.repository.answer_repository import Answer_Repository
from src.service.comment_service import Comment_Service
from src.repository.report_repository import Report_Repository
from src.service.oauth_service import Oauth_Service
from src.utils.schemas import GenerateReport, UpdatedReport, ReportQuotaResponse, StatusReport, ResponseAnswers
from src.utils.exceptions import BadGateway, BadRequest, Forbidden
from src.utils.processing import extract_youtube_video_id
from src.utils.logging import get_logger
from src.settings.config import settings
from fastapi import HTTPException, BackgroundTasks
from google import genai
from google.genai import types, errors
from uuid import UUID
from fpdf import FPDF
import json
import re
import asyncio
from datetime import date

logger = get_logger("report_service")


GEMINI_API_KEY = settings.GEMINI_API_KEY
REPORT_MONTHLY_LIMIT = 5

class Report_Service:

    def __init__(self, repository: Report_Repository, comment_service: Comment_Service, analysis_service: Analysis_Service,
                 oauth_service: Oauth_Service):

        self.repository = repository
        self.oauth_service = oauth_service
        self.comment_service = comment_service
        self.analysis_service = analysis_service
        self.gemini_service = genai.Client(api_key = GEMINI_API_KEY)
        self.model = "gemini-2.5-flash-lite"
        self.prompt = """
# Papel e objetivo

Você é um analista de dados especialista em comportamento de comunidades digitais, análise de audiência e interpretação de feedback social.

Sua tarefa é analisar comentários de um vídeo do YouTube e gerar uma análise estatística, comportamental e sentimental da recepção do conteúdo pelo público.

Você receberá dois conjuntos de informações:
- O contexto fornecido pelo criador do canal.
- Os comentários publicados no vídeo do YouTube.

Utilize o contexto do criador para compreender os objetivos e as necessidades do canal e personalizar os insights e as recomendações. Utilize os comentários como fonte exclusiva para as métricas e as conclusões sobre a percepção e o comportamento da audiência.

Não invente informações nem apresente suposições como fatos.

A análise deve identificar:
- Percepção geral do público.
- Predominância emocional.
- Padrões de comportamento.
- Assuntos mais discutidos.
- Críticas recorrentes.
- Elogios recorrentes.
- Oportunidades de conteúdo.
- Sinais de engajamento emocional ou polêmica.
- Intenção e interesse da audiência.

Caso a quantidade de comentários seja pequena, reduza o nível de confiança da análise e informe essa limitação nos insights.

# Regras obrigatórias

- Retorne exclusivamente um JSON válido, sem explicações fora da estrutura.
- Não utilize HTML.
- Utilize linguagem analítica, objetiva e profissional.
- Respeite exatamente os nomes e os tipos dos campos definidos na estrutura JSON.
- Não adicione campos extras ao objeto JSON principal.
- Todos os percentuais devem variar entre 0 e 100.
- Os percentuais de sentimento devem somar 100%, considerando possíveis diferenças de arredondamento.
- Não invente dados, temas, comentários, citações ou informações que não estejam fundamentados nos dados fornecidos.
- Diferencie evidências observadas de interpretações e recomendações.
- Caso não existam informações suficientes para determinada análise, informe a limitação no relatório ou utilize uma lista vazia, conforme as regras específicas de cada campo.
- Os campos `recurring_themes` e `recommendations` devem estar sempre presentes no JSON, mesmo quando seus valores forem listas vazias.
- Todo texto do JSON deve utilizar aspas duplas válidas e caracteres devidamente escapados quando necessário.
- Não inclua comentários, vírgulas finais indevidas ou blocos Markdown envolvendo o JSON.

# Estrutura obrigatória do JSON

Retorne exatamente os seguintes campos e tipos:

{
  "markdown": "Relatório completo em Markdown",
  "comments_positive": 0,
  "comments_negative": 0,
  "recurring_themes": [
    {
      "theme": "Nome do tema",
      "description": "Descrição breve do assunto discutido",
      "percentage_relevance": 0
    }
  ],
  "recommendations": [
    {
      "recommendation": "Ação prática recomendada para o canal",
      "justification": "Justificativa baseada nos comentários analisados e, quando pertinente, no contexto do criador"
    }
  ]
}

# Regras para os campos principais

## markdown

Gere o relatório completo em Markdown seguindo exatamente a estrutura definida neste prompt.

O relatório deve refletir os comentários analisados e pode utilizar o contexto do criador para interpretar os resultados e personalizar as recomendações.

## comments_positive

Informe a quantidade de comentários classificados como positivos.

## comments_negative

Informe a quantidade de comentários classificados como negativos.

Classifique os comentários com critérios consistentes:
- Positivos: expressam aprovação, satisfação, elogio, apoio ou outra manifestação claramente favorável ao conteúdo.
- Negativos: expressam insatisfação, reprovação, crítica ou outra manifestação claramente desfavorável ao conteúdo.
- Neutros: não apresentam sentimento claramente positivo ou negativo, como perguntas objetivas, informações, observações sem avaliação explícita ou comentários ambíguos.

Comentários neutros não devem ser contabilizados como positivos ou negativos.

Considere a quantidade de comentários efetivamente analisados. Não conte o mesmo comentário mais de uma vez e não confunda quantidade de comentários com quantidade de frases ou sentimentos identificados.

Comentários com sentimentos mistos devem ser classificados conforme o sentimento predominante, quando identificável. Caso contrário, classifique-os como neutros.

# Regras para métricas de sentimento

Calcule os percentuais com base na quantidade total de comentários efetivamente analisados.

- Positivo: proporção de comentários positivos.
- Negativo: proporção de comentários negativos.
- Neutro: proporção de comentários neutros.

Os três percentuais devem somar aproximadamente 100%, considerando arredondamentos.

A predominância de sentimento deve corresponder à categoria com maior percentual. Em caso de empate, informe que não há predominância clara.

Se nenhum comentário puder ser classificado com segurança, informe a limitação e evite apresentar conclusões categóricas.

# Regras para temas recorrentes

O campo `recurring_themes` será utilizado para preencher o card "Temas Mais Recorrentes nos Comentários".

- Identifique de 3 a 5 temas recorrentes, quando houver dados suficientes.
- Ordene os temas do mais relevante para o menos relevante.
- Cada tema deve conter `theme`, `description` e `percentage_relevance`.
- A relevância percentual representa a proporção estimada de comentários que abordam o tema.
- Calcule a relevância considerando a quantidade de comentários relacionados ao tema em relação ao total de comentários analisados.
- Um comentário pode abordar mais de um tema, portanto os percentuais não precisam somar 100%.
- Utilize somente temas identificáveis nos comentários fornecidos.
- Não invente temas para preencher a lista.
- Não confunda a relevância de um tema com o sentimento positivo ou negativo associado a ele.
- Se os comentários forem insuficientes para identificar temas confiáveis, retorne uma lista vazia.

# Regras para recomendações estratégicas

O campo `recommendations` será utilizado para preencher o card "Recomendações Estratégicas para seu Canal".

- Gere de 3 a 5 recomendações práticas, quando houver informações suficientes.
- Cada recomendação deve conter uma ação concreta e sua justificativa.
- Priorize oportunidades de novos vídeos, aprofundamento de assuntos, esclarecimento de dúvidas recorrentes, melhorias no conteúdo e interesses demonstrados pela audiência.
- Utilize o contexto do criador para adaptar as recomendações aos objetivos, ao público-alvo e às necessidades declaradas para o canal.
- Fundamente as recomendações nos comentários analisados. O contexto do criador pode orientar a aplicação das recomendações, mas não substitui as evidências dos comentários.
- Evite recomendações genéricas que poderiam ser aplicadas a qualquer canal.
- Não trate hipóteses como fatos.
- Quando houver divergência entre os objetivos do criador e os interesses demonstrados nos comentários, destaque essa divergência somente quando houver evidências suficientes.
- Não recomende ações com base em dúvidas, críticas ou interesses que não tenham sido identificados nos dados.
- Se não houver informações suficientes para recomendações confiáveis, retorne uma lista vazia.

# Contexto adicional fornecido pelo criador do canal

Você receberá informações fornecidas pelo próprio criador sobre seu canal. Elas podem incluir objetivos, público-alvo, nicho, estratégia de conteúdo, dificuldades, expectativas e outros aspectos relevantes.

Essas informações serão fornecidas separadamente dos comentários, na seção `CONTEXTO_DO_CRIADOR`.

## Como utilizar o contexto

- Utilize as respostas do criador para compreender os objetivos, o posicionamento e as necessidades específicas do canal.
- Cruze essas informações com os padrões identificados nos comentários para gerar insights e recomendações mais relevantes e personalizadas.
- Utilize o contexto para orientar as recomendações estratégicas, relacionando os interesses demonstrados pela audiência aos objetivos declarados pelo criador.
- Não trate as declarações do criador como evidências da opinião da audiência.
- A percepção do público, os sentimentos, os temas recorrentes, os elogios e as críticas devem ser identificados exclusivamente a partir dos comentários fornecidos.
- Não utilize as respostas do criador para inventar sentimentos, temas recorrentes, críticas, elogios ou comportamentos que não estejam presentes nos comentários.
- Caso exista divergência entre os objetivos do criador e os interesses demonstrados nos comentários, destaque essa divergência nos insights ou nas recomendações, quando houver evidências suficientes.
- Se o contexto estiver ausente, incompleto ou não for relevante para determinada análise, prossiga utilizando os comentários disponíveis, sem inventar informações.
- Considere as respostas do criador como contexto complementar, e não como substituição dos dados dos comentários.

# Estrutura obrigatória do relatório Markdown

O campo `markdown` deve conter as seguintes seções, nesta ordem:

## Resumo Geral

- Total de comentários analisados: X
- Nível de confiança da análise: Alto, Médio ou Baixo
- Predominância de sentimento: Positivo, Negativo ou Neutro, conforme as métricas calculadas

### Resumo Analítico

Apresente um resumo objetivo da percepção pública sobre o vídeo, considerando a distribuição de sentimentos, os temas mais relevantes e os padrões identificados.

O contexto do criador pode ser utilizado para contextualizar os objetivos do canal, mas não deve ser apresentado como evidência da opinião da audiência.


## Métricas de Sentimento

| Sentimento | Percentual |
| --- | --- |
| Positivo | X% |
| Negativo | X% |
| Neutro | X% |

Apresente percentuais coerentes com a classificação dos comentários e com as regras de cálculo estabelecidas neste prompt.


## Principais Elogios

Liste os elogios recorrentes identificados nos comentários.

Se não houver elogios identificáveis, informe que não foram identificados elogios recorrentes suficientes.


## Principais Críticas

Liste as críticas recorrentes identificadas nos comentários.

Se não houver críticas identificáveis, informe que não foram identificadas críticas recorrentes suficientes.


## Comentários de Destaque

Apresente comentários de destaque somente quando o texto original estiver disponível e houver motivo claro para destacá-los.

Priorize comentários que ilustrem padrões relevantes, dúvidas recorrentes, elogios, críticas ou manifestações significativas de interesse.

Não invente citações nem atribua aos comentários um significado que eles não sustentem.

Se não houver comentários que mereçam destaque, informe essa limitação.


## Insights Comportamentais

Apresente insights acionáveis sobre o comportamento e o interesse da audiência.

Utilize evidências dos comentários para identificar padrões de interesse, dúvidas, engajamento emocional, discordâncias, possíveis polêmicas e oportunidades de conteúdo.

Quando relevante, relacione esses padrões aos objetivos declarados pelo criador, diferenciando claramente os dados observados das interpretações.

Não generalize o comportamento de toda a audiência a partir de poucos comentários.


## Conclusão

Apresente uma conclusão objetiva sobre a recepção do vídeo e o comportamento observado na audiência.

Considere a distribuição dos sentimentos, os temas recorrentes, os elogios, as críticas e as limitações dos dados. Utilize o contexto do criador apenas para contextualizar os resultados e suas possíveis aplicações estratégicas.

# Dados de entrada

`CONTEXTO_DO_CRIADOR`:

{{contexto_criador}}

`COMENTARIOS_DO_VIDEO`:

{{comentarios_video}}
"""

    async def create_report (self, schema: GenerateReport, user_id: str, background_tasks: BackgroundTasks):

        try:
            logger.info("Starting report creation request for user %s, video_url %s", user_id, schema.video_url)
            stats = await self.repository.report_done_count_by_user_id(user_id)

            if stats.reports_used >= 5:
                logger.warning("Report creation rejected: limit reached for user %s", user_id)
                raise BadRequest(detail = "Limite de 5 relatórios mensais atingido")

            youtube_video_id = extract_youtube_video_id(schema.video_url)

            if not youtube_video_id:
                logger.warning("Report creation failed: invalid video URL %s", schema.video_url)
                raise BadRequest(detail = "Url do vídeo inválida")
            
            exists_report = await self.analysis_service.get_analysis_by_youtube_video_id(youtube_video_id, user_id)

            if exists_report:
                logger.warning("Report creation rejected: video_id %s already has a report for user %s", youtube_video_id, user_id)
                raise BadRequest(detail = f"Relatório do video ID: {youtube_video_id} já gerado")
            
            access_token, refresh_token = await self.oauth_service.get_tokens_by_user_id(user_id)
            youtube_service = self.oauth_service.get_youtube_service(access_token, refresh_token)

            channel_id_by_video, title = await self.comment_service.get_channel_id_title_by_video_id(youtube_service, youtube_video_id)
            channel_id_by_user = await self.oauth_service.get_channel_id_by_user_id(user_id)
            logger.info(
                "Comparing YouTube channel ids for user %s: video_channel_id = %s, user_channel_id = %s",
                user_id,
                channel_id_by_video,
                channel_id_by_user)

            if channel_id_by_video != channel_id_by_user:
                logger.warning(
                    "Report creation rejected: video_id %s does not belong to user %s channel (video_channel_id=%s, user_channel_id=%s)",
                    youtube_video_id,
                    user_id,
                    channel_id_by_video,
                    channel_id_by_user)
                raise Forbidden(detail = f"Vídeo ID {youtube_video_id} não pertence ao seu canal")
            
            logger.info(
                "Video ownership validated successfully for user %s and video_id %s",
                user_id,
                youtube_video_id)
            
            user_reports_key = f"{self.repository.cache_key}_{user_id}"

            try:
                new_analysis = await self.analysis_service.create_analysis(user_id, schema.video_url, youtube_video_id)
                new_report = await self.repository.create_report(new_analysis.id)
                await self.repository.session.commit()
            except Exception as e:
                logger.error("Failed to create analysis/report pair for user %s, video_id %s: %s", user_id, youtube_video_id, str(e), exc_info=True)
                raise

            try:
                keys = await self.repository.cache.keys(f"{user_reports_key}*")
                if keys:
                    await self.repository.cache.delete(*keys)
                    logger.info("Report cache invalidated for user %s after report creation", user_id)
            except Exception as e:
                logger.warning("Failed to invalidate report cache for user %s: %s", user_id, str(e), exc_info=True)

            background_tasks.add_task(self.generate_report, youtube_video_id, new_report.id, new_analysis.id, youtube_service, title, user_id)

            logger.info("Report creation background task started: report_id %s, video_id %s", new_report.id, youtube_video_id)
            return {
                "report_id": new_report.id, "status": new_analysis.status
            }

        except HTTPException:
            raise
        except Exception as e:
            await self.repository.session.rollback()
            logger.error("Unexpected error starting report creation for user %s: %s", user_id, str(e), exc_info=True)
            raise BadGateway
        
    async def generate_report (self, video_id: str, report_id: UUID, analysis_id: UUID, youtube_service, title: str, user_id: str):

        async with SessionLocal() as session:
            repository = Report_Repository(session)
            analysis_repository = Analysis_Repository(session)
            answer_repository = Answer_Repository(session)
            comment_service = Comment_Service()

            try:
                logger.info("Background Task: Generating report %s for video_id %s", report_id, video_id)
                comments = await comment_service.get_comments_by_video_id(youtube_service, video_id)

                if not comments:
                    raise ValueError("No comments returned by YouTube")

                comments_processed = comment_service.processing_comments(comments)

                if not comments_processed:
                    raise ValueError("No valid comments found")
                
                answers_by_user = await answer_repository.get_answers_by_user(user_id)

                if not answers_by_user:
                    raise ValueError("No creator context")
                    
                creator_context = [
                    {
                        "question_id": question_id,
                        "question": question,
                        "answer_id": answer_id,
                        "answer": answer,
                    }
                for question_id, question, answer_id, answer in answers_by_user]

                report_dict = await self.analyze_comments(comments_processed, creator_context)

                if not report_dict:
                    logger.error("Background Task: Gemini analysis failed for report %s", report_id)
                    raise RuntimeError("Gemini analysis returned no data")

                markdown = report_dict.get("markdown")
                comments_positive = report_dict.get("comments_positive")
                comments_negative = report_dict.get("comments_negative")
                recurring_themes = report_dict.get("recurring_themes")
                recommendations = report_dict.get("recommendations")

                await analysis_repository.update_analysis_done_by_id(analysis_id)
                await repository.update_report_done_by_id(report_id, self.prompt, title, markdown, len(comments_processed),
                                                              comments_positive, comments_negative, recurring_themes, recommendations)
                await session.commit()
                logger.info("Background Task: Report %s successfully generated and saved", report_id)

            except ValueError as e:
                logger.warning("Background Task: Report %s generation rejected: %s", report_id, str(e))
                await session.rollback()
                try:
                    await analysis_repository.update_analysis_failed_by_id(analysis_id)
                    await repository.update_report_failed_by_id(report_id)
                    await session.commit()
                    logger.info("Background Task: Report ID %s marked as failed", report_id)
                except Exception:
                    logger.error("Background Task: Failed to persist failure state for report_id %s", report_id, exc_info=True)
                return

            except Exception as e:
                logger.error("Background Task: Unexpected error generating report_id %s: %s", report_id, str(e), exc_info=True)
                await session.rollback()
                try:
                    await analysis_repository.update_analysis_failed_by_id(analysis_id)
                    await repository.update_report_failed_by_id(report_id)
                    await session.commit()
                    logger.info("Background Task: Report %s marked as failed", report_id)
                except Exception:
                    logger.error("Background Task: Failed to persist failure state for report_id %s", report_id, exc_info=True)
                return
        
    async def analyze_comments (self, comments: list, creator_context: list[dict]) -> dict:

        try:
            logger.info("Sending %s comments to Gemini API for analysis", len(comments))
            content_for_gemini = "\n".join(f"{i+1}. {c}" for i, c in enumerate(comments))

            response = await self.gemini_service.aio.models.generate_content(
                model = self.model,
                config = types.GenerateContentConfig(
                    system_instruction = self.prompt,
                    temperature = 0.2,
                    max_output_tokens = 6000,
                    response_mime_type = "application/json"
                ),
                contents=f"""
                    CONTEXTO_DO_CRIADOR:
                    {creator_context}

                    COMENTARIOS_DO_VIDEO:
                    {content_for_gemini}
                """
            )
            logger.info("Gemini API response received successfully")
            return json.loads(response.text)

        except errors.APIError as error:
            logger.error("Gemini API Error: Code %s - %s", error.code, error.message)
            return
        
        except Exception as e:
            logger.error("Unexpected error during Gemini analysis: %s", str(e), exc_info=True)
            return
        
        
    async def get_report_by_id (self, report_id: UUID, user_id: str):

        try:
            await self.analysis_service.get_analysis_by_report_id(report_id, user_id)

            report = await self.repository.get_report_by_id(report_id)

            logger.info("Retrieved report details for report_id %s", report_id)

            return {
                "id": report.id,
                "title": report.title,
                "url": report.analysis.video_url,
                "report": report.markdown,
                "status": report.analysis.status,
                "comments_processed": report.comments_processed,
                "comments_positive": report.comments_positive,
                "comments_negative": report.comments_negative,
                "recurring_themes": report.recurring_themes,
                "recommendations": report.recommendations,
                "created_at": report.created_at
            }
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error retrieving report_id %s: %s", report_id, str(e), exc_info=True)
            raise BadGateway
    
    async def get_reports_stats_by_user_id (self, user_id: str, status: StatusReport | None, start_date: date, end_date: date):

        try:
            if start_date > end_date:
                raise BadRequest(detail = "Intervalo de datas inválido")
            
            if (end_date - start_date).days > 45:
                raise BadRequest(detail = "Limite de intervalo inválido")

            user_reports_key = f"{self.repository.cache_key}_{user_id}_{status}_{start_date}_{end_date}"

            reports_cache = await self.repository.cache.get(user_reports_key)

            if reports_cache:
                logger.info("Retrieved reports from cache for user %s", user_id)
                return json.loads(reports_cache)

            reports = await self.repository.get_reports_by_user_id(user_id, status, start_date, end_date)
            stats = await self.repository.get_stats_by_user_id(user_id, status, start_date, end_date)
            
            result_reports = [
                {
                    "id": id,
                    "title": title,
                    "url": url,
                    "report": markdown,
                    "status": status,
                    "comments_processed": comments_processed,
                    "comments_positive": comments_positive,
                    "comments_negative": comments_negative,
                    "recurring_themes": recurring_themes,
                    "recommendations": recommendations,
                    "created_at": created_at
                }
            for id, title, url, markdown, status, comments_processed, comments_positive, comments_negative, recurring_themes, recommendations, created_at in reports]

            result = {
                "result": result_reports,
                "stats": {
                        "count": stats.reports_count,
                        "comments_processed": stats.comments_processed,
                        "comments_positive": stats.comments_positive,
                        "comments_negative": stats.comments_negative
                    }
            }

            await self.repository.cache.set(user_reports_key, json.dumps(result, default = str), ex = 3600)

            logger.info("Retrieved reports from database for user %s and updated cache", user_id)
            
            return result
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error listing reports for user %s: %s", user_id, str(e), exc_info=True)
            raise BadGateway
    
    async def update_report (self, report_id: UUID, schema: UpdatedReport, user_id: str):
        
        try:
            await self.analysis_service.get_analysis_by_report_id(report_id, user_id)
            
            report = await self.repository.get_report_by_id(report_id)

            user_reports_key = f"{self.repository.cache_key}_{user_id}"

            await self.repository.update_report(schema, report, user_reports_key)
            logger.info("Report ID %s updated successfully by user %s", report_id, user_id)
            return None

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error updating report_id %s: %s", report_id, str(e), exc_info=True)
            raise BadGateway
        
    async def delete_report (self, report_id: UUID, user_id: str):

        try:
            user_reports_key = f"{self.repository.cache_key}_{user_id}"

            await self.analysis_service.delete_analysis(report_id, user_id)

            keys = await self.repository.cache.keys(f"{user_reports_key}*")

            if keys:
                await self.repository.cache.delete(*keys)

            logger.info("Report ID %s and associated analysis deleted successfully for user %s", report_id, user_id)
            return None
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error deleting report %s: %s", report_id, str(e), exc_info=True)
            raise BadGateway
        
    async def get_report_pdf_by_id (self, report_id: UUID, user_id: str):

        try:

            await self.analysis_service.get_analysis_by_report_id(report_id, user_id)

            report = await self.repository.get_report_by_id(report_id)

            logger.info("Generating PDF for report %s", report_id)
            pdf_bytes = await asyncio.to_thread(self.generate_pdf, report)
            
            logger.info("PDF generated successfully for report_id %s", report_id)
            return pdf_bytes, "Relatorio"

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error generating PDF for report_id %s: %s", report_id, str(e), exc_info=True)
            raise BadGateway
        
    def generate_pdf (self, report: Report) -> bytes:

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto = True, margin = 15)
        self._render_pdf_title(pdf, report.title)
        self._render_pdf_markdown(pdf, report.markdown)
        self._render_pdf_recurring_themes(pdf, report.recurring_themes)
        self._render_pdf_recommendations(pdf, report.recommendations)
        
        return pdf.output()

    @staticmethod
    def _sanitize_pdf_text(text) -> str:
        if not text:
            return ""

        return str(text).replace("•", "-").replace("—", "-").replace("–", "-")

    @staticmethod
    def _parse_json_list(value) -> list:
        if isinstance(value, list):
            return value

        if isinstance(value, str):
            try:
                parsed_value = json.loads(value)
                return parsed_value if isinstance(parsed_value, list) else []
            except json.JSONDecodeError:
                return []

        return []

    def _render_pdf_title(self, pdf: FPDF, title: str | None) -> None:
        if not title:
            return

        pdf.set_font("Helvetica", "B", 22)
        pdf.multi_cell(0, 12, self._sanitize_pdf_text(title), align="C")
        pdf.ln(10)

    def _render_pdf_table(self, pdf: FPDF, data: list[list]) -> None:
        clean_data = []
        for row in data:
            normalized_row = [str(cell).strip() for cell in row]
            is_separator = all(re.match(r"^[\s\-:]+$", cell) for cell in normalized_row)
            if not is_separator:
                clean_data.append(normalized_row)

        if not clean_data:
            return

        pdf.set_font("Helvetica", "B", 10)
        with pdf.table(
            borders_layout="HORIZONTAL_LINES",
            cell_fill_color=245,
            cell_fill_mode="ROWS",
            line_height=8,
            text_align="CENTER"
        ) as table:
            for index, data_row in enumerate(clean_data):
                row = table.row()
                if index == 0:
                    pdf.set_font("Helvetica", "B", 10)
                else:
                    pdf.set_font("Helvetica", size=10)

                for cell in data_row:
                    row.cell(self._sanitize_pdf_text(cell))
        pdf.ln(5)

    def _render_pdf_markdown(self, pdf: FPDF, markdown: str | None) -> None:
        table_data = []

        pdf.set_font("Helvetica", size=11)
        for line in markdown.split("\n") if markdown else []:
            line_strip = line.strip()

            if line_strip.startswith("|") and line_strip.endswith("|"):
                parts = [part.strip() for part in line_strip.split("|")][1:-1]
                if parts:
                    table_data.append(parts)
                continue

            if table_data:
                self._render_pdf_table(pdf, table_data)
                table_data = []

            if not line_strip:
                pdf.ln(3)
                continue

            pdf.set_x(pdf.l_margin)

            if line_strip.startswith("# "):
                pdf.set_font("Helvetica", "B", 18)
                pdf.multi_cell(0, 10, self._sanitize_pdf_text(line_strip[2:]), markdown=True)
                pdf.ln(4)
            elif line_strip.startswith("## "):
                pdf.set_font("Helvetica", "B", 15)
                pdf.multi_cell(0, 10, self._sanitize_pdf_text(line_strip[3:]), markdown=True)
                pdf.ln(3)
            elif line_strip.startswith("### "):
                pdf.set_font("Helvetica", "B", 13)
                pdf.multi_cell(0, 8, self._sanitize_pdf_text(line_strip[4:]), markdown=True)
                pdf.ln(2)
            elif line_strip.startswith("* ") or line_strip.startswith("- "):
                pdf.set_font("Helvetica", size=11)
                pdf.multi_cell(0, 7, f"  - {self._sanitize_pdf_text(line_strip[2:])}", markdown=True)
            elif line_strip.startswith("---"):
                pdf.ln(2)
                pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
                pdf.ln(4)
            else:
                pdf.set_font("Helvetica", size=11)
                pdf.multi_cell(0, 7, self._sanitize_pdf_text(line_strip), markdown=True)

        if table_data:
            self._render_pdf_table(pdf, table_data)

    def _render_pdf_recurring_themes(self, pdf: FPDF, themes_data) -> None:
        recurring_themes = self._parse_json_list(themes_data)
        theme_rows = [
            [
                theme.get("theme") or "Nao informado",
                theme.get("description") or "Nao informada",
                f"{theme.get('percentage_relevance') or 0}%"
            ]
            for theme in recurring_themes
            if isinstance(theme, dict)
        ]

        if not theme_rows:
            return

        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 15)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 10, "Temas Recorrentes")
        self._render_pdf_table(pdf, [["Tema", "Descricao", "Relevancia"], *theme_rows])

    def _render_pdf_recommendations(self, pdf: FPDF, recommendations_data) -> None:
        recommendations = self._parse_json_list(recommendations_data)
        valid_recommendations = [
            recommendation
            for recommendation in recommendations
            if isinstance(recommendation, dict)
        ]

        if not valid_recommendations:
            return

        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 15)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 10, "Recomendações")
        pdf.ln(2)

        for recommendation in valid_recommendations:
            recommendation_text = recommendation.get("recommendation") or "Nao informada"
            justification = recommendation.get("justification") or "Nao informada"

            pdf.set_font("Helvetica", "B", 11)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 7, f"- {self._sanitize_pdf_text(recommendation_text)}")
            pdf.set_font("Helvetica", size=11)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 7, f"Justificativa: {self._sanitize_pdf_text(justification)}")
            pdf.ln(3)


    async def get_report_quota(self, user_id: str) -> ReportQuotaResponse:

        try:
            logger.info("Fetching report quota for user %s", user_id)

            stats = await self.repository.report_done_count_by_user_id(user_id)
            remaining = max(REPORT_MONTHLY_LIMIT - stats.reports_used, 0)

            logger.info(
                "Report quota retrieved for user %s: used=%s, remaining=%s, comments_processed=%s",
                user_id,
                stats.reports_used,
                remaining,
                stats.comments_processed
            )
            
            return ReportQuotaResponse(
                used = stats.reports_used,
                limit = REPORT_MONTHLY_LIMIT,
                remaining = remaining,
                comments_processed = stats.comments_processed)
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error fetching report quota for user %s: %s", user_id, str(e), exc_info=True)
            raise BadGateway
