from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.users import User
from utils.schemas import RegisterUser
from utils.security import hash_password

class User_Repository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_email (self, email: str) -> User:

        query = select(User).filter(User.email == email)

        result = await self.session.execute(query)

        return result.scalar_one_or_none()
    
    async def create_user (self, schema: RegisterUser):

        new_user = User(name = schema.name,
                        email = schema.email,
                        phone = schema.phone,
                        password_hash = hash_password(schema.password))

        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)

        return new_user
