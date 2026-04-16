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
            
            analysis = await self.analyse_service.create_analysis(user_id, body.video_url, video_id)

            new_report = await self.repository.create_report(analysis.id)

            return {
                "report_id": new_report.id, "status": analysis.status
            }

        except HTTPException:
            raise
        except Exception:
            raise BadGateway
        
    async def get_report_by_id (self, report_id):

        try:
            
            res = await self.repository.get_report_by_id(report_id)

            if not res:
                raise NotFound(register = "Relatório")

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
    
    async def get_reports_by_user (self, user_id):

        try:
            
            res = await self.repository.get_reports_by_user(user_id)

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
