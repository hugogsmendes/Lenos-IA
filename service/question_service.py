from repository.question_repository import Question_Repository
from fastapi import HTTPException
from utils.exceptions import BadGateway

class Question_Service:

    def __init__(self, repository: Question_Repository):
        self.repository = repository

    async def create_question (self, description: str):
        try:
            return await self.repository.create_question(description)

        except HTTPException:
            raise
        except Exception:
            raise BadGateway
        
    async def get_questions_by_user (self, user_id):
        try:

            res = await self.repository.get_questions_by_user(user_id)
            
            return [
                {
                    "question": question.description,
                    "answer": answer.answer,
                }
            for question, answer in res]
        
        except HTTPException:
            raise
        except Exception:
            raise BadGateway
    
    async def list_questions (self):
        try:

            res = await self.repository.list_questions()

            return [
                {
                    "question": question.description
                }
            for question in res]
        
        except HTTPException:
            raise
        except Exception:
            raise BadGateway