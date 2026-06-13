from repository.question_repository import Question_Repository
from fastapi import HTTPException
from utils.exceptions import BadGateway
import json
from utils.logging import get_logger

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

            questions = await self.repository.cache.get(self.repository.cache_key)

            if questions:
                logger.info("Retrieved questions from cache")
                return json.loads(questions)
            
            res = await self.repository.list_questions()

            result = [
                {
                    "id": question.id,
                    "question": question.description
                }
            for question in res]

            await self.repository.cache.set(self.repository.cache_key, json.dumps(result, default = str), ex = 120)

            logger.info("Retrieved questions from database and updated cache")
            return result
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error listing questions: %s", str(e), exc_info=True)
            raise BadGateway