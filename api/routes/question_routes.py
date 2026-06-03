from fastapi import APIRouter, Depends, status, Request
from app.main import limiter
from utils.schemas import ResponseQuestion, CreateQuestion
from service.question_service import Question_Service
from utils.dependencies import get_question_service, get_current_user, get_current_user_adm

question_router = APIRouter(prefix = "/v1", tags = ["question"])

@question_router.post(path = "/create_question", status_code = status.HTTP_201_CREATED, response_model = ResponseQuestion)
@limiter.limit("10/minute")
async def create_question(request: Request, body: CreateQuestion, service: Question_Service = Depends(get_question_service),
                          current_user: dict = Depends(get_current_user_adm)):
    return await service.create_question(body.description)

@question_router.get(path = "/questions", status_code = status.HTTP_200_OK)
@limiter.limit("10/minute")
async def list_questions(request: Request, service: Question_Service = Depends(get_question_service), current_user: dict = Depends(get_current_user)):
    return await service.list_questions()