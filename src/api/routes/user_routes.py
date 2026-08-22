from fastapi import APIRouter, Depends, status, Response, Request, BackgroundTasks
from src.utils.schemas import (ResponseUser, RegisterUser, LoginUser, UpdateUser, UpdatePasswordUser, 
                           ForgotPassword, ResetPassword, MessageError, RateLimitError, UserMessage, UserMe)
from src.app.main import limiter
from src.service.user_service import User_Service
from src.utils.dependencies import get_user_service, get_current_user, get_current_user_adm
from src.utils.cookies import clear_tokens_cookies, set_access_token_cookie, set_refresh_token_cookie

user_router = APIRouter(prefix = "/v1/user", tags = ["user"])

user_register_responses = {
    201: {"model": ResponseUser, "description": "Usuário registrado"},
    400: {"model": MessageError, "description": "Não aceitou os termos"},
    409: {"model": MessageError, "description": "Email já cadastrado"},
    429: {"model": RateLimitError, "description": "Limite de requisição"},
    502: {"model": MessageError, "description": "Serviço indisponível"}
}

user_login_responses = {
    200: {"model": UserMessage, "description": "Usuário logado"},
    401: {"model": MessageError, "description": "Credencias inválidas"},
    429: {"model": RateLimitError, "description": "Limite de requisição"},
    502: {"model": MessageError, "description": "Serviço indisponível"}
}

user_logout_responses = {
    200: {"model": UserMessage, "description": "Usuário deslogado"},
    403: {"model": MessageError, "description": "Sem permissão"},
    502: {"model": MessageError, "description": "Serviço indisponível"}
}

user_refresh_responses = {
    200: {"model": UserMessage, "description": "Refresh realizado"},
    400: {"model": MessageError, "description": "Token inválido"},
    502: {"model": MessageError, "description": "Serviço indisponível"}
}

user_me_responses = {
    200: {"model": UserMe, "description": "Usuário atual"},
    403: {"model": MessageError, "description": "Sem permissão"},
    502: {"model": MessageError, "description": "Serviço indisponível"}
}

user_update_responses = {
    204: {"model": None, "description": "Usuário atualizado"},
    403: {"model": MessageError, "description": "Sem permissão"},
    404: {"model": MessageError, "description": "Usuário não encontrado"},
    409: {"model": MessageError, "description": "Email já cadastrado"},
    429: {"model": RateLimitError, "description": "Limite de requisição"},
    502: {"model": MessageError, "description": "Serviço indisponível"}
}

user_update_password_responses = {
    204: {"model": None, "description": "Senha atualizada"},
    401: {"model": MessageError, "description": "Credencias inválidas"},
    403: {"model": MessageError, "description": "Sem permissão"},
    502: {"model": MessageError, "description": "Serviço indisponível"}
}

user_delete_responses = {
    204: {"model": None, "description": "Usuário deletado"},
    403: {"model": MessageError, "description": "Sem permissão"},
    404: {"model": MessageError, "description": "Usuário não encontrado"},
    502: {"model": MessageError, "description": "Serviço indisponível"}
}

user_verify_email_responses = {
    200: {"model": UserMessage, "description": "Email verificado"},
    400: {"model": MessageError, "description": "Token inválido"},
    404: {"model": MessageError, "description": "Usuário não encontrado"},
    429: {"model": RateLimitError, "description": "Limite de requisição"},
    502: {"model": MessageError, "description": "Serviço indisponível"}
}

user_forgot_password_responses = {
    200: {"model": UserMessage, "description": "Email enviado"},
    404: {"model": MessageError, "description": "Usuário não encontrado"},
    429: {"model": RateLimitError, "description": "Limite de requisição"},
    502: {"model": MessageError, "description": "Serviço indisponível"}
}

user_reset_password_responses = {
    200: {"model": UserMessage, "description": "Senha redefinida"},
    400: {"model": MessageError, "description": "Token inválido"},
    404: {"model": MessageError, "description": "Usuário não encontrado"},
    429: {"model": RateLimitError, "description": "Limite de requisição"},
    502: {"model": MessageError, "description": "Serviço indisponível"}
}

