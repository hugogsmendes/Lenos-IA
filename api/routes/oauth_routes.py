from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import RedirectResponse
from app.main import limiter
from service.oauth_service import Oauth_Service
from utils.dependencies import get_oauth_service, get_current_user
from settings.config import Settings
from utils.schemas import MessageError, RateLimitError, UserMessage

settings = Settings()

AUTH_URI = settings.AUTH_URI
SCOPE = settings.SCOPE
REDIRECT_URI = settings.REDIRECT_URI
CLIENT_ID = settings.CLIENT_ID

oauth_router = APIRouter(prefix = "/v1/oauth2", tags = ["oauth2"])

oauth_login_responses = {
    307: {"model": None, "description": "Redirecionamento temporário"},
    400: {"model": MessageError, "description": "Conta Youtube já conectada"},
    403: {"model": MessageError, "description": "Sem permissão"},
    429: {"model": RateLimitError, "description": "Limite de requisição"},
    502: {"model": MessageError, "description": "Serviço indisponível"}
}

oauth_callback_responses = {
    200: {"model": UserMessage, "description": "Conta Youtube conectada"},
    400: {"model": MessageError, "description": "Código de autorização inválido"},
    403: {"model": MessageError, "description": "Sem permissão"},
    404: {"model": MessageError, "description": "Não foi possível encontrar o canal"},
    429: {"model": RateLimitError, "description": "Limite de requisição"},
    502: {"model": MessageError, "description": "Serviço indisponível"}
}

@oauth_router.get(path = "/login", 
                  responses = oauth_login_responses,
                  status_code = status.HTTP_307_TEMPORARY_REDIRECT)
@limiter.limit("10/minute")
async def oauth_login (request: Request, service: Oauth_Service = Depends(get_oauth_service), current_user: dict = Depends(get_current_user)):
    await service.get_oauth_tokens_by_user_id(current_user.get("id"))
    auth_url = f"{AUTH_URI}?scope={SCOPE}&access_type=offline&response_type=code&prompt=consent&redirect_uri={REDIRECT_URI}&client_id={CLIENT_ID}"
    return RedirectResponse(auth_url)

@oauth_router.get(path = "/callback", 
                  responses = oauth_callback_responses,
                  status_code = status.HTTP_200_OK)
@limiter.limit("10/minute")
async def ouath_callback (request: Request, code: str, service: Oauth_Service = Depends(get_oauth_service), current_user: dict = Depends(get_current_user)):
    await service.create_oauth(current_user.get("id"), code)
    return {"message": "Conta Youtube conectada com sucesso"}