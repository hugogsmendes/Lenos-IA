from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
import re
from datetime import datetime
from uuid import UUID

MAX_NAME_LENGTH = 50
MAX_EMAIL_LENGTH = 200
MIN_PHONE_LENGTH = 13
MAX_PHONE_LENGTH = 20
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 20
MAX_QUESTION_LENGTH = 100
MAX_ANSWER_LENGTH = 50
MAX_TITLE_LENGTH = 50

class RegisterUser (BaseModel):

    model_config = ConfigDict(from_attributes = True, str_strip_whitespace = True)

    name: str = Field(..., min_length = 3, max_length = MAX_NAME_LENGTH)
    email: EmailStr = Field(..., max_length = MAX_EMAIL_LENGTH)
    phone: str = Field(..., min_length = MIN_PHONE_LENGTH, max_length = MAX_PHONE_LENGTH)
    password: str = Field(..., min_length = MIN_PASSWORD_LENGTH, max_length = MAX_PASSWORD_LENGTH)
    terms_accepted: bool

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Nome nao pode ser vazio.")

        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Telefone nao pode ser vazio.")
        if not re.fullmatch(r"\+?[0-9]{8,20}", value):
            raise ValueError("Telefone deve conter apenas numeros e opcional '+' no inicio.")

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < MIN_PASSWORD_LENGTH:
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

    model_config = ConfigDict(from_attributes = True, str_strip_whitespace = True)

    email: EmailStr = Field(..., max_length = MAX_EMAIL_LENGTH)
    password: str = Field(..., min_length = MIN_PASSWORD_LENGTH, max_length = MAX_PASSWORD_LENGTH)
    
class ResponseUser (BaseModel):

    model_config = ConfigDict(from_attributes = True)

    name: str
    email: EmailStr
    phone: str
    created_at: datetime

class UpdateUser (BaseModel):

    model_config = ConfigDict(from_attributes = True, str_strip_whitespace = True)

    name: str | None = Field(default = None, min_length = 3, max_length = MAX_NAME_LENGTH)
    email: EmailStr | None = None
    phone: str | None = Field(default = None, min_length = MIN_PHONE_LENGTH, max_length = MAX_PHONE_LENGTH)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not value.strip():
            raise ValueError("Nome nao pode ser vazio.")

        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not value.strip():
            raise ValueError("Telefone nao pode ser vazio.")
        if not re.fullmatch(r"\+?[0-9]{8,20}", value):
            raise ValueError("Telefone deve conter apenas numeros e opcional '+' no inicio.")

        return value

class UpdatePasswordUser (BaseModel):

    model_config = ConfigDict(from_attributes = True)

    current_password: str
    new_password: str

    @field_validator("new_password")
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

class CreateQuestion (BaseModel):

    model_config = ConfigDict(from_attributes = True, str_strip_whitespace = True)

    description: str = Field(..., min_length = 5, max_length = MAX_QUESTION_LENGTH)

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Descricao da pergunta nao pode ser vazia.")

        return value

class ResponseQuestion (BaseModel):

    model_config = ConfigDict(from_attributes = True)

    description: str

class ResponseAnswersByUser(BaseModel):

    model_config = ConfigDict(from_attributes = True)

    question: str
    answer: str

class AnswerQuestion (BaseModel):

    model_config = ConfigDict(from_attributes = True, str_strip_whitespace = True)

    question_id: UUID
    answer: str = Field(..., min_length = 1, max_length = MAX_ANSWER_LENGTH)

    @field_validator("answer")
    @classmethod
    def validate_answer(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Resposta nao pode ser vazia.")

        return value

class ResponseAnswerQuestion (BaseModel):

    question: ResponseQuestion
    answer: str
    user: ResponseUser

class UpdateAnswer (BaseModel):

    model_config = ConfigDict(from_attributes = True, str_strip_whitespace = True)

    question_id: UUID
    new_answer: str = Field(..., min_length = 1, max_length = MAX_ANSWER_LENGTH)

    @field_validator("new_answer")
    @classmethod
    def validate_answer(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Resposta nao pode ser vazia.")

        return value

class GenerateReport (BaseModel):

    model_config = ConfigDict(from_attributes = True, str_strip_whitespace = True)

    video_url: str

class UpdatedReport (BaseModel):

    model_config = ConfigDict(from_attributes = True, str_strip_whitespace = True)

    report_id: UUID
    title: str = Field(..., min_length = 2, max_length = MAX_TITLE_LENGTH)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Titulo nao pode ser vazia.")

        return value
