import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.base.exceptions import CustomException, ExType
from app.base.utils import update_partially

from .dependencies import get_authenticated_user
from .models import User
from .schemas import LoginIn, Registration, UpdateAccessTokenIn, UserIn, UserOut
from .utils import (
    authenticate_user,
    create_access_token,
    create_access_token_from_refresh_token,
    create_refresh_token,
    get_password_hash,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/api/v1/registration", status_code=status.HTTP_201_CREATED, response_model=UserOut
)
def registration(data: Registration) -> Any:
    if User.exists({"username": data.username}):
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ExType.USERNAME_EXISTS,
            detail="Username already exists.",
            field="email",
        )

    try:
        hash_password = get_password_hash(data.password)
        user = User(
            username=data.username,
            full_name=data.full_name,
            joining_date=datetime.utcnow(),
            password=hash_password,
            random_str=User.new_random_str(),
        ).create()
    except Exception as ex:
        logger.warning(f"Raise error while creating user error:{ex}")
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ExType.UNHANDLED_ERROR,
            detail="Something wrong. Try later.",
        )

    return UserOut.from_orm(user)


def token_response(username: str, password: str) -> Any:
    user = authenticate_user(username, password)
    if not user or user.is_active is False:
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ExType.AUTHENTICATION_ERROR,
            detail="Incorrect username or password",
        )
    access_token = create_access_token(
        data={"id": str(user.id), "random_str": str(user.random_str)}
    )
    refresh_token = create_refresh_token(
        data={"id": str(user.id), "random_str": str(user.random_str)}
    )
    user.update(raw={"$set": {"last_login": datetime.utcnow()}})
    return {
        "token_type": "Bearer",
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@router.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    return token_response(form_data.username, form_data.password)


@router.post("/api/v1/token")
def login(data: LoginIn) -> Any:
    return token_response(data.username, data.password)


@router.post("/api/v1/update-access-token")
def update_access_token(
    data: UpdateAccessTokenIn = Body(...),
) -> Any:
    access_token = create_access_token_from_refresh_token(data.refresh_token)
    return {"access_token": access_token}


@router.get("/api/v1/me", response_model=UserOut)
def ger_me(user: User = Depends(get_authenticated_user)) -> Any:
    return UserOut.from_orm(user)


@router.patch("/api/v1/update-user", response_model=UserOut)
def update_user(user_data: UserIn, user: User = Depends(get_authenticated_user)) -> Any:
    user = update_partially(user, user_data)
    user.update()
    return UserOut.from_orm(user)


@router.put("/api/v1/logout-from-all-device")
def logout_from_all_device(user: User = Depends(get_authenticated_user)) -> Any:
    user.random_str = User.new_random_str()
    user.update()
    return {"message": "Logged out."}
