from src.repository.user_repository import User_Repository
from src.service.email_service import Email_Service
from src.utils.schemas import RegisterUser, LoginUser, UpdateUser, UpdatePasswordUser, ForgotPassword, ResetPassword
from src.utils.exceptions import Conflict, BadRequest, NotFound, Unauthorized, BadGateway
from src.utils.security import verify_password, create_email_verification_token, create_password_reset_token, create_access_token, create_refresh_token, verify_token_jwt
from src.utils.logging import get_logger
from fastapi import HTTPException, Request, BackgroundTasks
import asyncio


logger = get_logger("user_service")


class User_Service:

    def __init__(self, repository: User_Repository, email_service: Email_Service):
        self.repository = repository
        self.email_service = email_service

    async def register (self, schema: RegisterUser, background_tasks: BackgroundTasks):

        try:

            if not schema.terms_accepted:
                logger.warning("User creation failed: terms not accepted for email %s", schema.email)
                raise BadRequest
            
            user = await self.repository.get_user_by_email(schema.email)

            if user:
                logger.warning("User creation failed: email %s already registered", schema.email)
                raise Conflict(register = schema.email)
        
            new_user = await self.repository.create_user(schema)

            email_verification_token = create_email_verification_token(new_user.email)

            background_tasks.add_task(self.email_service.send_verification_email, new_user.email, email_verification_token)

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
            
            if not user or not verify_password(user.password_hash, schema.password):
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

            if schema.email != user.email:
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
            
            await self.repository.update_password(schema.new_password, user)
            logger.info("Password updated successfully for user: %s", email)
            return None

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
            
            await self.repository.delete_user(user)
            logger.info("User deleted successfully: %s", email)
            return None
        
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
            
            await self.repository.update_email_verified(user)
            logger.info("Email verified successfully for: %s", email)
            return None
                
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
            
            password_reset_token = create_password_reset_token(user.email)

            await asyncio.to_thread(self.email_service.send_reset_password_email, user.email, password_reset_token)
            return None
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error during forgot password: %s", str(e), exc_info=True)
            raise BadGateway
        
    async def reset_password (self, token: str, schema: ResetPassword):

        try:

            payload = verify_token_jwt(token, "password_reset")

            if not payload:
                logger.warning("Reset password failed: invalid token")
                raise BadRequest
            
            email = payload.get("email")

            user = await self.repository.get_user_by_email(email)

            if not user:
                logger.warning("Reset password failed: user %s not found", email)
                raise NotFound(register = email)
            
            await self.repository.update_password(schema.new_password, user)
            logger.info("Password updated successfully for user: %s", email)
            return None
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error during reset password: %s", str(e), exc_info=True)
            raise BadGateway


