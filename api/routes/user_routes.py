from fastapi import APIRouter, Depends, status
from utils.schemas import ResponseUser, RegisterUser
from service.user_service import User_Service
from sessions.dependencies import get_user_service

user_router = APIRouter(prefix = "/v1", tags = ["user"])

@user_router.post(path = "/register", status_code = status.HTTP_201_CREATED, response_model = ResponseUser)
async def register_user (body: RegisterUser, service: User_Service = Depends(get_user_service)):
    return await service.create_user(body)