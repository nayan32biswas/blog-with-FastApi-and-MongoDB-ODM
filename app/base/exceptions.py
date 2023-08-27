from enum import Enum
from typing import Optional

from fastapi import HTTPException as FastapiHTTPException


class UnicornException(Exception):
    def __init__(self, name: str):
        self.name = name


class CustomException(FastapiHTTPException):
    code: str
    field: Optional[str] = None

    def __init__(
        self, status_code: int, code: str, detail: str, field: Optional[str] = None
    ):
        self.code = code
        self.field = field
        super().__init__(status_code=status_code, detail=detail)


class ExType(str, Enum):
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    UNHANDLED_ERROR = "UNHANDLED_ERROR"

    OBJECT_NOT_FOUND = "OBJECT_NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"

    USERNAME_EXISTS = "USERNAME_EXISTS"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    PERMISSION_ERROR = "PERMISSION_ERROR"
