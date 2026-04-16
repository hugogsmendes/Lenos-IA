from repository.analyses_repository import Analyse_Repository
from fastapi import HTTPException
from utils.exceptions import BadGateway


class Analyse_Service:

    def __init__(self, repository: Analyse_Repository):
        self.repository = repository

    async def create_analysis(self, user_id, video_url, youtube_video_id):
        
        try:

            new_analysis = await self.repository.create_analysis(user_id, video_url, youtube_video_id)

            return new_analysis.id
        
        except HTTPException:
            raise
        except Exception:
            raise BadGateway