from fastapi import APIRouter, Depends, status, Response, Request, BackgroundTasks
from utils.schemas import ResponseUser, RegisterUser, LoginUser, UpdateUser, UpdatePasswordUser, ForgotPassword, ResetPassword
from app.main import limiter
from service.user_service import User_Service
from utils.dependencies import get_user_service, get_current_user, get_current_user_adm
from utils.cookies import clear_auth_cookies, set_access_cookie, set_refresh_cookie

user_router = APIRouter(prefix = "/v1", tags = ["user"])

@user_router.post(path = "/register", status_code = status.HTTP_201_CREATED, response_model = ResponseUser)
@limiter.limit("10/minute")
async def register_user (request: Request, body: RegisterUser, background_tasks: BackgroundTasks,
                         service: User_Service = Depends(get_user_service)):
    return await service.create_user(body, background_tasks)

@user_router.post(path = "/login", status_code = status.HTTP_200_OK)
@limiter.limit("10/minute")
async def login (request: Request, response: Response, body: LoginUser, service: User_Service = Depends(get_user_service)):
    res = await service.login(body)
    set_access_cookie(response, res.get("access_token"))
    set_refresh_cookie(response, res.get("refresh_token"))

    return {"message": "Login realizado com sucesso."}

@user_router.post(path = "/logout", status_code = status.HTTP_200_OK)
async def logout (response: Response, current_user: dict = Depends(get_current_user)):
    clear_auth_cookies(response)

    return {"message": "Logout realizado com sucesso."}

@user_router.post(path = "/refresh", status_code = status.HTTP_200_OK)
async def refresh (request: Request, response: Response, service: User_Service = Depends(get_user_service)):
    res = await service.refresh(request)
    set_access_cookie(response, res.get("access_token"))

    return {"message": "Refresh realizado com sucesso"}

@user_router.get(path = "/me", status_code = status.HTTP_200_OK)
async def me (current_user: dict = Depends(get_current_user)):
    return current_user

@user_router.get(path = "/me/adm", status_code = status.HTTP_200_OK)
async def me (current_user: dict = Depends(get_current_user_adm)):
    return current_user

@user_router.put(path = "/update_user", status_code = status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def update_user (request: Request, response: Response, body: UpdateUser, service: User_Service = Depends(get_user_service), 
                       current_user: dict = Depends(get_current_user)):
    res = await service.update_user(body, current_user.get("email"))
    set_access_cookie(response, res.get("access_token"))
    set_refresh_cookie(response, res.get("refresh_token"))

@user_router.put(path = "/update_password", status_code = status.HTTP_204_NO_CONTENT)
async def update_password (response: Response, body: UpdatePasswordUser, service: User_Service = Depends(get_user_service),
                            current_user: dict = Depends(get_current_user)):
    
    await service.update_password(body, current_user.get("email"))
    clear_auth_cookies(response)


@user_router.delete(path = "/delete_user", status_code = status.HTTP_200_OK)
async def delete_user (response: Response, service: User_Service = Depends(get_user_service), 
                       current_user: dict = Depends(get_current_user)):

    await service.delete_user(current_user.get("email"))
    clear_auth_cookies(response)
    return {"message": "Usuario deletado com sucesso"}

@user_router.post(path = "/verify_email", status_code = status.HTTP_200_OK)
@limiter.limit("5/minute")
async def verify_email (request: Request, token: str, service: User_Service = Depends(get_user_service)):

    await service.verify_email(token)

    return {"message": "Email verificado com sucesso"}

@user_router.post(path = "/forgot_password", status_code = status.HTTP_200_OK)
@limiter.limit("5/minute")
async def forgot_password (request: Request, body: ForgotPassword, service: User_Service = Depends(get_user_service)):

    await service.forgot_password(body)

    return {"message": "Email para redefinir senha enviado"}

@user_router.post(path = "/reset_password", status_code = status.HTTP_200_OK)
@limiter.limit("5/minute")
async def reset_password (request: Request, body: ResetPassword, service: User_Service = Depends(get_user_service)):
    
    await service.reset_password(body)

    return {"message": "Senha redefinida com sucesso"}
