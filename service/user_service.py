from repository.user_repository import User_Repository
from utils.schemas import RegisterUser, LoginUser, UpdateUser, UpdatePasswordUser
from utils.exceptions import Conflict, BadRequest, NotFound, Unauthorized, BadGateway
from utils.security import verify_password, create_email_token, create_access_token, create_refresh_token, verify_token_jwt
from fastapi import HTTPException, Request



class User_Service:

    def __init__(self, repository: User_Repository):
        self.repository = repository

    async def create_user (self, schema: RegisterUser):

        if not schema.terms_accepted:
            raise BadRequest

        try:
            user = await self.repository.get_user_by_email(schema.email)

            if user:
                raise Conflict(register = schema.email)
        
            new_user = await self.repository.create_user(schema)

            token_email = create_email_token(new_user.email)

            return new_user
        
        except HTTPException:
            raise
        except Exception:
            raise BadGateway
        
    async def login (self, schema: LoginUser):
        
        try:
            user = await self.repository.get_user_by_email(schema.email)
            
            if not user:
                raise Unauthorized(detail = "Credencias inválidas")
            
            if not verify_password(user.password_hash, schema.password):
                raise Unauthorized(detail = "Credencias inválidas")
            
            if not user.email_verified:
                raise Unauthorized(detail = "Email não verificado")
            
            access_token = create_access_token(user.id, user.name, user.email, user.phone)
            refresh_token = create_refresh_token(user.id, user.name, user.email, user.phone)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token
            }
            
        except HTTPException:
            raise
        except Exception:
            raise BadGateway
        
    async def refresh (self, request: Request):

        try:
            payload = verify_token_jwt(request.cookies.get("refresh_token"), "refresh")
            if not payload:
                raise BadRequest
            
            access_token = create_access_token(payload.get("sub"), payload.get("name"), 
                                               payload.get("email"), payload.get("phone"))

            return {
                "access_token": access_token
            }
            
        except HTTPException:
            raise
        except Exception:
            raise BadGateway
        
    async def update_user (self, schema: UpdateUser, email: str):

        try:
            user = await self.repository.get_user_by_email(email)

            if not user:
                raise NotFound(register = email)

            if schema.email and schema.email != user.email:
                exists_user = await self.repository.get_user_by_email(schema.email)

                if exists_user:
                    raise Conflict(register = schema.email)
        
            update_user = await self.repository.update_user(schema, user)

            access_token = create_access_token(update_user.id, update_user.name, update_user.email, update_user.phone)
            refresh_token = create_refresh_token(update_user.id, update_user.name, update_user.email, update_user.phone)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
        
        except HTTPException:
            raise
        except Exception:
            raise BadGateway
        
    async def update_password(self, schema: UpdatePasswordUser, email: str):

        try:
            user = await self.repository.get_user_by_email(email)

            if not verify_password(user.password_hash, schema.current_password):
                raise Unauthorized(detail = "Credencias inválidas")
            
            return await self.repository.update_password(schema.new_password, user)

        except HTTPException:
            raise
        except Exception:
            raise BadGateway
    
    async def delete_user(self, email: str):

        try:

            user = await self.repository.get_user_by_email(email)

            if not user:
                raise NotFound(register = email)
            
            return await self.repository.delete_user(user)
        
        except HTTPException:
            raise
        except Exception:
            raise BadGateway
        
    async def verify_email(self, token: str):

        try:

            payload = verify_token_jwt(token, "email_verification")

            if not payload:
                raise BadRequest
            
            email = payload.get("email")

            user = await self.repository.get_user_by_email(email)

            if not user:
                raise NotFound(register = email)
            
            return await self.repository.update_email_verified(user)
                
        except HTTPException:
            raise
        except Exception:
            raise BadGateway

