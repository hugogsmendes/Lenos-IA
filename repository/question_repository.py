from sqlalchemy.ext.asyncio import AsyncSession
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