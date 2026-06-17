from repository.user_repository import User_Repository
from service.email_service import Email_Service
from utils.schemas import RegisterUser, LoginUser, UpdateUser, UpdatePasswordUser, ForgotPassword, ResetPassword
from utils.exceptions import Conflict, BadRequest, NotFound, Unauthorized, BadGateway
from fastapi import BackgroundTasks
from utils.security import verify_password, create_email_token, create_password_token, create_access_token, create_refresh_token, verify_token_jwt
from fastapi import HTTPException, Request
from utils.logging import get_logger
import asyncio


logger = get_logger("user_service")


class User_Service:

    def __init__(self, repository: User_Repository, email_service: Email_Service):
        self.repository = repository
        self.email_service = email_service

    async def create_user (self, schema: RegisterUser, background_tasks: BackgroundTasks):

        try:

            if not schema.terms_accepted:
                logger.warning("User creation failed: terms not accepted for email %s", schema.email)
                raise BadRequest
            
            user = await self.repository.get_user_by_email(schema.email)

            if user:
                logger.warning("User creation failed: email %s already registered", schema.email)
                raise Conflict(register = schema.email)
        
            new_user = await self.repository.create_user(schema)

            token_email = create_email_token(new_user.email)

            background_tasks.add_task(self.email_service.send_verification_email, new_user.email, token_email)

            logger.info("User successfully created: %s", new_user.email)
            return new_user
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error creating user %s: %s", schema.email, str(e), exc_info=True)
            raise BadGateway
        
    async def login (self, schema: LoginUser):
        
        try:
            user = await self.repository.get_user_by_email(schema.email)
            
            if not (user and verify_password(user.password_hash, schema.password)):
                logger.warning("Login failed: invalid credentials for email %s", schema.email)
                raise Unauthorized(detail = "Credencias inválidas")
            
            if not user.email_verified:
                logger.warning("Login failed: email not verified for %s", schema.email)
                raise Unauthorized(detail = "Email não verificado")
            
            access_token = create_access_token(user.id, user.name, user.email, user.phone, user.role)
            refresh_token = create_refresh_token(user.id, user.name, user.email, user.phone, user.role)

            logger.info("User logged in successfully: %s", user.email)
            return {
                "access_token": access_token,
                "refresh_token": refresh_token
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error during login for %s: %s", schema.email, str(e), exc_info=True)
            raise BadGateway
        
    async def refresh (self, request: Request):

        try:
            payload = verify_token_jwt(request.cookies.get("refresh_token"), "refresh")
            if not payload:
                logger.warning("Token refresh failed: invalid refresh token")
                raise BadRequest
            
            access_token = create_access_token(payload.get("sub"), payload.get("name"), 
                                               payload.get("email"), payload.get("phone"), payload.get("role"))

            logger.info("Token refreshed successfully for user: %s", payload.get("email"))
            return {
                "access_token": access_token
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error during token refresh: %s", str(e), exc_info=True)
            raise BadGateway
        
    async def update_user (self, schema: UpdateUser, email: str):

        try:
            user = await self.repository.get_user_by_email(email)

            if not user:
                logger.warning("User update failed: user %s not found", email)
                raise NotFound(register = email)

            if schema.email and schema.email != user.email:
                exists_user = await self.repository.get_user_by_email(schema.email)

                if exists_user:
                    logger.warning("User update failed: new email %s already registered", schema.email)
                    raise Conflict(register = schema.email)
        
            update_user = await self.repository.update_user(schema, user)

            access_token = create_access_token(update_user.id, update_user.name, update_user.email, update_user.phone, update_user.role)
            refresh_token = create_refresh_token(update_user.id, update_user.name, update_user.email, update_user.phone, update_user.role)

            logger.info("User updated successfully: %s", update_user.email)
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error updating user %s: %s", email, str(e), exc_info=True)
            raise BadGateway
        
    async def update_password(self, schema: UpdatePasswordUser, email: str):

        try:
            user = await self.repository.get_user_by_email(email)

            if not verify_password(user.password_hash, schema.current_password):
                logger.warning("Password update failed: invalid current password for %s", email)
                raise Unauthorized(detail = "Credencias inválidas")
            
            result = await self.repository.update_password(schema.new_password, user)
            logger.info("Password updated successfully for user: %s", email)
            return result

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error updating password for %s: %s", email, str(e), exc_info=True)
            raise BadGateway
    
    async def delete_user(self, email: str):

        try:

            user = await self.repository.get_user_by_email(email)

            if not user:
                logger.warning("User deletion failed: user %s not found", email)
                raise NotFound(register = email)
            
            result = await self.repository.delete_user(user)
            logger.info("User deleted successfully: %s", email)
            return result
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error deleting user %s: %s", email, str(e), exc_info=True)
            raise BadGateway
        
    async def verify_email(self, token: str):

        try:

            payload = verify_token_jwt(token, "email_verification")

            if not payload:
                logger.warning("Email verification failed: invalid token")
                raise BadRequest
            
            email = payload.get("email")

            user = await self.repository.get_user_by_email(email)

            if not user:
                logger.warning("Email verification failed: user %s not found", email)
                raise NotFound(register = email)
            
            result = await self.repository.update_email_verified(user)
            logger.info("Email verified successfully for: %s", email)
            return result
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error during email verification: %s", str(e), exc_info=True)
            raise BadGateway
    
    async def forgot_password (self, schema: ForgotPassword):

        try:

            user = await self.repository.get_user_by_email(schema.email)

            if not user:
                logger.warning("Forgot password failed: user %s not found", schema.email)
                raise NotFound(register = schema.email)
            
            token_password = create_password_token(user.email)

            await asyncio.to_thread(self.email_service.send_verification_password_email, user.email, token_password)
            return
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error during forgot password: %s", str(e), exc_info=True)
            raise BadGateway
        
    async def reset_password (self, schema: ResetPassword):

        try:

            payload = verify_token_jwt(schema.token, "password_verification")

            if not payload:
                logger.warning("Reset password failed: invalid token")
                raise BadRequest
            
            email = payload.get("email")

            user = await self.repository.get_user_by_email(email)

            if not user:
                logger.warning("Reset password failed: user %s not found", email)
                raise NotFound(register = email)
            
            result = await self.repository.update_password(schema.new_password, user)
            logger.info("Password updated successfully for user: %s", email)
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error during reset password: %s", str(e), exc_info=True)
            raise BadGateway


