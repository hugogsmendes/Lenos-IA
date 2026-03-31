from fastapi import APIRouter, Depends, status, Response, Request
from utils.schemas import ResponseUser, RegisterUser, LoginUser, UpdateUser, UpdatePasswordUser
from service.user_service import User_Service
from utils.dependencies import get_user_service, get_current_user
from utils.cookies import clear_auth_cookies, set_access_cookie, set_refresh_cookie

user_router = APIRouter(prefix = "/v1", tags = ["user"])

@user_router.post(path = "/register", status_code = status.HTTP_201_CREATED, response_model = ResponseUser)
async def register_user (body: RegisterUser, service: User_Service = Depends(get_user_service)):
    return await service.create_user(body)

@user_router.post(path = "/login", status_code = status.HTTP_200_OK)
async def login (response: Response, body: LoginUser, service: User_Service = Depends(get_user_service)):
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

@user_router.get(path = "/me", status_code = status.HTTP_200_OK, response_model = ResponseUser)
async def me (current_user = Depends(get_current_user)):
    return current_user

@user_router.put(path = "/update_user", status_code = status.HTTP_204_NO_CONTENT)
async def update_user (response: Response, body: UpdateUser, service: User_Service = Depends(get_user_service), 
                       current_user = Depends(get_current_user)):
    res = await service.update_user(body, getattr(current_user, "email", None))
    set_access_cookie(response, res.get("access_token"))
    set_refresh_cookie(response, res.get("refresh_token"))

@user_router.put(path = "/update_password", status_code = status.HTTP_204_NO_CONTENT)
async def update_password (body: UpdatePasswordUser, service: User_Service = Depends(get_user_service),
                            current_user = Depends(get_current_user)):
    return await service.update_password(body, getattr(current_user, "email", None))

@user_router.delete(path = "/delete_user", status_code = status.HTTP_200_OK)
async def delete_user (response: Response, service: User_Service = Depends(get_user_service), current_user = Depends(get_current_user)):

    await service.delete_user(getattr(current_user, "email", None))
    clear_auth_cookies(response)
    return {"message": "Usuario deletado com sucesso"}