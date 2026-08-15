from database.postgres_client import SessionLocal
from repository.analysis_repository import Analysis_Repository
from models.reports import Report
from repository.report_repository import Report_Repository
from repository.comment_repository import Comment_Repository
from service.comment_service import Comment_Service
from service.analysis_service import Analysis_Service
from utils.schemas import GenerateReport, UpdatedReport
from fastapi import HTTPException, BackgroundTasks
from utils.exceptions import BadGateway, BadRequest
from utils.processing import extract_youtube_video_id
from database.redis_client import get_redis
from google import genai
from google.genai import types, errors
import json
from uuid import UUID
import re
import asyncio
from fpdf import FPDF
from utils.logging import get_logger
from settings.config import Settings

logger = get_logger("report_service")

settings = Settings()

GEMINI_API_KEY = settings.GEMINI_API_KEY
class Report_Service:

    def __init__(self, repository: Report_Repository, comment_service: Comment_Service, analysis_service: Analysis_Service):

        self.repository = repository
        self.comment_service = comment_service
        self.analysis_service = analysis_service
        self.gemini_service = genai.Client(api_key = GEMINI_API_KEY)
        self.model = "gemini-2.5-flash-lite"
        self.prompt = """
            Você é um analista de dados especialista em comportamento de comunidades digitais, análise de audiência e interpretação de feedback social.
            Sua tarefa é analisar comentários de um vídeo do YouTube e gerar uma análise estatística, comportamental e sentimental da recepção do conteúdo pelo público.

            Considere exclusivamente as informações presentes nos comentários fornecidos.

            A análise deve identificar:

            * percepção geral do público
            * predominância emocional
            * padrões de comportamento
            * assuntos mais discutidos
            * críticas recorrentes
            * elogios recorrentes
            * possíveis oportunidades de conteúdo
            * sinais de engajamento emocional ou polêmica
            * intenção e interesse da audiência

            Caso a quantidade de comentários seja pequena, reduza o nível de confiança da análise e informe isso nos insights.

            Regras obrigatórias:

            * Retorne um JSON com as seguinte estrutura: {titulo: Título curto, criativo e chamativo, markdown: Relatório em markdown}

            * O título não pode ter mais de 50 caracteres
            * Não utilize HTML
            * Utilize títulos, subtítulos, listas e tabelas no Markdown quando necessário
            * Não escreva explicações fora da estrutura solicitada
            * Não invente informações inexistentes
            * Utilize linguagem analítica, objetiva e profissional
            * Todos os percentuais devem variar entre 0 e 100
            * A soma dos sentimentos deve resultar em aproximadamente 100

            Estrutura obrigatória da resposta em Markdown:

            ---

            ## Resumo Geral

            * Total de comentários analisados: X
            * Nível de confiança da análise: Alto/Médio/Baixo
            * Predominância de sentimento: Positivo/Negativo/Neutro

            ### Resumo Analítico

            [Resumo completo da percepção pública]

            ---

            ## Métricas de Sentimento

            | Sentimento | Percentual |
            | ---------- | ---------- |
            | Positivo   | X%         |
            | Negativo   | X%         |
            | Neutro     | X%         |

            ---

            ## Principais Temas

            ### Tema 1

            * Relevância aproximada: X%
            * Descrição:
                [Descrição breve]

            ### Tema 2

            * Relevância aproximada: X%
            * Descrição:
                [Descrição breve]

            ---

            ## Principais Elogios
            * [Elogio recorrente]
            * [Elogio recorrente]
            * [Elogio recorrente]

            ---

            ## Principais Críticas
            * [Crítica recorrente]
            * [Crítica recorrente]
            * [Crítica recorrente]

            ---

            ## Comentários de Destaque

            ### Comentário 1
            * Motivo do destaque:
            [Maior engajamento, polêmica, humor, crítica forte, etc.]

            ### Comentário 2

            * Motivo do destaque:
            [Descrição]

            ---

            ## Insights Comportamentais
            * [Insight acionável]
            * [Insight acionável]
            * [Insight acionável]

            ---

            ## Recomendações para Próximos Vídeos
            * [Sugestão]
            * [Sugestão]
            * [Sugestão]

            ---

            ## Conclusão
            [Conclusão final sobre a recepção do vídeo e comportamento da audiência]
        """

    async def create_report (self, schema: GenerateReport, user_id: str, background_tasks: BackgroundTasks):

        try:
            logger.info("Starting report creation request for user %s, video_url %s", user_id, schema.video_url)
            count = await self.repository.report_count_by_user_id(user_id)

            if count >= 3:
                logger.warning("Report creation rejected: limit reached for user %s", user_id)
                raise BadRequest(detail = "Limite de 3 relatórios atingido")

            youtube_video_id = extract_youtube_video_id(schema.video_url)

            if not youtube_video_id:
                logger.warning("Report creation failed: invalid video URL %s", schema.video_url)
                raise BadRequest
            
            exists_report = await self.analysis_service.get_analysis_by_youtube_video_id(youtube_video_id, user_id)

            if exists_report:
                logger.warning("Report creation rejected: video %s already has a report for user %s", youtube_video_id, user_id)
                raise BadRequest(detail = f"Relatório do vídeo id: {youtube_video_id} já gerado")

            await self.comment_service.verify_video_exists(youtube_video_id)
                
            new_analysis = await self.analysis_service.create_analysis(user_id, schema.video_url, youtube_video_id)

            user_reports_key = f"{self.repository.cache_key}_{user_id}"

            new_report = await self.repository.create_report(new_analysis.id, user_reports_key)

            background_tasks.add_task(self.generate_report, youtube_video_id, new_report.id, user_id, user_reports_key)

            logger.info("Report creation background task started: report_id %s, video_id %s", new_report.id, youtube_video_id)
            return {
                "report_id": new_report.id, "status": new_analysis.status
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error starting report creation for user %s: %s", user_id, str(e), exc_info=True)
            raise BadGateway
        
    async def generate_report (self, video_id: str, report_id: UUID, user_id: str, user_reports_key: str):

        try:
            redis_client = await get_redis()
            async with SessionLocal() as session:
                repository = Report_Repository(session, redis_client)
                analysis_repository = Analysis_Repository(session)
                comment_repository = Comment_Repository(session)
                comment_service = Comment_Service(comment_repository)
                    
                report = await repository.get_report_by_id(report_id)
                analysis = await analysis_repository.get_analysis_by_report_id(report_id, user_id)

                try:
                    logger.info("Background Task: Generating report %s for video %s", report_id, video_id)
                    comments = await comment_service.get_comments_by_video_id(video_id)

                    processed_comments = comment_service.processing_comments(comments)

                    if not processed_comments:
                        logger.warning("Background Task: No valid comments found for video %s, report %s failed", video_id, report_id)
                        await analysis_repository.update_analysis_failed(analysis)
                        await repository.update_report_failed(report, user_reports_key)
                        return

                    report_dict = await self.analyze_comments(processed_comments)

                    if not report_dict:
                        logger.error("Background Task: Gemini analysis failed for report %s", report_id)
                        await analysis_repository.update_analysis_failed(analysis)
                        await repository.update_report_failed(report, user_reports_key)
                        return

                    await analysis_repository.update_analysis_done(analysis)
                        
                    title = report_dict.get("titulo")
                    markdown = report_dict.get("markdown")

                    await repository.update_report_done(report, self.prompt, 
                                                                title, markdown, user_reports_key)
                    logger.info("Background Task: Report %s successfully generated and saved", report_id)
                        
                except Exception as e:
                    logger.error("Background Task: Unexpected error generating report %s: %s", report_id, str(e), exc_info=True)
                    try:
                        await analysis_repository.update_analysis_failed(analysis)
                        await repository.update_report_failed(report, user_reports_key)
                    except Exception:
                        pass
                    return
        finally:
            await redis_client.aclose()
        
    async def analyze_comments (self, comments: list) -> dict:

        try:
            logger.info("Sending %s comments to Gemini API for analysis", len(comments))
            content_for_gemini = "\n".join(f"{i+1}. {c}" for i, c in enumerate(comments))

            response = await self.gemini_service.aio.models.generate_content(
                model = self.model,
                config = types.GenerateContentConfig(
                    system_instruction = self.prompt,
                    temperature = 0.2,
                    max_output_tokens = 2000,
                    response_mime_type = "application/json"
                ),
                contents = f"Analise os seguintes comentários:\n{content_for_gemini}"
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
                "title": report.report_title,
                "url": report.analysis.video_url,
                "report": report.report_markdown,
                "status": report.analysis.status
            }
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error retrieving report %s: %s", report_id, str(e), exc_info=True)
            raise BadGateway
    
    async def get_reports_by_user (self, user_id: str):

        try:
            user_reports_key = f"{self.repository.cache_key}_{user_id}"

            reports_cache = await self.repository.cache.get(user_reports_key)

            if reports_cache:
                logger.info("Retrieved reports from cache for user %s", user_id)
                return json.loads(reports_cache)

            reports = await self.repository.get_reports_by_user(user_id)

            result = [
                {
                    "id": report_id,
                    "title": title,
                    "url": url,
                    "report": report,
                    "status": status
                }
            for report_id, title, url, report, status in reports]

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
            logger.info("Report %s updated successfully by user %s", report_id, user_id)
            return None

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error updating report %s: %s", report_id, str(e), exc_info=True)
            raise BadGateway
        
    async def delete_report (self, report_id: UUID, user_id: str):

        try:
            user_reports_key = f"{self.repository.cache_key}_{user_id}"

            await self.analysis_service.delete_analysis(report_id, user_id)

            await self.repository.cache.delete(user_reports_key)

            logger.info("Report %s and associated analysis deleted successfully for user %s", report_id, user_id)
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
            
            logger.info("PDF generated successfully for report %s", report_id)
            return pdf_bytes, "Relatorio"

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error generating PDF for report %s: %s", report_id, str(e), exc_info=True)
            raise BadGateway
        
    def generate_pdf (self, report: Report) -> bytes:

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto = True, margin = 15)
        
        def s(text):
            if not text: return ""
            return text.replace("•", "-").replace("—", "-").replace("–", "-")

        if report.report_title:
            pdf.set_font("Helvetica", "B", 22)
            pdf.multi_cell(0, 12, s(report.report_title), align='C')
            pdf.ln(10)

        lines = report.report_markdown.split("\n") if report.report_markdown else []
        table_data = []

        def render_table(data):
            if not data: return
            
            clean_data = []
            for row in data:
                is_separator = all(re.match(r"^[\s\-:]+$", cell) for cell in row)
                if not is_separator:
                    clean_data.append(row)
            
            if not clean_data: return

            pdf.set_font("Helvetica", "B", 10)
            with pdf.table(
                borders_layout="HORIZONTAL_LINES",
                cell_fill_color=245,
                cell_fill_mode="ROWS",
                line_height=8,
                text_align="CENTER"
            ) as table:
                for i, data_row in enumerate(clean_data):
                    row = table.row()
                    if i == 0:
                        pdf.set_font("Helvetica", "B", 10)
                    else:
                        pdf.set_font("Helvetica", size=10)
                        
                    for cell in data_row:
                    
                        row.cell(s(cell.strip()))
            pdf.ln(5)

        pdf.set_font("Helvetica", size=11)

        for line in lines:
            line_strip = line.strip()
            
            if line_strip.startswith("|") and line_strip.endswith("|"):
                parts = [p.strip() for p in line_strip.split("|")][1:-1]
                if parts:
                    table_data.append(parts)
                continue
            else:
                if table_data:
                    render_table(table_data)
                    table_data = []

            if not line_strip:
                pdf.ln(3)
                continue

            pdf.set_x(pdf.l_margin)

            if line_strip.startswith("# "):
                pdf.set_font("Helvetica", "B", 18)
                pdf.multi_cell(0, 10, s(line_strip[2:]), markdown=True)
                pdf.ln(4)
            elif line_strip.startswith("## "):
                pdf.set_font("Helvetica", "B", 15)
                pdf.multi_cell(0, 10, s(line_strip[3:]), markdown=True)
                pdf.ln(3)
            elif line_strip.startswith("### "):
                pdf.set_font("Helvetica", "B", 13)
                pdf.multi_cell(0, 8, s(line_strip[4:]), markdown=True)
                pdf.ln(2)
            elif line_strip.startswith("* ") or line_strip.startswith("- "):
                pdf.set_font("Helvetica", size=11)
                pdf.multi_cell(0, 7, f"  - {s(line_strip[2:])}", markdown=True)
            elif line_strip.startswith("---"):
                pdf.ln(2)
                pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
                pdf.ln(4)
            else:
                pdf.set_font("Helvetica", size=11)
                pdf.multi_cell(0, 7, s(line_strip), markdown=True)

        if table_data:
            render_table(table_data)
        
        return pdf.output()
