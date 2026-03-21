from fastapi import APIRouter, Depends, status
from utils.schemas import ResponseQuestion, CreateQuestion
from service.question_service import Question_Service
from sessions.dependencies import get_question_service, get_current_user

question_router = APIRouter(prefix = "/v1", tags = ["question"])

@question_router.post(path = "/create-question", status_code = status.HTTP_201_CREATED, response_model = ResponseQuestion)
async def create_question(body: CreateQuestion, service: Question_Service = Depends(get_question_service),
                          current_user = Depends(get_current_user)):
    return await service.create_question(body.description)