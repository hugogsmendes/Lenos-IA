from repository.question_repository import Question_Repository
from fastapi import HTTPException
from utils.exceptions import BadGateway
import json
from fastapi.encoders import jsonable_encoder

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

            questions = await self.repository.cache.get(self.repository.cache_key)

            if questions:
                return json.loads(questions)
            
            res = await self.repository.list_questions()

            result = [
                {
                    "id": question.id,
                    "question": question.description
                }
            for question in res]

            await self.repository.cache.set(self.repository.cache_key, json.dumps(result, default = str), ex = 120)

            return result
        
        except HTTPException:
            raise
        except Exception:
            raise BadGateway