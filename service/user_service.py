from repository.user_repository import User_Repository
from utils.schemas import RegisterUser
from utils.exceptions import RegisterExistsError, BadRequest

class User_Service:

    def __init__(self, repository: User_Repository):
        self.repository = repository

    async def create_user (self, schema: RegisterUser):

        try:

            user = await self.repository.get_user_by_email(schema.email)

            if user:
                raise RegisterExistsError(register = schema.email)
        
            return await self.repository.create_user(schema)
        
        except Exception:
            raise BadRequest