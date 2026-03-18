from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from utils.database import SessionLocal
from fastapi import Depends
from repository.user_repository import User_Repository
from service.user_service import User_Service

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def get_user_repository(session: AsyncSession = Depends(get_session)):
    return User_Repository(session = session)

def get_user_service(repository: User_Repository = Depends(get_user_repository)):
    return User_Service(repository = repository)