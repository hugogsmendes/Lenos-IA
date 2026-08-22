from src.settings.config import settings
from fastapi import Response

ACCESS_TOKEN_EXPIRE = settings.ACCESS_TOKEN_EXPIRE
REFRESH_TOKEN_EXPIRE = settings.REFRESH_TOKEN_EXPIRE
ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"
ENV = settings.ENV

def _cookie_kwargs(duration: int) -> dict:
    if ENV == "prod":
        return {
        "httponly": True,
        "secure": True,
        "max_age": duration,
        "path": "/v1",
        "samesite": "lax",
        "domain": "lenos-ia.com.br"
        }
    
    else:
        return {
        "httponly": True,
        "secure": True,
        "max_age": duration,
        "path": "/v1",
        "samesite": "none",
        }


def set_access_token_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key = ACCESS_COOKIE_NAME,
        value = token,
        **_cookie_kwargs(ACCESS_TOKEN_EXPIRE),
    )


def set_refresh_token_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key = REFRESH_COOKIE_NAME,
        value = token,
        **_cookie_kwargs(REFRESH_TOKEN_EXPIRE),
    )

def clear_tokens_cookies(response: Response) -> None:

    if ENV == "prod":
        response.delete_cookie(
            key = ACCESS_COOKIE_NAME,
            httponly = True,
            secure = True,
            path = "/v1",
            samesite = "lax",
            domain = "lenos-ia.com.br",
        )
        response.delete_cookie(
            key = REFRESH_COOKIE_NAME,
            httponly = True,
            secure = True,
            path = "/v1",
            samesite = "lax",
            domain = "lenos-ia.com.br",
        )

    else:
        response.delete_cookie(
            key = ACCESS_COOKIE_NAME,
            httponly = True,
            secure = True,
            path = "/v1",
            samesite = "none",
        )
        response.delete_cookie(
            key = REFRESH_COOKIE_NAME,
            httponly = True,
            secure = True,
            path = "/v1",
            samesite = "none",
        )