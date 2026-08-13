from fastapi import APIRouter, Depends, status, Request
from app.main import limiter
from utils.schemas import AnswerQuestion, ResponseAnswerQuestion, UpdateAnswer, MessageError, RateLimitError, ResponseAnswers
from service.answer_service import Answer_Service
from utils.dependencies import get_answer_service, get_current_user
from uuid import UUID

answer_router = APIRouter(prefix = "/v1/user", tags = ["answer"])

answer_create_responses = {
    201: {"model": ResponseAnswerQuestion, "description": "Resposta criada"},
    403: {"model": MessageError, "description": "Sem permissão"},
    404: {"model": MessageError, "description": "Pergunta não encontrada"},
    429: {"model": RateLimitError, "description": "Limite de requisição"},
    502: {"model": MessageError, "description": "Serviço indisponível"}
}

answer_update_responses = {
    204: {"model": None, "description": "Resposta atualizada"},
    400: {"model": MessageError, "description": "Resposta não encontrada ou não pertence ao usuário"},
    403: {"model": MessageError, "description": "Sem permissão"},
    429: {"model": RateLimitError, "description": "Limite de requisição"},
    502: {"model": MessageError, "description": "Serviço indisponível"}
}

list_answers_responses = {
    200: {"model": list[ResponseAnswers], "description": "Respostas listadas"},
    403: {"model": MessageError, "description": "Sem permissão"},
    429: {"model": RateLimitError, "description": "Limite de requisição"},
    502: {"model": MessageError, "description": "Serviço indisponível"}
}

@answer_router.post(path = "/answer", 
                    responses = answer_create_responses,
                    status_code = status.HTTP_201_CREATED, response_model = ResponseAnswerQuestion)
@limiter.limit("10/minute")
async def answer_question(request: Request, body: AnswerQuestion, service: Answer_Service = Depends(get_answer_service),
                          current_user = Depends(get_current_user)):
       
    return await service.answer_question(body, current_user.get("id"))

    
@answer_router.put(path = "/answer/{id}", 
                   responses = answer_update_responses,
                   status_code = status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def update_answer(request: Request, id: UUID, body: UpdateAnswer, service: Answer_Service = Depends(get_answer_service),
                        current_user = Depends(get_current_user)):
        
    return await service.update_answer(id, body, current_user.get("id"))

@answer_router.get(path = "/answers", 
                   responses = list_answers_responses,
                   status_code = status.HTTP_200_OK)
@limiter.limit("10/minute")
async def get_answers_by_user(request: Request, service: Answer_Service = Depends(get_answer_service),
                         current_user: dict = Depends(get_current_user)):
    return await service.get_answers_by_user(current_user.get("id"))
