from src.models.oauths import Oauth
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


class Oauth_Repository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_tokens_by_user_id (self, user_id: str) -> tuple | None:

        query = select(Oauth.access_token, Oauth.refresh_token).filter(Oauth.user_id == user_id).order_by(Oauth.created_at.desc())

        result = await self.session.execute(query)

        return result.first()

    async def create_user_oauth (self, oauth_dict: dict) -> None:

        new_oauth = Oauth(**oauth_dict)
        self.session.add(new_oauth)
        await self.session.commit()

    async def get_channel_id_by_user_id (self, user_id: str) -> tuple | None:

        query = select(Oauth.channel_id).filter(Oauth.user_id == user_id).order_by(Oauth.created_at.desc())

        result = await self.session.execute(query)

        return result.first()