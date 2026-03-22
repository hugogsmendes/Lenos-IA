from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.questions import Question
from models.answers import Answer

class Question_Repository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_question (self, description: str) -> Question:

        new_question = Question(description = description)

        self.session.add(new_question)
        await self.session.commit()
        await self.session.refresh(new_question)

        return new_question
    
    async def get_question_by_description (self, description: str) -> Question:

        query = select(Question).filter(Question.description == description)

        result = await self.session.execute(query)

        return result.scalar_one_or_none()
    
    async def get_questions_by_user (self, user_id) -> list[(Question, Answer)]:
        
        query = select(Question, Answer).join(Question.answers).filter(Answer.user_id == user_id)

        result = await self.session.execute(query)

        return result.all()