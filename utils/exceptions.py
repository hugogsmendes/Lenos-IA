from fastapi import HTTPException, status

class RegisterExistsError(HTTPException):

    def __init__(self, register: str, detail: str = "já registrado"):
        self.detail = f"{register} {detail}"

        super().__init__(status_code=status.HTTP_409_CONFLICT,detail=self.detail)

class RegisterNotFoundError(HTTPException):

    def __init__(self, register: str, detail: str = "não encontrado"):
        self.detail = f"{register} {detail}"

        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=self.detail)

class NotPermission (HTTPException):

    def __init__(self, detail: str = "Você não tem permissão para acessar este recurso"):
        self.detail = detail
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=self.detail)

class Unauthorized (HTTPException):

    def __init__(self, detail: str = "Não autentificado"):
        self.detail = detail
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=self.detail)