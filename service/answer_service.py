from repository.answer_repository import Answer_Repository
from utils.schemas import AnswerQuestion
from fastapi import Depends, HTTPException
from utils.exceptions import BadRequest

class Answer_Service:

    def __init__(self, repository: Answer_Repository):
        self.repository = repository

    async def answer_question(self, schema: AnswerQuestion, user_id, questions_id):

        try:
        
            return await self.repository.answer_question(user_id, questions_id, schema.answer)

        except HTTPException:
            raise
        except Exception:
            raise BadRequest
        
    async def update_answer (self, new_answer: str, user_id, questions_id):
        try:
            
            answer = await self.repository.get_answer_by_user(user_id, questions_id)
            return await self.repository.update_answer(new_answer, answer)

        except HTTPException:
            raise
        except Exception:
            raise BadRequest