from repository.user_repository import User_Repository
from utils.schemas import RegisterUser, LoginUser, UpdateUser, UpdatePasswordUser
from utils.exceptions import RegisterExistsError, BadRequest, RegisterNotFoundError, Unauthorized
from utils.security import verify_password, create_access_token, create_refresh_token, verify_token_jwt
from fastapi import HTTPException, Request



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
        
    async def refresh (self, request: Request):

        try:
            payload = verify_token_jwt(request.cookies.get("refresh_token"), "refresh")
            if not payload:
                raise Unauthorized(detail = "Token inválido")
            
            user = await self.repository.get_user_by_email(payload.get("email"))

            access_token = create_access_token(user.id, user.name, user.email)

            return {
                "access_token": access_token,
                "type": "Bearer"
            }
            
        except HTTPException:
            raise
        except Exception:
            raise BadRequest
        
    async def update_user (self, schema: UpdateUser, email: str):

        try:

            exists_user = await self.repository.get_user_by_email(schema.email)

            if exists_user:
                raise RegisterExistsError(register = schema.email)
            
            user = await self.repository.get_user_by_email(email)
        
            update_user = await self.repository.update_user(schema, user)

            access_token = create_access_token(update_user.id, update_user.name, update_user.email)
            refresh_token = create_refresh_token(update_user.id, update_user.name, update_user.email)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "type": "Bearer"
            }
        
        except HTTPException:
            raise
        except Exception:
            raise BadRequest
        
    async def update_password(self, schema: UpdatePasswordUser, email: str):

        try:
            user = await self.repository.get_user_by_email(email)

            if not verify_password(user.password_hash, schema.current_password):
                raise Unauthorized(detail = "Credencias inválidas")
            
            return await self.repository.update_password(schema.new_password, user)

        except HTTPException:
            raise
        except Exception:
            raise BadRequest

