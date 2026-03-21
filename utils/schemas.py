from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
import re
from datetime import datetime

class RegisterUser (BaseModel):

    model_config = ConfigDict(from_attributes = True)

    name: str
    email: EmailStr
    phone: str
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("A senha deve conter no minimo 8 caracteres.")
        if not re.search(r"[a-z]", value):
            raise ValueError("A senha deve conter pelo menos 1 letra minuscula.")
        if not re.search(r"[A-Z]", value):
            raise ValueError("A senha deve conter pelo menos 1 letra maiuscula.")
        if not re.search(r"[0-9]", value):
            raise ValueError("A senha deve conter pelo menos 1 numero.")
        if not re.search(r"[^A-Za-z0-9]", value):
            raise ValueError("A senha deve conter pelo menos 1 caractere especial.")

        return value
    
class LoginUser (BaseModel):

    model_config = ConfigDict(from_attributes = True)

    email: EmailStr
    password: str
    
class ResponseUser (BaseModel):

    model_config = ConfigDict(from_attributes = True)

    name: str
    email: EmailStr
    phone: str
    created_at: datetime

class UpdateUser (BaseModel):

    model_config = ConfigDict(from_attributes = True)

    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None

class CreateQuestion (BaseModel):

    model_config = ConfigDict(from_attributes = True)

    description: str

class ResponseQuestion (BaseModel):

    model_config = ConfigDict(from_attributes = True)

    description: str
    answers: list

class AnswerQuestion (BaseModel):

    model_config = ConfigDict(from_attributes = True)

    question: str
    answer: str

class ResponseAnswerQuestion (BaseModel):

    answer: str
    user: ResponseUser


class ResponseQuestionsByUser(BaseModel):

    model_config = ConfigDict(from_attributes = True)

    question: str
    answer: str