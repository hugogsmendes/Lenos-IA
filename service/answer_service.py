from repository.answer_repository import Answer_Repository
from repository.question_repository import Question_Repository
from utils.schemas import AnswerQuestion, UpdateAnswer
from fastapi import HTTPException
from utils.exceptions import BadGateway, NotFound

class Answer_Service:

    def __init__(self, repository: Answer_Repository, question_repository: Question_Repository):
        self.repository = repository
        self.question_repository = question_repository

    async def answer_question(self, body: AnswerQuestion, user_id):

        try:
            question = await self.question_repository.get_question_by_description(body.question)
            if not question:
                raise NotFound(register = f"Question {body.question}")
            
            return await self.repository.answer_question(user_id, question.id, body.answer)

        except HTTPException:
            raise
        except Exception:
            raise BadGateway
        
    async def update_answer (self, body: UpdateAnswer, user_id):
        try:
            
            question = await self.question_repository.get_question_by_description(body.question)
            if not question:
                raise NotFound(register = f"Question {body.question}")
            
            answer = await self.repository.get_answer_by_user(user_id, question.id)
            return await self.repository.update_answer(body.new_answer, answer)

        except HTTPException:
            raise
        except Exception:
            raise BadGateway
    
    async def get_answers_by_user (self, user_id):
        try:

            res = await self.repository.get_answers_by_user(user_id)
            
            return [
                {
                    "question": description,
                    "answer": answer,
                }
            for description, answer in res]
        
        except HTTPException:
            raise
        except Exception:
            raise BadGateway