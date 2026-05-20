from repository.analysis_repository import Analysis_Repository
from fastapi import HTTPException
from utils.exceptions import BadGateway, BadRequest, Forbidden


class Analysis_Service:

    def __init__(self, repository: Analysis_Repository):
        self.repository = repository

    async def create_analysis(self, user_id, video_url, youtube_video_id):
        
        try:

            new_analysis = await self.repository.create_analysis(user_id, video_url, youtube_video_id)

            return new_analysis
        
        except HTTPException:
            raise
        except Exception:
            raise BadGateway
        
    async def get_analysis_by_report_id (self, report_id, user_id): 

        try:

            analysis = await self.repository.get_analysis_by_report_id(report_id)

            if not analysis:
                raise BadRequest
            
            if str(analysis.user_id) != user_id:
                raise Forbidden

            return analysis
        
        except HTTPException:
            raise
        except Exception:
            raise BadGateway
        
    async def delete_analysis (self, report_id, user_id):

        try:

            analysis = await self.get_analysis_by_report_id(report_id, user_id)
            
            return await self.repository.delete_analysis(analysis)

        except HTTPException:
            raise
        except Exception:
            raise BadGateway