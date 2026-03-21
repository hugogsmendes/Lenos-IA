from repository.question_repository import Question_Repository
from fastapi import HTTPException
from utils.exceptions import BadRequest

class Question_Service:

    def __init__(self, repository: Question_Repository):
        self.repository = repository

    async def create_question (self, description: str):
        try:
            return await self.repository.create_question(description)

        except HTTPException:
            raise
        except Exception:
            raise BadRequest