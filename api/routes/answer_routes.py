from fastapi import APIRouter, Depends, status, Request
from app.main import limiter
from utils.schemas import AnswerQuestion, ResponseAnswerQuestion, UpdateAnswer
from service.answer_service import Answer_Service
from utils.dependencies import get_answer_service, get_current_user

answer_router = APIRouter(prefix = "/v1/user", tags = ["answer"])

@answer_router.post(path = "/answer_question", status_code = status.HTTP_201_CREATED, response_model = ResponseAnswerQuestion)
@limiter.limit("10/minute")
async def answer_question(request: Request, body: AnswerQuestion, service: Answer_Service = Depends(get_answer_service),
                          current_user = Depends(get_current_user)):
       
    return await service.answer_question(body, current_user.get("id"))

    
@answer_router.put(path = "/update_answer", status_code = status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def update_answer(request: Request, body: UpdateAnswer, service: Answer_Service = Depends(get_answer_service),
                        current_user = Depends(get_current_user)):
        
    return await service.update_answer(body, current_user.get("id"))

@answer_router.get(path = "/answers_questions", status_code = status.HTTP_200_OK)
@limiter.limit("10/minute")
async def get_answers_by_user(request: Request, service: Answer_Service = Depends(get_answer_service),
                         current_user: dict = Depends(get_current_user)):
    return await service.get_answers_by_user(current_user.get("id"))
