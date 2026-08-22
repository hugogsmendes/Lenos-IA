from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
import jwt
from datetime import datetime, timedelta, timezone
from src.utils.logging import get_logger
from src.settings.config import settings
from uuid import UUID

logger = get_logger("security")


PEPPER = settings.PEPPER
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE = settings.ACCESS_TOKEN_EXPIRE
REFRESH_TOKEN_EXPIRE = settings.REFRESH_TOKEN_EXPIRE

argon = PasswordHasher()

def hash_password (password: str):
    if PEPPER:
        password_pepper = password + PEPPER
    return argon.hash(password_pepper) if PEPPER else argon.hash(password)

def verify_password (hashed_password: str, password: str):
    if PEPPER:
        password_pepper = password + PEPPER
    try:
        return argon.verify(hashed_password, password_pepper) if PEPPER else argon.verify(hashed_password, password)
    except VerificationError:
        return False

def create_access_token (user_id: UUID, name: str, email: str, phone: str, role: str, token_duration = timedelta(seconds = ACCESS_TOKEN_EXPIRE)):
    expire = datetime.now(timezone.utc) + token_duration

    payload = {
        "sub": str(user_id),
        "name": name,
        "email": email,
        "phone": phone, 
        "role": role,
        "exp": expire,
        "type": "access"
    }

    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm = ALGORITHM)
    logger.info("Access token created for user_id: %s", user_id)
    return encoded_jwt

def create_refresh_token (user_id: UUID, name: str, email: str, phone: str, role: str, token_duration = timedelta(seconds = REFRESH_TOKEN_EXPIRE)):
    expire = datetime.now(timezone.utc) + token_duration

    payload = {
        "sub": str(user_id),
        "name": name,
        "email": email,
        "phone": phone,
        "role": role,
        "exp": expire,
        "type": "refresh"
    }

    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm = ALGORITHM)
    logger.info("Refresh token created for user_id: %s", user_id)
    return encoded_jwt

def create_email_verification_token (email: str, token_duration = timedelta(hours = 24)):
    expire = datetime.now(timezone.utc) + token_duration

    payload = {
        "email": email,
        "exp": expire,
        "type": "email_verification"
    }

    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm = ALGORITHM)
    logger.info("Email verification token created for: %s", email)
    return encoded_jwt  

def create_password_reset_token (email: str, token_duration = timedelta(hours = 24)):
    expire = datetime.now(timezone.utc) + token_duration

    payload = {
        "email": email,
        "exp": expire,
        "type": "password_reset"
    }

    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm = ALGORITHM)
    logger.info("Password reset token created for: %s", email)
    return encoded_jwt 

def verify_token_jwt (token_jwt: str, expected_type: str | None = None):

    try:
        payload = jwt.decode(token_jwt, SECRET_KEY, algorithms = [ALGORITHM])

        if expected_type and payload.get("type") != expected_type:
            logger.warning("Token type mismatch. Expected: %s, Got: %s", expected_type, payload.get("type"))
            return None

        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("Token verification failed: signature expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning("Token verification failed: invalid token - %s", str(e))
        return None
    except Exception as e:
        logger.error("Unexpected error during token verification: %s", str(e))
        return None
