from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from models.answers import Answer
from models.questions import Question
from sqlalchemy import select
from uuid import UUID

class Answer_Repository:

    def __init__(self, session: AsyncSession, cache: Redis):
        self.session = session
        self.cache = cache
        self.cache_key = "answers"

    async def answer_question(self, user_id: str, question_id: UUID, answer: str) -> Answer:
        
        new_anser = Answer(user_id = user_id,
                           question_id = question_id,
                           answer = answer)
        self.session.add(new_anser)
        await self.session.commit()
        await self.session.refresh(new_anser)

        return new_anser
    
    async def get_answer_by_user (self, id: UUID, user_id: str) -> Answer | None:

        query = select(Answer).filter((Answer.id == id) & (Answer.user_id == user_id))

        result = await self.session.execute(query)

        return result.scalar_one_or_none()
    
    async def update_answer (self, new_answer: str, answer: Answer, cache_key: str) -> None:

        answer.answer = new_answer
        await self.session.commit()
        await self.cache.delete(cache_key)
        await self.session.refresh(answer)

    async def get_answers_by_user (self, user_id: str) -> list[(Question, Answer)]:
        
        query = select(Question.id, Question.description, Answer.id, Answer.answer).join(Answer.question).filter(Answer.user_id == user_id)

        result = await self.session.execute(query)

        return result.all()

