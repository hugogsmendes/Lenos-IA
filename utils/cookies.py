from dotenv import load_dotenv
import os
from fastapi import Response

load_dotenv()

ACCESS_TOKEN_EXPIRE = int(os.getenv("ACCESS_TOKEN_EXPIRE"))
REFRESH_TOKEN_EXPIRE = int(os.getenv("REFRESH_TOKEN_EXPIRE"))
ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"
ENV = os.getenv("ENV")

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


def set_access_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key = ACCESS_COOKIE_NAME,
        value = token,
        **_cookie_kwargs(ACCESS_TOKEN_EXPIRE),
    )


def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key = REFRESH_COOKIE_NAME,
        value = token,
        **_cookie_kwargs(REFRESH_TOKEN_EXPIRE),
    )

def clear_auth_cookies(response: Response) -> None:

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