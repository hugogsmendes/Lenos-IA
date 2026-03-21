from fastapi import APIRouter, Depends, status, HTTPException
from utils.schemas import AnswerQuestion, ResponseAnswerQuestion
from service.answer_service import Answer_Service
from repository.question_repository import Question_Repository
from sessions.dependencies import get_answer_service, get_current_user, get_question_repository
from utils.exceptions import BadRequest

answer_router = APIRouter(prefix = "/v1/user", tags = ["answer"])

@answer_router.post(path = "/answer-question", status_code = status.HTTP_201_CREATED, response_model = ResponseAnswerQuestion)
async def answer_question(body: AnswerQuestion, service: Answer_Service = Depends(get_answer_service),
                          current_user = Depends(get_current_user),
                          question_repository: Question_Repository = Depends(get_question_repository)):
    try:

        question = await question_repository.get_question_by_description(body.question)
        return await service.answer_question(body, getattr(current_user, "id", None), question.id)

    except HTTPException:
        raise
    except Exception:
        raise BadRequest