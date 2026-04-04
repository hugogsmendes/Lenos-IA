from fastapi import APIRouter, Depends, status
from utils.schemas import AnswerQuestion, ResponseAnswerQuestion, UpdateAnswer
from service.answer_service import Answer_Service
from utils.dependencies import get_answer_service, get_current_user

answer_router = APIRouter(prefix = "/v1/user", tags = ["answer"])

@answer_router.post(path = "/answer_question", status_code = status.HTTP_201_CREATED, response_model = ResponseAnswerQuestion)
async def answer_question(body: AnswerQuestion, service: Answer_Service = Depends(get_answer_service),
                          current_user = Depends(get_current_user)):
       
    return await service.answer_question(body, getattr(current_user, "id", None))

    
@answer_router.put(path = "/update_answer", status_code = status.HTTP_204_NO_CONTENT)
async def update_answer(body: UpdateAnswer, service: Answer_Service = Depends(get_answer_service),
                        current_user = Depends(get_current_user)):
        
    return await service.update_answer(body, getattr(current_user, "id", None))
