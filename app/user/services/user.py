import logging
from datetime import datetime

from fastapi import status

from app.base.exceptions import CustomException, ExType
from app.user.models import User
from app.user.services.auth import AuthService

logger = logging.getLogger(__name__)


def create_user(username: str, full_name: str, plain_password: str) -> User:
    if User.exists({"username": username}):
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ExType.USERNAME_EXISTS,
            detail="Username already exists.",
            field="username",
        )

    try:
        hash_password = AuthService.get_password_hash(plain_password)
        user = User(
            username=username,
            full_name=full_name,
            joining_date=datetime.now(),
            password=hash_password,
            random_str=User.new_random_str(),
        ).create()
    except Exception as ex:
        logger.warning(f"Raise error while creating user error:{ex}")
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ExType.UNHANDLED_ERROR,
            detail="Something wrong. Try later.",
        ) from ex

    return user
