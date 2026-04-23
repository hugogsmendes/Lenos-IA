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
            
    async def list_questions (self):
        try:

            res = await self.repository.list_questions()

            return [
                {
                    "id": question.id,
                    "question": question.description
                }
            for question in res]
        
        except HTTPException:
            raise
        except Exception:
            raise BadGateway