import os
from argon2 import PasswordHasher

PEPPER = str(os.getenv("pepper"))
argon = PasswordHasher()

def hash_password (password: str):
    if PEPPER:
        password_pepper = password + PEPPER
    return argon.hash(password_pepper) if PEPPER else argon.hash(password)

def verify_password (hashed_password: str, password: str):
    if PEPPER:
        password_pepper = password + PEPPER
    return argon.verify(hashed_password, password_pepper) if PEPPER else argon.verify(hashed_password, password)

if __name__ == "__main__":
    hashed_password = hash_password("Teste2025@fatec")
    assert verify_password(hashed_password, "Teste2025@fatec") is True