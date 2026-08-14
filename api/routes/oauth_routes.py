from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import RedirectResponse
from app.main import limiter
from service.user_service import User_Service
from utils.dependencies import get_user_service, get_current_user
from settings.config import Settings
from utils.schemas import MessageError, RateLimitError

settings = Settings()

AUTH_URI = settings.AUTH_URI
TOKEN_URI = settings.TOKEN_URI
SCOPE = settings.SCOPE
REDIRECT_URI = settings.REDIRECT_URI
CLIENT_ID = settings.CLIENT_ID
CLIENT_SECRET = settings.CLIENT_SECRET

oauth_router = APIRouter(prefix = "/v1/oauth2", tags = ["oauth2"])

oauth_login_responses = {
    307: {"model": None, "description": "Redirecionamento temporário"},
    403: {"model": MessageError, "description": "Sem permissão"},
    429: {"model": RateLimitError, "description": "Limite de requisição"},
}

@oauth_router.get(path = "/login", 
                  responses = oauth_login_responses,
                  status_code = status.HTTP_307_TEMPORARY_REDIRECT)
@limiter.limit("10/minute")
async def oauth_login (request: Request, current_user: dict = Depends(get_current_user)):

    auth_url = f"{AUTH_URI}?scope={SCOPE}&access_type=offline&response_type=code&prompt=consent&redirect_uri={REDIRECT_URI}&client_id={CLIENT_ID}"
    return RedirectResponse(auth_url)

@oauth_router.get(path = "/callback", status_code = status.HTTP_200_OK)
async def ouath_callback (code: str, current_user: dict = Depends(get_current_user)):
    ...