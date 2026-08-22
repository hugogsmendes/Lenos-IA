from src.repository.answer_repository import Answer_Repository
from src.repository.question_repository import Question_Repository
from src.utils.schemas import AnswerQuestion, UpdateAnswer
from src.utils.exceptions import BadGateway, NotFound, BadRequest
from src.utils.logging import get_logger
from fastapi import HTTPException
import json
from uuid import UUID

logger = get_logger("answer_service")

class Answer_Service:

    def __init__(self, repository: Answer_Repository, question_repository: Question_Repository):
        self.repository = repository
        self.question_repository = question_repository

    async def answer_question(self, schema: AnswerQuestion, user_id: str):

        try:
            question = await self.question_repository.get_question_by_id(schema.question_id)
            if not question:
                logger.warning("Answer attempt failed: question %s not found", schema.question_id)
                raise NotFound("Question")
            
            new_answer = await self.repository.answer_question(user_id, schema.question_id, schema.answer)
            logger.info("Question %s answered successfully by user %s", schema.question_id, user_id)
            return new_answer

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error answering question %s by user %s: %s", schema.question_id, user_id, str(e), exc_info=True)
            raise BadGateway
        
    async def update_answer (self, id: UUID, schema: UpdateAnswer, user_id: str):
        try:
            answer = await self.repository.get_answer_by_user(id, user_id)
            if not answer:
                logger.warning("Answer update failed: answer %s not found or not owned by user %s", id, user_id)
                raise BadRequest
            
            user_answers_key = f"{self.repository.cache_key}_{user_id}"
            update_answer = await self.repository.update_answer(schema.new_answer, answer, user_answers_key)
            logger.info("Answer %s updated successfully by user %s", id, user_id)
            return update_answer

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error updating answer %s by user %s: %s", id, user_id, str(e), exc_info=True)
            raise BadGateway
    
    async def get_answers_by_user (self, user_id: str):
        try:

            user_answers_key = f"{self.repository.cache_key}_{user_id}"

            answers_cache = await self.repository.cache.get(user_answers_key)

            if answers_cache:
                logger.info("Retrieved answers from cache for user %s", user_id)
                return json.loads(answers_cache)

            answers = await self.repository.get_answers_by_user(user_id)
            
            result = [
                {
                    "question_id": question_id,
                    "question": description,
                    "answer_id": answer_id,
                    "answer": answer,
                }
            for question_id, description, answer_id, answer in answers]

            await self.repository.cache.set(user_answers_key, json.dumps(result, default = str), ex = 3600)

            logger.info("Retrieved answers from database for user %s and updated cache", user_id)
            return result
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error getting answers for user %s: %s", user_id, str(e), exc_info=True)
            raise BadGateway