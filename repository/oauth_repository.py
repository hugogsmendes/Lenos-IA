from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.oauths import Oauth


class Oauth_Repository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_oauth_by_user_id (self, user_id: str) -> Oauth | None:

        query = select(Oauth.user_id).filter(Oauth.user_id == user_id)

        result = await self.session.execute(query)

        return result.scalar_one_or_none()

    async def create_oauth (self, oauth_dict: dict) -> None:

        new_oauth = Oauth(**oauth_dict)
        self.session.add(new_oauth)
        await self.session.commit()