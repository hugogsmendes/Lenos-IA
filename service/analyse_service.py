from repository.analyses_repository import Analyse_Repository
from fastapi import HTTPException
from utils.exceptions import BadGateway, BadRequest


class Analyse_Service:

    def __init__(self, repository: Analyse_Repository):
        self.repository = repository

    async def create_analysis(self, user_id, video_url, youtube_video_id):
        
        try:

            new_analysis = await self.repository.create_analysis(user_id, video_url, youtube_video_id)

            return new_analysis
        
        except HTTPException:
            raise
        except Exception:
            raise BadGateway
        
    async def get_analysis_by_report_id (self, report_id): 

        try:

            analysis = await self.repository.get_analysis_by_report_id(report_id)

            if not analysis:
                raise BadRequest

            return analysis
        
        except HTTPException:
            raise
        except Exception:
            raise BadGateway