from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.questions import Question

class Question_Repository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_question (self, description: str) -> Question:

        new_question = Question(description = description)

        self.session.add(new_question)
        await self.session.commit()
        await self.session.refresh(new_question)

        return new_question
    
    async def get_question_id_by_description (self, description: str):

        query = select(Question.id).filter(Question.description == description)

        result = await self.session.execute(query)

        return result.scalar_one_or_none()
        
    async def list_questions (self) -> list[(Question)]:

        query = select(Question.description).order_by(Question.description.desc())

        result = await self.session.execute(query)

        return result.all()