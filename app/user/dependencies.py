from enum import Enum
from typing import Any

import jwt
from bson import ObjectId
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer

from app.base.config import ALGORITHM, SECRET_KEY
from app.base.exceptions import CustomException, ExType
from app.user.models import User
from app.user.schemas import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
oauth2_scheme_or_none = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

credentials_exception = CustomException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    code=ExType.AUTHENTICATION_ERROR,
    detail="Could not validate credentials",
)

TOKEN_PREFIX = "Bearer"


class TokenType(str, Enum):
    ACCESS = "ACCESS"
    REFRESH = "REFRESH"


def _get_token_data(token: str) -> TokenData:
    payload: Any = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    id: str | None = payload.get("id")
    random_str: str | None = payload.get("random_str")
    if id is None or random_str is None:
        raise credentials_exception
    token_type = payload.get("token_type")
    if token_type is None or token_type != TokenType.ACCESS:
        raise CustomException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ExType.AUTHENTICATION_ERROR,
            detail="Invalid Access Token",
        )
    return TokenData(id=id, random_str=random_str)


async def get_authenticated_token(
    token: str | None = Depends(oauth2_scheme),
) -> TokenData:
    try:
        if token is None:
            raise credentials_exception
        return _get_token_data(token)
    except Exception as e:
        raise credentials_exception from e


async def get_authenticated_user(
    token_data: TokenData = Depends(get_authenticated_token),
) -> User:
    user = await User.afind_one(
        {"_id": ObjectId(token_data.id), "random_str": token_data.random_str},
        projection={"user_links": False, "bio": False},
    )
    if user is None:
        raise credentials_exception
    if user.is_active is False:
        raise CustomException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ExType.AUTHENTICATION_ERROR,
            detail="Inactive User",
        )
    return user


async def get_authenticated_token_or_none(
    token: str | None = Depends(oauth2_scheme_or_none),
) -> TokenData | None:
    try:
        if token is None:
            return None
        return _get_token_data(token)
    except Exception as e:
        raise credentials_exception from e


async def get_authenticated_user_or_none(
    token_data: TokenData = Depends(get_authenticated_token_or_none),
) -> User | None:
    if not token_data:
        return None
    user = await User.afind_one(
        {"_id": ObjectId(token_data.id), "random_str": token_data.random_str}
    )
    if user and user.is_active:
        return user
    return None
