from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from utils.database import SessionLocal
from fastapi import Depends, Request, HTTPException
from repository.user_repository import User_Repository
from service.user_service import User_Service
from repository.question_repository import Question_Repository
from service.question_service import Question_Service
from repository.answer_repository import Answer_Repository
from service.answer_service import Answer_Service
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.exceptions import Unauthorized, BadRequest
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

def get_answer_service(repository: Answer_Repository = Depends(get_answer_repository)):
    return Answer_Service(repository = repository)

async def get_current_user(request: Request, credential: HTTPAuthorizationCredentials = Depends(security),
                     repository: User_Repository = Depends(get_user_repository)):
    try:
        token = credential.credentials if credential else request.cookies.get("access_token")
        if not token:
            raise Unauthorized(detail = "Não autenticado")
    
        payload = verify_token_jwt(token, "access")

        if not payload:
            raise Unauthorized(detail = "Token inválido")
        
        user = await repository.get_user_by_email(payload.get("email"))

        if not user:
            raise Unauthorized(detail = "Usuário não encontrado")

        return user

    except HTTPException:
        raise
    except Exception:
        raise BadRequest