from dotenv import load_dotenv
import os
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
import jwt
from datetime import datetime, timedelta, timezone

load_dotenv()

PEPPER = str(os.getenv("pepper"))
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE = int(os.getenv("ACCESS_TOKEN_EXPIRE"))
REFRESH_TOKEN_EXPIRE = int(os.getenv("REFRESH_TOKEN_EXPIRE"))

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

def create_access_token (user_id, name, email, token_duration = timedelta(seconds = ACCESS_TOKEN_EXPIRE)):
    expire = datetime.now(timezone.utc) + token_duration

    payload = {
        "sub": str(user_id),
        "name": name,
        "email": email,
        "exp": expire,
        "type": "access"
    }

    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm = ALGORITHM)
    return encoded_jwt

def create_refresh_token (user_id, name, email, token_duration = timedelta(seconds = REFRESH_TOKEN_EXPIRE)):
    expire = datetime.now(timezone.utc) + token_duration

    payload = {
        "sub": str(user_id),
        "name": name,
        "email": email,
        "exp": expire,
        "type": "refresh"
    }

    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm = ALGORITHM)
    return encoded_jwt

def verify_token_jwt (token_jwt: str, expected_type: str | None = None):

    try:
        payload = jwt.decode(token_jwt, SECRET_KEY, algorithms = [ALGORITHM])

        if expected_type and payload.get("type") != expected_type:
            return None

        return payload

    except jwt.InvalidTokenError:
        return None
