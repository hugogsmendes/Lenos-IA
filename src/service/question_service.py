from src.repository.question_repository import Question_Repository
from src.utils.exceptions import BadGateway
from src.utils.logging import get_logger
from src.utils.schemas import ResponseQuestion
from fastapi import HTTPException
import json

logger = get_logger("question_service")

class Question_Service:

    def __init__(self, repository: Question_Repository):
        self.repository = repository

    async def create_question (self, description: str):
        try:
            result = await self.repository.create_question(description)
            logger.info("Question created successfully: %s", description[:50] + "...")
            return result

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error creating question: %s", str(e), exc_info=True)
            raise BadGateway
            
    async def list_questions (self):
        try:

            questions_cache = await self.repository.cache.get(self.repository.cache_key)

            if questions_cache:
                logger.info("Retrieved questions from cache")
                return json.loads(questions_cache)
            
            questions = await self.repository.list_questions()

            result = [
                ResponseQuestion.model_validate(question).model_dump(mode = "json")
                for question in questions
            ]

            await self.repository.cache.set(self.repository.cache_key, json.dumps(result, default = str), ex = 3600)

            logger.info("Retrieved questions from database and updated cache")
            return result
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error listing questions: %s", str(e), exc_info=True)
            raise BadGateway