from fastapi import APIRouter, Depends, status, Response, Request
from utils.schemas import ResponseUser, RegisterUser, LoginUser
from service.user_service import User_Service
from sessions.dependencies import get_user_service
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
def logout (response: Response):
    clear_auth_cookies(response)
    
    return {"message": "Logout realizado com sucesso."}

@user_router.post(path = "/refresh", status_code = status.HTTP_200_OK)
async def refresh (request: Request, response: Response, service: User_Service = Depends(get_user_service)):
    res = await service.refresh(request)
    set_access_cookie(response, res.get("access_token"))

    return {"message": "Refresh realizado com sucesso"}
