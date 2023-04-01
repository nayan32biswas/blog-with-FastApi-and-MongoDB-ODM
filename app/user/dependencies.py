from enum import Enum
from typing import Any

import jwt
from bson import ObjectId  # type: ignore
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.base.config import ALGORITHM, SECRET_KEY
from app.user.models import User

from .schemas import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
oauth2_scheme_or_none = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

TOKEN_PREFIX = "Bearer"


class TokenType(str, Enum):
    ACCESS = "ACCESS"
    REFRESH = "REFRESH"


def _get_token_data(token: str) -> TokenData:
    payload: Any = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    id: str = payload.get("id")
    if id is None:
        print("id is None")
        raise credentials_exception
    token_type = payload.get("token_type")
    if token_type is None or token_type != TokenType.ACCESS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Access Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    r_str = payload.get("r_str")
    return TokenData(id=id, r_str=r_str)


async def get_authenticated_token(token: str = Depends(oauth2_scheme)):
    try:
        if token is None:
            raise credentials_exception
        return _get_token_data(token)
    except Exception:
        raise credentials_exception


async def get_authenticated_user(
    token_data: TokenData = Depends(get_authenticated_token),
):
    user = User.find_one({"_id": ObjectId(token_data.id), "rand_str": token_data.r_str})
    if user is None:
        raise credentials_exception
    if user.is_active is False:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


async def get_authenticated_token_or_none(token: str = Depends(oauth2_scheme_or_none)):
    try:
        if token is None:
            return None
        return _get_token_data(token)
    except Exception:
        raise credentials_exception


async def get_authenticated_user_or_none(
    token_data: TokenData = Depends(get_authenticated_token_or_none),
):
    if not token_data:
        return None
    user = User.find_one({"_id": ObjectId(token_data.id), "rand_str": token_data.r_str})
    if user and user.is_active:
        return user
    return None
