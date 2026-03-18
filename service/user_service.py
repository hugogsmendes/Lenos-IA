from repository.user_repository import User_Repository
from utils.schemas import RegisterUser, LoginUser
from utils.exceptions import RegisterExistsError, BadRequest, RegisterNotFoundError, Unauthorized
from utils.security import verify_password, create_access_token, create_refresh_token
from fastapi import HTTPException


class User_Service:

    def __init__(self, repository: User_Repository):
        self.repository = repository

    async def create_user (self, schema: RegisterUser):

        try:
            user = await self.repository.get_user_by_email(schema.email)

            if user:
                raise RegisterExistsError(register = schema.email)
        
            return await self.repository.create_user(schema)
        
        except HTTPException:
            raise
        except Exception:
            raise BadRequest
        
    async def login (self, schema: LoginUser):
        
        try:
            user = await self.repository.get_user_by_email(schema.email)
            
            if not user:
                raise RegisterNotFoundError(register = schema.email)
            
            if not verify_password(user.password_hash, schema.password):
                raise Unauthorized(detail = "Credencias inválidas")
            
            access_token = create_access_token(user.id, user.name, user.email)
            refresh_token = create_refresh_token(user.id, user.name, user.email)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "type": "Bearer"
            }
            
        except HTTPException:
            raise
        except Exception:
            raise BadRequest