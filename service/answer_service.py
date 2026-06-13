from repository.answer_repository import Answer_Repository
from repository.question_repository import Question_Repository
from utils.schemas import AnswerQuestion, UpdateAnswer
from fastapi import HTTPException
from utils.exceptions import BadGateway, NotFound, BadRequest
import json
from utils.logging import get_logger

logger = get_logger("answer_service")

class Answer_Service:

    def __init__(self, repository: Answer_Repository, question_repository: Question_Repository):
        self.repository = repository
        self.question_repository = question_repository

    async def answer_question(self, body: AnswerQuestion, user_id):

        try:
            question = await self.question_repository.get_question_by_id(body.question_id)
            if not question:
                logger.warning("Answer attempt failed: question %s not found", body.question_id)
                raise NotFound("Question")
            
            result = await self.repository.answer_question(user_id, body.question_id, body.answer)
            logger.info("Question %s answered successfully by user %s", body.question_id, user_id)
            return result

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error answering question %s by user %s: %s", body.question_id, user_id, str(e), exc_info=True)
            raise BadGateway
        
    async def update_answer (self, id, body: UpdateAnswer, user_id):
        try:
            answer = await self.repository.get_answer_by_user(id, user_id)
            if not answer:
                logger.warning("Answer update failed: answer %s not found or not owned by user %s", id, user_id)
                raise BadRequest
            
            user_key = f"{self.repository.cache_key}_{user_id}"
            result = await self.repository.update_answer(body.new_answer, answer, user_key)
            logger.info("Answer %s updated successfully by user %s", id, user_id)
            return result

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error updating answer %s by user %s: %s", id, user_id, str(e), exc_info=True)
            raise BadGateway
    
    async def get_answers_by_user (self, user_id):
        try:

            user_key = f"{self.repository.cache_key}_{user_id}"

            user_answers = await self.repository.cache.get(user_key)

            if user_answers:
                logger.info("Retrieved answers from cache for user %s", user_id)
                return json.loads(user_answers)

            res = await self.repository.get_answers_by_user(user_id)
            
            result = [
                {
                    "question_id": question_id,
                    "question": description,
                    "answer_id": answer_id,
                    "answer": answer,
                }
            for question_id, description, answer_id, answer in res]

            await self.repository.cache.set(user_key, json.dumps(result, default = str), ex = 120)

            logger.info("Retrieved answers from database for user %s and updated cache", user_id)
            return result
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error getting answers for user %s: %s", user_id, str(e), exc_info=True)
            raise BadGateway