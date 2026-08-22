from fastapi import HTTPException, status

class Conflict (HTTPException):

    def __init__(self, register: str, detail: str = "já registrado"):
        self.detail = f"{register} {detail}"

        super().__init__(status_code=status.HTTP_409_CONFLICT,detail=self.detail)

class NotFound (HTTPException):

    def __init__(self, register: str, detail: str = "não encontrado"):
        self.detail = f"{register} {detail}"

        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=self.detail)

class Forbidden (HTTPException):

    def __init__(self, detail: str = "Sem permissão"):
        self.detail = detail
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=self.detail)

class Unauthorized (HTTPException):

    def __init__(self, detail: str = "Não autenticado"):
        self.detail = detail
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=self.detail)

class BadRequest (HTTPException):

    def __init__(self, detail: str = "Erro de requisição"):
        self.detail = detail
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=self.detail)

class BadGateway (HTTPException):

    def __init__(self, detail: str = "Serviço indisponível"):
        self.detail = detail
        super().__init__(status_code=status.HTTP_502_BAD_GATEWAY, detail=self.detail)