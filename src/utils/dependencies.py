from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from src.database.postgres_client import SessionLocal
from src.database.redis_client import get_redis
from src.utils.logging import get_logger
from src.utils.exceptions import BadGateway, Forbidden
from src.utils.security import verify_token_jwt
from fastapi import Depends, Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.repository.user_repository import User_Repository
from src.service.user_service import User_Service
from src.service.email_service import Email_Service
from src.repository.question_repository import Question_Repository
from src.service.question_service import Question_Service
from src.repository.answer_repository import Answer_Repository
from src.service.answer_service import Answer_Service
from src.repository.analysis_repository import Analysis_Repository
from src.service.analysis_service import Analysis_Service
from src.repository.comment_repository import Comment_Repository
from src.service.comment_service import Comment_Service
from src.repository.report_repository import Report_Repository
from src.service.report_service import Report_Service
from src.repository.oauth_repository import Oauth_Repository
from src.service.oauth_service import Oauth_Service

logger = get_logger("dependencies")

security = HTTPBearer(auto_error = False)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session  

async def get_session_redis():
    session = await get_redis()
    try:
        yield session
    finally:
        await session.aclose()      

def get_user_repository(session: AsyncSession = Depends(get_session)):
    return User_Repository(session = session)

def get_email_service():
    return Email_Service()

def get_user_service(repository: User_Repository = Depends(get_user_repository),
                     email_service: Email_Service = Depends(get_email_service)):
    return User_Service(repository = repository, email_service = email_service)

def get_question_repository(session: AsyncSession = Depends(get_session), cache: Redis = Depends(get_session_redis)):
    return Question_Repository(session = session, cache = cache)

def get_question_service(repository: Question_Repository = Depends(get_question_repository)):
    return Question_Service(repository = repository)

def get_answer_repository(session: AsyncSession = Depends(get_session), cache: Redis = Depends(get_session_redis)):
    return Answer_Repository(session = session, cache = cache)

def get_answer_service(repository: Answer_Repository = Depends(get_answer_repository),
                       question_repository: Question_Repository = Depends(get_question_repository)):
    return Answer_Service(repository = repository, question_repository = question_repository)

def get_analysis_repository(session: AsyncSession = Depends(get_session)):
    return Analysis_Repository(session = session)

def get_analysis_service(repository: Analysis_Repository = Depends(get_analysis_repository)):
    return Analysis_Service(repository = repository)

def get_oauth_repository(session: AsyncSession = Depends(get_session)):
    return Oauth_Repository(session = session)

def get_oauth_service(repository: Oauth_Repository = Depends(get_oauth_repository)):
    return Oauth_Service(repository = repository)

def get_comment_repository(session: AsyncSession = Depends(get_session)):
    return Comment_Repository(session = session)

def get_comment_service(repository: Comment_Repository = Depends(get_comment_repository)):
    return Comment_Service(repository = repository)

def get_report_repository(session: AsyncSession = Depends(get_session), cache: Redis = Depends(get_session_redis)):
    return Report_Repository(session = session, cache = cache)

def get_report_service(repository: Report_Repository = Depends(get_report_repository),
                       comment_service: Comment_Service = Depends(get_comment_service),
                       analysis_service: Analysis_Service = Depends(get_analysis_service),
                       oauth_service: Oauth_Service = Depends(get_oauth_service)):
    
    return Report_Service(repository = repository, comment_service = comment_service, 
                          analysis_service = analysis_service, oauth_service = oauth_service)

async def get_current_user(request: Request, credential: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = request.cookies.get("access_token")
        if not token:
            logger.warning("Authentication failed: No access_token found in cookies")
            raise Forbidden
    
        payload = verify_token_jwt(token, "access")

        if not payload:
            logger.warning("Authentication failed: Invalid or expired token")
            raise Forbidden
        
        logger.info("User authenticated: %s (id: %s)", payload.get("email"), payload.get("sub"))
        return {
            "id": payload.get("sub"),
            "name": payload.get("name"),
            "email": payload.get("email"),
            "phone": payload.get("phone"),
            "role": payload.get("role")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in get_current_user: %s", str(e), exc_info=True)
        raise BadGateway
    
async def get_current_user_adm (current_user: dict = Depends(get_current_user)):
    
    if not current_user.get("role") == "admin":
        logger.warning("Authorization failed: User %s does not have admin role", current_user.get("email"))
        raise Forbidden
    
    logger.info("Admin user authorized: %s", current_user.get("email"))
    return current_user