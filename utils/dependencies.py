from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from database.postgres import SessionLocal
from fastapi import Depends, Request, HTTPException
from repository.user_repository import User_Repository
from service.user_service import User_Service
from repository.question_repository import Question_Repository
from service.question_service import Question_Service
from repository.answer_repository import Answer_Repository
from service.answer_service import Answer_Service
from repository.analyses_repository import Analyse_Repository
from service.analyse_service import Analyse_Service
from repository.comment_repository import Comment_Repository
from service.comment_service import Comment_Service
from repository.report_repository import Report_Repository
from service.report_service import Report_Service
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.exceptions import Unauthorized, BadGateway
from utils.security import verify_token_jwt

security = HTTPBearer(auto_error = False)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session        

def get_user_repository(session: AsyncSession = Depends(get_session)):
    return User_Repository(session = session)

def get_user_service(repository: User_Repository = Depends(get_user_repository)):
    return User_Service(repository = repository)

def get_question_repository(session: AsyncSession = Depends(get_session)):
    return Question_Repository(session = session)

def get_question_service(repository: Question_Repository = Depends(get_question_repository)):
    return Question_Service(repository = repository)

def get_answer_repository(session: AsyncSession = Depends(get_session)):
    return Answer_Repository(session = session)

def get_answer_service(repository: Answer_Repository = Depends(get_answer_repository),
                       question_repository: Question_Repository = Depends(get_question_repository)):
    return Answer_Service(repository = repository, question_repository = question_repository)

def get_analyse_repository(session: AsyncSession = Depends(get_session)):
    return Analyse_Repository(session = session)

def get_analyse_service(repository: Analyse_Repository = Depends(get_analyse_repository)):
    return Analyse_Service(repository = repository)

def get_comment_repository(session: AsyncSession = Depends(get_session)):
    return Comment_Repository(session = session)

def get_comment_service(repository: Comment_Repository = Depends(get_comment_repository)):
    return Comment_Service(repository = repository)

def get_report_repository(session: AsyncSession = Depends(get_session)):
    return Report_Repository(session = session)

def get_report_service(repository: Report_Repository = Depends(get_report_repository)):
    return Report_Service(repository = repository)

async def get_current_user(request: Request, credential: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = request.cookies.get("access_token")
        if not token:
            raise Unauthorized(detail = "Não autenticado")
    
        payload = verify_token_jwt(token, "access")

        if not payload:
            raise Unauthorized(detail = "Não autenticado")
        
        return {
            "id": payload.get("sub"),
            "name": payload.get("name"),
            "email": payload.get("email"),
            "phone": payload.get("phone")
        }

    except HTTPException:
        raise
    except Exception:
        raise BadGateway