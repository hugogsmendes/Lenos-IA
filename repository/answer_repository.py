from sqlalchemy.ext.asyncio import AsyncSession
from models.answers import Answer

class Answer_Repository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def answer_question(self, user_id, questions_id, answer) -> Answer:
        
        new_anser = Answer(user_id = user_id,
                           questions_id = questions_id,
                           answer = answer)
        self.session.add(new_anser)
        await self.session.commit()
        await self.session.refresh(new_anser)

        return new_anser