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
from pathlib import Path
import json
import re
import asyncio
from datetime import date

logger = get_logger("report_service")


GEMINI_API_KEY = settings.GEMINI_API_KEY
REPORT_MONTHLY_LIMIT = 5
PROMPT_FILE_PATH = Path(__file__).resolve().parent.parent.parent / "prompt.md"
VADER_PDF_PATH = Path(__file__).resolve().parent.parent.parent / "vader.pdf"

class Report_Service:

    def __init__(self, repository: Report_Repository, comment_service: Comment_Service, analysis_service: Analysis_Service,
                 oauth_service: Oauth_Service):

        self.repository = repository
        self.oauth_service = oauth_service
        self.comment_service = comment_service
        self.analysis_service = analysis_service
        self.gemini_service = genai.Client(api_key = GEMINI_API_KEY)
        self.model = "gemini-2.5-flash-lite"
        self.pdf_path = VADER_PDF_PATH

    def load_prompt(self, file_path: Path | str = PROMPT_FILE_PATH) -> str:
        """Lê o arquivo prompt.md, extrai seu conteúdo e retorna o texto para a requisição de análise."""

        path = Path(file_path)
        if not path.is_file():
            fallback = Path("prompt.md").resolve()
            if fallback.is_file():
                path = fallback
            else:
                logger.error("Prompt file not found at %s or %s", path, fallback)
                raise FileNotFoundError(f"Arquivo de prompt não encontrado: {path}")

        with open(path, "r", encoding="utf-8") as file:
            prompt_content = file.read()

        logger.info("Prompt loaded successfully from %s (%s characters)", path, len(prompt_content))
        return prompt_content

    def load_pdf_part(self, file_path: Path | str = VADER_PDF_PATH) -> types.Part | None:
        """Lê o arquivo PDF local e retorna uma Part multimodal para a requisição de análise."""

        path = Path(file_path)
        if not path.is_file():
            fallback = Path("vader.pdf").resolve()
            if fallback.is_file():
                path = fallback
            else:
                logger.warning("PDF file not found at %s or %s. Proceeding without PDF context.", path, fallback)
                return None

        try:
            with open(path, "rb") as f:
                pdf_bytes = f.read()

            logger.info("PDF loaded successfully from %s (%.2f KB) as multimodal Part", path, len(pdf_bytes) / 1024)
            return types.Part.from_bytes(
                data = pdf_bytes,
                mime_type = "application/pdf"
            )
        except Exception as e:
            logger.error("Failed to read PDF file at %s: %s", path, str(e), exc_info=True)
            return None


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
                
                prompt = self.load_prompt()
                report_dict = await self.analyze_comments(comments_processed, creator_context, prompt)

                if not report_dict:
                    logger.error("Background Task: Gemini analysis failed for report %s", report_id)
                    raise RuntimeError("Gemini analysis returned no data")

                markdown = report_dict.get("markdown")
                comments_positive = report_dict.get("comments_positive")
                comments_negative = report_dict.get("comments_negative")
                comments_neutral = report_dict.get("comments_neutral")
                recurring_themes = report_dict.get("recurring_themes")
                recommendations = report_dict.get("recommendations")

                await analysis_repository.update_analysis_done_by_id(analysis_id)
                await repository.update_report_done_by_id(report_id, prompt, title, markdown, len(comments_processed),
                                                              comments_positive, comments_negative, comments_neutral, recurring_themes, recommendations)
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
        
    async def analyze_comments (self, comments: list, creator_context: list[dict], prompt: str) -> dict:

        try:
            logger.info("Sending %s comments to Gemini API for analysis", len(comments))
            content_for_gemini = "\n".join(f"{i+1}. {c}" for i, c in enumerate(comments))
            formatted_creator_context = "\n".join(
                f"- Pergunta: {item.get('question')}\n  Resposta: {item.get('answer')}"
                for item in (creator_context or [])
            )
            pdf_part = self.load_pdf_part()
    

            response = await self.gemini_service.aio.models.generate_content(
                model = self.model,
                config = types.GenerateContentConfig(
                    system_instruction = prompt,
                    temperature = 0.2,
                    max_output_tokens = 6000,
                    response_mime_type = "application/json"
                ),
                contents =f"""
                    CONTEXTO_DO_CRIADOR:
                    {formatted_creator_context}

                    COMENTARIOS_DO_VIDEO:
                    {content_for_gemini}

                    METODOLOGIA:
                    {pdf_part}
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
                "comments_neutral": report.comments_neutral,
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
                    "comments_neutral": comments_neutral,
                    "recurring_themes": recurring_themes,
                    "recommendations": recommendations,
                    "created_at": created_at
                }
            for id, title, url, markdown, status, comments_processed, comments_positive, comments_negative, comments_neutral, 
                recurring_themes, recommendations, created_at in reports]

            result = {
                "result": result_reports,
                "stats": {
                        "count": stats.reports_count,
                        "comments_processed": stats.comments_processed,
                        "comments_positive": stats.comments_positive,
                        "comments_negative": stats.comments_negative,
                        "comments_neutral": stats.comments_neutral
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
