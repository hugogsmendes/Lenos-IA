from fastapi import APIRouter, Depends, status
from utils.schemas import ResponseQuestion, CreateQuestion, ResponseQuestionsByUser
from service.question_service import Question_Service
from utils.dependencies import get_question_service, get_current_user

question_router = APIRouter(prefix = "/v1", tags = ["question"])

@question_router.post(path = "/create_question", status_code = status.HTTP_201_CREATED, response_model = ResponseQuestion)
async def create_question(body: CreateQuestion, service: Question_Service = Depends(get_question_service),
                          current_user: dict = Depends(get_current_user)):
    return await service.create_question(body.description)

@question_router.get(path = "/user/answers_questions", status_code = status.HTTP_200_OK, response_model = list[ResponseQuestionsByUser])
async def get_questions_by_user(service: Question_Service = Depends(get_question_service),
                         current_user: dict = Depends(get_current_user)):
    return await service.get_questions_by_user(current_user.get("id"))