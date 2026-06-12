from repository.analysis_repository import Analysis_Repository
from fastapi import HTTPException
from utils.exceptions import BadGateway, BadRequest, Forbidden
import uuid
from models.analyses import Analysis



class Analysis_Service:

    def __init__(self, repository: Analysis_Repository):
        self.repository = repository

    async def create_analysis(self, user_id: uuid.UUID, video_url: str, youtube_video_id: str):
        
        try:

            new_analysis = await self.repository.create_analysis(user_id, video_url, youtube_video_id)

            return new_analysis
        
        except HTTPException:
            raise
        except Exception:
            raise BadGateway
        
    async def get_analysis_by_report_id (self, report_id: uuid.UUID, user_id: uuid.UUID): 

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
        
    async def delete_analysis (self, report_id: uuid.UUID, user_id: uuid.UUID):

        try:

            analysis = await self.get_analysis_by_report_id(report_id, user_id)
            
            return await self.repository.delete_analysis(analysis)

        except HTTPException:
            raise
        except Exception:
            raise BadGateway
        
    async def update_analysis_failed (self, analysis: Analysis):
        try:

            return await self.repository.update_analysis_failed(analysis)

        except HTTPException:
            raise
        except Exception:
            raise BadGateway
        
    async def update_analysis_done (self, analysis: Analysis):
        try:

            return await self.repository.update_analysis_done(analysis)

        except HTTPException:
            raise
        except Exception:
            raise BadGateway
        
    async def get_analysis_by_youtube_video_id (self, youtube_video_id: str, user_id: uuid.UUID):
        try:

            return await self.repository.get_analysis_by_youtube_video_id(youtube_video_id, user_id)

        except HTTPException:
            raise
        except Exception:
            raise BadGateway