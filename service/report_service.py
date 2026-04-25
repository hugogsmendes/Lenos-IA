from repository.report_repository import Report_Repository
from service.comment_service import Comment_Service
from service.analysis_service import Analysis_Service
from utils.schemas import GenerateReport
from fastapi import HTTPException
from utils.exceptions import BadGateway, BadRequest, Forbidden, NotFound
from utils.processing import extract_youtube_video_id
from utils.schemas import UpdatedReport
class Report_Service:

    def __init__(self, repository: Report_Repository, comment_service: Comment_Service, analysis_service: Analysis_Service):

        self.repository = repository
        self.comment_service = comment_service
        self.analysis_service = analysis_service

    async def create_report (self, body: GenerateReport, user_id):

        try:
            video_id = extract_youtube_video_id(body.video_url)

            if not video_id:
                raise BadRequest
            
            analysis = await self.analysis_service.create_analysis(user_id, body.video_url, video_id)

            new_report = await self.repository.create_report(analysis.id)

            return {
                "report_id": new_report.id, "status": analysis.status
            }

        except HTTPException:
            raise
        except Exception:
            raise BadGateway
        
    async def get_report_by_id (self, report_id, user_id):

        try:
            analysis = await self.analysis_service.get_analysis_by_report_id(report_id)

            if str(analysis.user_id) != user_id:
                raise Forbidden

            res = await self.repository.get_report_by_id(report_id)

            return [
                {
                    "id": report_id,
                    "title": title,
                    "report": report,
                    "status": status
                }
            for report_id, title, report, status in res]
        
        except HTTPException:
            raise
        except Exception:
            raise BadGateway
    
    async def get_reports_by_user (self, user_id):

        try:
            
            res = await self.repository.get_reports_by_user(user_id)

            return [
                {
                    "id": report_id,
                    "title": title,
                    "report": report,
                    "status": status
                }
            for report_id, title, report, status in res]
        
        except HTTPException:
            raise
        except Exception:
            raise BadGateway
    
    async def update_report (self, schema: UpdatedReport, user_id):
        
        try:
            analysis = await self.analysis_service.get_analysis_by_report_id(schema.report_id)

            if str(analysis.user_id) != user_id:
                raise Forbidden
            
            report = await self.repository.get_report(schema.report_id)

            return await self.repository.update_report(schema, report)

        except HTTPException:
            raise
        except Exception:
            raise BadGateway
        
    async def delete_report (self, report_id, user_id):

        try:

            return await self.analysis_service.delete_analysis(report_id, user_id)

        except HTTPException:
            raise
        except Exception:
            raise BadGateway

