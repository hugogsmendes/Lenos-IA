from dotenv import load_dotenv
import os
from repository.report_repository import Report_Repository
from service.comment_service import Comment_Service
from service.analysis_service import Analysis_Service
from utils.schemas import GenerateReport
from fastapi import HTTPException, BackgroundTasks, status
from utils.exceptions import BadGateway, BadRequest, Forbidden, NotFound
from utils.processing import extract_youtube_video_id
from utils.schemas import UpdatedReport
from google import genai
from google.genai import types, errors
import json
from models.analyses import Analysis
from models.reports import Report
import uuid


load_dotenv()

class Report_Service:

    def __init__(self, repository: Report_Repository, comment_service: Comment_Service, analysis_service: Analysis_Service):

        self.repository = repository
        self.comment_service = comment_service
        self.analysis_service = analysis_service
        self._api_key = os.getenv("key_gemini")
        self.gemini_service = genai.Client(api_key = self._api_key)
        self.prompt = """
            Você é um analista de dados especialista em comportamento de comunidades digitais e influenciadores. 
            Sua tarefa é analisar uma lista de comentários limpos extraídos do YouTube.
            Para o lote de comentários enviado, você deve gerar uma análise estatística e comportamental estrita.
            Você deve responder exclusivamente em formato JSON, sem nenhuma marcação de texto, introdução ou conclusão (não use blocos de código markdown como ```json).
            O JSON deve seguir exatamente esta estrutura:
            {   
                "titulo_analise": "Um título curto e contextualizado sobre o lote de comentários",
                "resumo_metas": {
                "total_analisado": número de comentários,
                "predominancia_sentimento": "Positivo", "Negativo" ou "Neutro"
            },
                "metricas_sentimento": {
                "positivo_porcentagem": número de 0 a 100,
                "negativo_porcentagem": número de 0 a 100,
                "neutro_porcentagem": número de 0 a 100
            },
            "principais_temas": [
            {
                "tema": "Nome do assunto mais falado",
                "relevancia_porcentagem": número de 0 a 100,
                "descricao_breve": "O que a comunidade está dizendo sobre isso"
            }
            ],
            "insights_comportamentais": [
                "Uma frase curta com um insight acionável sobre o comportamento ou intenção desse público"
            ]
            }
            """

    async def create_report (self, body: GenerateReport, user_id, background_tasks: BackgroundTasks):

        try:
            video_id = extract_youtube_video_id(body.video_url)

            if not video_id:
                raise BadRequest
            
            self.comment_service.verify_video_exists(video_id)
                
            new_analysis = await self.analysis_service.create_analysis(user_id, body.video_url, video_id)

            new_report = await self.repository.create_report(new_analysis.id)
            
            background_tasks.add_task(self.generate_report, video_id, new_analysis, new_report)

            return {
                "report_id": new_report.id, "status": new_analysis.status
            }

        except HTTPException:
            raise
        except Exception:
            raise BadGateway
        
    async def generate_report (self, video_id: str, analysis: Analysis, report: Report):
        try:
            comments = self.comment_service.get_comments_by_video_id(video_id)

            processed_comments = self.comment_service.processing_comments(comments)

            report_comments = await self.analyze_comments(processed_comments)

            if not report_comments:
                await self.analysis_service.update_analysis_failed(analysis)

            await self.analysis_service.update_analysis_done(analysis)
            
            title = report_comments.get("titulo_analise")
            report_comments.pop("titulo_analise")
            await self.repository.update_report_done(report, self.prompt, 
                                                    title, str(report_comments))
            
        except HTTPException as e:

            try:
                await self.analysis_service.update_analysis_failed(analysis)
                await self.repository.update_report_failed(report)
            except Exception:
                pass
            print(f"Handled HTTPException in background task: {e}")
            return
        except Exception as e:

            try:
                await self.analysis_service.update_analysis_failed(analysis)
                await self.repository.update_report_failed(report)
            except Exception:
                pass
            print(f"Unexpected error in background task generate_report: {e}")
            return
        
    async def analyze_comments (self, comments: list) -> dict:

        try:
            
            content_for_gemini = "\n".join(f"{i+1}. {c}" for i, c in enumerate(comments))

            response = await self.gemini_service.aio.models.generate_content(
                model = "gemini-2.5-flash-lite",
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
        
            if e.code == 429:
                raise HTTPException(
                    status_code = status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Limite de requisições do Gemini atingido. Tente novamente em breve."
                )
            elif e.code == 403:
                raise HTTPException(
                    status_code = status.HTTP_403_FORBIDDEN,
                    detail="Erro de autenticação na API de IA (Chave inválida ou expirada)."
                )
            else:
                raise HTTPException(
                    status_code = status.HTTP_502_BAD_GATEWAY,
                    detail=f"O provedor de IA retornou um erro: {e.message}"
                    )
        except Exception as e:
            print(f"Erro inesperado no Python: {str(e)}")
            raise HTTPException(
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao processar a análise do lote."
            )
        
        
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
            
            res = await self.repository.get_reports_by_user(user_id)

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
    
    async def update_report (self, schema: UpdatedReport, user_id: uuid.UUID):
        
        try:
            await self.analysis_service.get_analysis_by_report_id(schema.report_id, user_id)
            
            report = await self.repository.get_report(schema.report_id)

            return await self.repository.update_report(schema, report)

        except HTTPException:
            raise
        except Exception:
            raise BadGateway
        
    async def delete_report (self, report_id: uuid.UUID, user_id: uuid.UUID):

        try:

            return await self.analysis_service.delete_analysis(report_id, user_id)

        except HTTPException:
            raise
        except Exception:
            raise BadGateway

