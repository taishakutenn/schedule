from fastapi import HTTPException, status


class CredentialsException(HTTPException):
    """Исключение для ошибок аутентификации"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учётные данные",
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenAccess(HTTPException):
    """Исключение для запрета доступа"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения этой операции",
            headers={"WWW-Authenticate": "Bearer"},
        )