@user_router.post(path = "/register", 
                  responses = user_register_responses,
                  status_code = status.HTTP_201_CREATED, response_model = ResponseUser)
@limiter.limit("10/minute")
async def register(request: Request, body: RegisterUser, background_tasks: BackgroundTasks,
                         service: User_Service = Depends(get_user_service)):
    return await service.register(body, background_tasks)

@user_router.post(path = "/login", 
                  responses = user_login_responses,
                  status_code = status.HTTP_200_OK)
@limiter.limit("10/minute")
async def login (request: Request, response: Response, body: LoginUser, service: User_Service = Depends(get_user_service)):
    result = await service.login(body)
    set_access_token_cookie(response, result.get("access_token"))
    set_refresh_token_cookie(response, result.get("refresh_token"))

    return {"message": "Login realizado com sucesso."}

@user_router.post(path = "/logout", 
                  responses = user_logout_responses,
                  status_code = status.HTTP_200_OK)
async def logout (response: Response, current_user: dict = Depends(get_current_user)):
    clear_tokens_cookies(response)

    return {"message": "Logout realizado com sucesso."}

@user_router.post(path = "/refresh",
                  responses = user_refresh_responses, 
                  status_code = status.HTTP_200_OK)
async def refresh (request: Request, response: Response, service: User_Service = Depends(get_user_service)):
    result = await service.refresh(request)
    set_access_token_cookie(response, result.get("access_token"))

    return {"message": "Refresh realizado com sucesso"}

@user_router.get(path = "/me", 
                 responses = user_me_responses,
                 status_code = status.HTTP_200_OK)
async def me (current_user: dict = Depends(get_current_user)):
    return current_user

@user_router.get(path = "/me-adm", 
                 responses = user_me_responses,
                 status_code = status.HTTP_200_OK)
async def me_adm (current_user: dict = Depends(get_current_user_adm)):
    return current_user

@user_router.put(path = "", 
                 responses = user_update_responses,
                 status_code = status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def update_user (request: Request, response: Response, body: UpdateUser, service: User_Service = Depends(get_user_service), 
                       current_user: dict = Depends(get_current_user)):
    result = await service.update_user(body, current_user.get("email"))
    set_access_token_cookie(response, result.get("access_token"))
    set_refresh_token_cookie(response, result.get("refresh_token"))

@user_router.put(path = "/password", 
                 responses = user_update_password_responses,
                 status_code = status.HTTP_204_NO_CONTENT)
async def update_password (response: Response, body: UpdatePasswordUser, service: User_Service = Depends(get_user_service),
                            current_user: dict = Depends(get_current_user)):
    
    await service.update_password(body, current_user.get("email"))
    clear_tokens_cookies(response)


@user_router.delete(path = "", 
                    responses = user_delete_responses,
                    status_code = status.HTTP_204_NO_CONTENT)
async def delete_user (response: Response, service: User_Service = Depends(get_user_service), 
                       current_user: dict = Depends(get_current_user)):

    await service.delete_user(current_user.get("email"))
    clear_tokens_cookies(response)

@user_router.post(path = "/verify-email", 
                  responses = user_verify_email_responses,
                  status_code = status.HTTP_200_OK)
@limiter.limit("5/minute")
async def verify_email (request: Request, token: str, service: User_Service = Depends(get_user_service)):

    await service.verify_email(token)

    return {"message": "Email verificado com sucesso"}

@user_router.post(path = "/forgot-password", 
                  responses = user_forgot_password_responses,
                  status_code = status.HTTP_200_OK)
@limiter.limit("5/minute")
async def forgot_password (request: Request, body: ForgotPassword, service: User_Service = Depends(get_user_service)):

    await service.forgot_password(body)

    return {"message": "Email para redefinir senha enviado"}

@user_router.post(path = "/reset-password", 
                  responses = user_reset_password_responses,
                  status_code = status.HTTP_200_OK)
@limiter.limit("5/minute")
async def reset_password (request: Request, token: str, body: ResetPassword, service: User_Service = Depends(get_user_service)):
    
    await service.reset_password(token, body)

    return {"message": "Senha redefinida com sucesso"}
