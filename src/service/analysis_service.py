from src.repository.analysis_repository import Analysis_Repository
from src.utils.exceptions import BadGateway, BadRequest
from src.utils.logging import get_logger
from fastapi import HTTPException
from uuid import UUID

logger = get_logger("analysis_service")


class Analysis_Service:

    def __init__(self, repository: Analysis_Repository):
        self.repository = repository

    async def create_analysis(self, user_id: str, video_url: str, youtube_video_id: str):
        
        try:
            logger.info("Creating new analysis for user %s, video_id %s", user_id, youtube_video_id)
            new_analysis = await self.repository.create_analysis(user_id, video_url, youtube_video_id)
            return new_analysis
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to create analysis for video_id %s: %s", youtube_video_id, str(e), exc_info=True)
            raise BadGateway
        
    async def get_analysis_by_report_id (self, report_id: UUID, user_id: str): 

        try:
            analysis = await self.repository.get_analysis_by_report_id(report_id, user_id)

            if not analysis:
                logger.warning("Analysis not found for report_id or trying to access analysis of user %s", report_id)
                raise BadRequest

            return analysis
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error retrieving analysis for report_id %s: %s", report_id, str(e), exc_info=True)
            raise BadGateway
        
    async def delete_analysis (self, report_id: UUID, user_id: str):

        try:
            analysis = await self.get_analysis_by_report_id(report_id, user_id)
            await self.repository.delete_analysis(analysis)
            logger.info("Analysis deleted successfully for report_id %s", report_id)
            return None

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error deleting analysis for report_id %s: %s", report_id, str(e), exc_info=True)
            raise BadGateway
        
        
    async def get_analysis_by_youtube_video_id (self, youtube_video_id: str, user_id: str):
        try:
            return await self.repository.get_analysis_by_youtube_video_id(youtube_video_id, user_id)

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error retrieving analysis for youtube_video_id %s: %s", youtube_video_id, str(e), exc_info=True)
            raise BadGateway