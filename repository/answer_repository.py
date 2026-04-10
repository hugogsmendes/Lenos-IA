from sqlalchemy.ext.asyncio import AsyncSession
from models.answers import Answer
from models.questions import Question
from sqlalchemy import select

class Answer_Repository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def answer_question(self, user_id, question_id, answer) -> Answer:
        
        new_anser = Answer(user_id = user_id,
                           question_id = question_id,
                           answer = answer)
        self.session.add(new_anser)
        await self.session.commit()
        await self.session.refresh(new_anser)

        return new_anser
    
    async def get_answer_by_user (self, user_id, question_id) -> Answer:

        query = select(Answer).filter((Answer.user_id == user_id) & (Answer.question_id == question_id))

        result = await self.session.execute(query)

        return result.scalar_one_or_none()
    
    async def update_answer (self, new_answer: str, answer: Answer) -> None:

        answer.answer = new_answer
        await self.session.commit()
        await self.session.refresh(answer)

    async def get_answers_by_user (self, user_id) -> list[(Question, Answer)]:
        
        query = select(Question.description, Answer.answer).join(Question.answers).filter(Answer.user_id == user_id)

        result = await self.session.execute(query)

        return result.all()

