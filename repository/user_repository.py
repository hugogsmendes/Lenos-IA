from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class User_Repository:

    def __init__(self, session: AsyncSession):
        self.session = session