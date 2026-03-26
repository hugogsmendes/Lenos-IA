from dotenv import load_dotenv
import os
from fastapi import Response

load_dotenv()

ACCESS_TOKEN_EXPIRE = int(os.getenv("ACCESS_TOKEN_EXPIRE"))
REFRESH_TOKEN_EXPIRE = int(os.getenv("REFRESH_TOKEN_EXPIRE"))
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE")
COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN")
COOKIES_SECURE = os.getenv("COOKIE_SECURE")
ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"


def _cookie_kwargs(duration: int) -> dict:
    return {
        "httponly": True,
        "secure": COOKIES_SECURE,
        "max_age": duration,
        "path": "/v1",
        "samesite": COOKIE_SAMESITE,
        "domain": COOKIE_DOMAIN,
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
    response.delete_cookie(
        key = ACCESS_COOKIE_NAME,
        path = "/v1",
        samesite = COOKIE_SAMESITE,
        domain = COOKIE_DOMAIN,
    )
    response.delete_cookie(
        key = REFRESH_COOKIE_NAME,
        path = "/v1",
        samesite = COOKIE_SAMESITE,
        domain = COOKIE_DOMAIN,
    )

    
