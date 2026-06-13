from repository.analysis_repository import Analysis_Repository
from fastapi import HTTPException
from utils.exceptions import BadGateway, BadRequest, Forbidden
import uuid
from models.analyses import Analysis
from utils.logging import get_logger

logger = get_logger("analysis_service")



class Analysis_Service:

    def __init__(self, repository: Analysis_Repository):
        self.repository = repository

    async def create_analysis(self, user_id: uuid.UUID, video_url: str, youtube_video_id: str):
        
        try:
            logger.info("Creating new analysis for user %s, video %s", user_id, youtube_video_id)
            new_analysis = await self.repository.create_analysis(user_id, video_url, youtube_video_id)
            return new_analysis
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to create analysis for video %s: %s", youtube_video_id, str(e), exc_info=True)
            raise BadGateway
        
    async def get_analysis_by_report_id (self, report_id: uuid.UUID, user_id: uuid.UUID): 

        try:
            analysis = await self.repository.get_analysis_by_report_id(report_id)

            if not analysis:
                logger.warning("Analysis not found for report_id %s", report_id)
                raise BadRequest
            
            if str(analysis.user_id) != str(user_id):
                logger.warning("Access forbidden: user %s trying to access analysis of user %s", user_id, analysis.user_id)
                raise Forbidden

            return analysis
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error retrieving analysis for report_id %s: %s", report_id, str(e), exc_info=True)
            raise BadGateway
        
    async def delete_analysis (self, report_id: uuid.UUID, user_id: uuid.UUID):

        try:
            analysis = await self.get_analysis_by_report_id(report_id, user_id)
            result = await self.repository.delete_analysis(analysis)
            logger.info("Analysis deleted successfully for report_id %s", report_id)
            return result

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error deleting analysis for report_id %s: %s", report_id, str(e), exc_info=True)
            raise BadGateway
        
    async def update_analysis_failed (self, analysis: Analysis):
        try:
            logger.warning("Setting analysis status to FAILED for video %s", analysis.youtube_video_id)
            return await self.repository.update_analysis_failed(analysis)

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error updating analysis to FAILED for video %s: %s", analysis.youtube_video_id, str(e), exc_info=True)
            raise BadGateway
        
    async def update_analysis_done (self, analysis: Analysis):
        try:
            logger.info("Setting analysis status to DONE for video %s", analysis.youtube_video_id)
            return await self.repository.update_analysis_done(analysis)

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error updating analysis to DONE for video %s: %s", analysis.youtube_video_id, str(e), exc_info=True)
            raise BadGateway
        
    async def get_analysis_by_youtube_video_id (self, youtube_video_id: str, user_id: uuid.UUID):
        try:
            return await self.repository.get_analysis_by_youtube_video_id(youtube_video_id, user_id)

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error retrieving analysis for youtube_video_id %s: %s", youtube_video_id, str(e), exc_info=True)
            raise BadGateway