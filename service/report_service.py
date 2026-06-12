from database.postgres import SessionLocal
from repository.analysis_repository import Analysis_Repository
from dotenv import load_dotenv
import os
from models.reports import Report
from repository.report_repository import Report_Repository
from service.comment_service import Comment_Service
from service.analysis_service import Analysis_Service
from utils.schemas import GenerateReport, UpdatedReport
from fastapi import HTTPException, BackgroundTasks, status
from utils.exceptions import BadGateway, BadRequest
from utils.processing import extract_youtube_video_id
from database.redis_client import get_redis
from google import genai
from google.genai import types, errors
import json
import uuid
import re
import asyncio
from fpdf import FPDF


load_dotenv()

class Report_Service:

    def __init__(self, repository: Report_Repository, comment_service: Comment_Service, analysis_service: Analysis_Service):

        self.repository = repository
        self.comment_service = comment_service
        self.analysis_service = analysis_service
        self._api_key = os.getenv("key_gemini")
        self.gemini_service = genai.Client(api_key = self._api_key)
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

    async def create_report (self, body: GenerateReport, user_id: uuid.UUID, background_tasks: BackgroundTasks):

        try:
            count = await self.repository.report_count(user_id)

            if count >= 3:
                raise HTTPException(status_code = status.HTTP_429_TOO_MANY_REQUESTS, 
                                    detail = "Limite de 3 relatórios atingido")

            video_id = extract_youtube_video_id(body.video_url)

            if not video_id:
                raise BadRequest
            
            exists_report_by_video_id = await self.analysis_service.get_analysis_by_youtube_video_id(video_id, user_id)

            if exists_report_by_video_id:
                raise HTTPException(status_code = status.HTTP_429_TOO_MANY_REQUESTS,
                                    detail = f"Relatório do vídeo id: {video_id} já gerado")

            await self.comment_service.verify_video_exists(video_id)
                
            new_analysis = await self.analysis_service.create_analysis(user_id, body.video_url, video_id)

            user_key = f"{self.repository.cache_key}_{user_id}"

            new_report = await self.repository.create_report(new_analysis.id, user_key)
            
            background_tasks.add_task(self.generate_report, video_id, new_report.id, user_key)

            return {
                "report_id": new_report.id, "status": new_analysis.status
            }

        except HTTPException:
            raise
        except Exception:
            raise BadGateway
        
    async def generate_report (self, video_id: str, report_id: uuid.UUID, user_key: str):

        redis_client = await get_redis()
        try:
            async with SessionLocal() as session:
                repository = Report_Repository(session, redis_client)
                analysis_repository = Analysis_Repository(session)
                    
                report = await repository.get_report(report_id)
                analysis = await analysis_repository.get_analysis_by_report_id(report_id)

                try:

                    comments = await self.comment_service.get_comments_by_video_id(video_id)

                    processed_comments = self.comment_service.processing_comments(comments)

                    if not processed_comments:
                        await analysis_repository.update_analysis_failed(analysis)
                        await repository.update_report_failed(report, user_key)
                        return

                    report_dict = await self.analyze_comments(processed_comments)

                    if not report_dict:
                        await analysis_repository.update_analysis_failed(analysis)
                        await repository.update_report_failed(report, user_key)
                        return

                    await analysis_repository.update_analysis_done(analysis)
                        
                    title = report_dict.get("titulo")
                    markdown = report_dict.get("markdown",)

                    await repository.update_report_done(report, self.prompt, 
                                                                title, markdown, user_key)
                        
                except Exception as e:

                    try:
                        await analysis_repository.update_analysis_failed(analysis)
                        await repository.update_report_failed(report, user_key)
                    except Exception:
                        pass
                    print(f"Unexpected error in background task generate report: {e}")
                    return
        finally:
            await redis_client.aclose()
        
    async def analyze_comments (self, comments: list) -> dict:

        try:
            
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
            return json.loads(response.text)

        except errors.APIError as e:
            print(f"Erro na API do Gemini: Código {e.code} - {e.message}")
            return
        
        except Exception as e:
            print(f"Erro inesperado no Python: {str(e)}")
            return
        
        
    async def get_report_by_id (self, report_id: uuid.UUID, user_id: uuid.UUID):

        try:
            await self.analysis_service.get_analysis_by_report_id(report_id, user_id)

            res = await self.repository.get_report_by_id(report_id)

            return [
                {
                    "id": report_id,
                    "title": title,
                    "url": url,
                    "report": report,
                    "status": status
                }
            for report_id, title, url, report, status in res]
        
        except HTTPException:
            raise
        except Exception:
            raise BadGateway
    
    async def get_reports_by_user (self, user_id: uuid.UUID):

        try:
            user_key = f"{self.repository.cache_key}_{user_id}"

            user_reports = await self.repository.cache.get(user_key)

            if user_reports:
                return json.loads(user_reports)

            res = await self.repository.get_reports_by_user(user_id)

            result = [
                {
                    "id": report_id,
                    "title": title,
                    "url": url,
                    "report": report,
                    "status": status
                }
            for report_id, title, url, report, status in res]

            await self.repository.cache.set(user_key, json.dumps(result, default = str), ex = 120)

            return result
        
        except HTTPException:
            raise
        except Exception:
            raise BadGateway
    
    async def update_report (self, report_id: uuid.UUID, schema: UpdatedReport, user_id: uuid.UUID):
        
        try:
            await self.analysis_service.get_analysis_by_report_id(report_id, user_id)
            
            report = await self.repository.get_report(report_id)

            user_key = f"{self.repository.cache_key}_{user_id}"

            return await self.repository.update_report(schema, report, user_key)

        except HTTPException:
            raise
        except Exception:
            raise BadGateway
        
    async def delete_report (self, report_id: uuid.UUID, user_id: uuid.UUID):

        try:
            user_key = f"{self.repository.cache_key}_{user_id}"

            await self.analysis_service.delete_analysis(report_id, user_id)

            await self.repository.cache.delete(user_key)

            return None
        
        except HTTPException:
            raise
        except Exception:
            raise BadGateway
        
    async def get_report_pdf_by_id (self, report_id: uuid.UUID, user_id: uuid.UUID):

        try:

            await self.analysis_service.get_analysis_by_report_id(report_id, user_id)

            report = await self.repository.get_report(report_id)

            pdf_bytes = await asyncio.to_thread(self.generate_pdf, report)
            
            return pdf_bytes, "Relatorio"

        except HTTPException:
            raise
        except Exception:
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
