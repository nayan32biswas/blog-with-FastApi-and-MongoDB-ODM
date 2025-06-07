import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import jwt
from bson import ObjectId
from fastapi import status

from app.base.base_class import StaticBase
from app.base.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
)
from app.base.exceptions import CustomException, ExType
from app.user.models import User
from app.user.services.auth import AuthService

logger = logging.getLogger(__name__)


class TokenType(str, Enum):
    ACCESS = "ACCESS"
    REFRESH = "REFRESH"


invalid_refresh_token = CustomException(
    status_code=status.HTTP_403_FORBIDDEN,
    code=ExType.PERMISSION_ERROR,
    detail="Invalid Refresh Token",
)


class TokenService(StaticBase):
    @classmethod
    def create_access_token(cls, data: dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "token_type": TokenType.ACCESS})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @classmethod
    def create_refresh_token(cls, data: dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "token_type": TokenType.REFRESH})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @classmethod
    def create_access_token_from_user(cls, user: User) -> str:
        data = {"id": str(user.id), "random_str": str(user.random_str)}

        return cls.create_access_token(data=data)

    @classmethod
    def create_refresh_token_from_user(cls, user: User) -> str:
        data = {"id": str(user.id), "random_str": str(user.random_str)}

        return cls.create_refresh_token(data=data)

    @classmethod
    def create_access_token_from_refresh_token(cls, refresh_token: str) -> str:
        if not refresh_token:
            raise invalid_refresh_token

        try:
            payload: Any = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        except Exception as e:
            raise invalid_refresh_token from e

        token_type = payload.get("token_type")
        if token_type is None or token_type != TokenType.REFRESH:
            raise invalid_refresh_token

        user = User.find_one(
            {"_id": ObjectId(payload["id"]), "random_str": payload["random_str"]}
        )
        if user is None:
            raise invalid_refresh_token

        access_token = cls.create_access_token_from_user(user)

        return access_token


def token_response(username: str, password: str) -> Any:
    user = AuthService.authenticate_user(username, password)
    if not user or user.is_active is False:
        raise CustomException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ExType.AUTHENTICATION_ERROR,
            detail="Incorrect username or password",
        )

    access_token = TokenService.create_access_token_from_user(user)
    refresh_token = TokenService.create_refresh_token_from_user(user)

    user.update(raw={"$set": {"last_login": datetime.now()}})

    return {
        "token_type": "Bearer",
        "access_token": access_token,
        "refresh_token": refresh_token,
    }
