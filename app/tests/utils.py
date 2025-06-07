import logging
import os
from functools import cache
from typing import Any

from fastapi.testclient import TestClient

from app.base import config
from app.main import app
from app.user.models import User
from app.user.services.token import TokenService
from cli.management_command.data_population import users

logger = logging.getLogger(__name__)
client = TestClient(app)


@cache
def get_user() -> User:
    return User.get({"username": users[0]["username"]})


def get_auth_header(access_token: str) -> dict[str, Any]:
    return {
        "Authorization": f"Bearer {access_token}",
    }


def get_header_by_user(user: User) -> dict[str, Any]:
    access_token = TokenService.create_access_token_from_user(user)

    return get_auth_header(access_token)


@cache
def get_header() -> dict[str, Any]:
    user = get_user()

    return get_header_by_user(user)


def get_test_file_path() -> str:
    return os.path.join(config.BASE_DIR, "app/tests/files")


def get_other_user(current_user: User) -> User:
    return User.get_random_one({"_id": {"$ne": current_user.id}})
