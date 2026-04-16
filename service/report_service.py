from repository.report_repository import Report_Repository
from service.comment_service import Comment_Service
from service.analyse_service import Analyse_Service
from utils.schemas import GenerateReport
from fastapi import HTTPException
from utils.exceptions import BadGateway, BadRequest, NotFound
from utils.processing import extract_youtube_video_id

class Report_Service:

    def __init__(self, repository: Report_Repository, comment_service: Comment_Service, analyse_service: Analyse_Service):

        self.repository = repository
        self.comment_service = comment_service
        self.analyse_service = analyse_service

    async def create_report (self, body: GenerateReport, user_id):

        try:
            video_id = extract_youtube_video_id(body.video_url)

            if not video_id:
                raise BadRequest
            
            analysis_id = await self.analyse_service.create_analysis(user_id, body.video_url, video_id)

            new_report = await self.repository.create_report(analysis_id)

            return {
                "report_id": new_report.id, "status": "pending"
            }

        except HTTPException:
            raise
        except Exception:
            raise BadGateway
        
    async def list_report (self, report_id):

        try:

            report = await self.repository.get_report_by_id(report_id)

            if not report:
                raise NotFound(register = "Relatório")
            
            res = await self.repository.list_report(report_id)

            return [
                {
                    "title": title,
                    "report": report,
                    "status": status
                }
            for title, report, status in res]
        
        except HTTPException:
            raise
        except Exception:
            raise BadGateway
