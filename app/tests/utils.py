import logging
import os
from typing import Any

from fastapi.testclient import TestClient

from app.base import config
from app.base.utils.decorator import async_lru_cache
from app.main import app
from app.user.models import User
from app.user.services.token import TokenService
from cli.management_command.data_population import DEFAULT_USERS

logger = logging.getLogger(__name__)
client = TestClient(app)


@async_lru_cache()
async def get_user() -> User:
    return await User.aget({"username": DEFAULT_USERS[0]["username"]})


def get_auth_header(access_token: str) -> dict[str, Any]:
    return {
        "Authorization": f"Bearer {access_token}",
    }


def get_header_by_user(user: User) -> dict[str, Any]:
    access_token = TokenService.create_access_token_from_user(user)

    return get_auth_header(access_token)


@async_lru_cache()
async def get_header() -> dict[str, Any]:
    user = await get_user()

    return get_header_by_user(user)


def get_test_file_path() -> str:
    return os.path.join(config.BASE_DIR, "app/tests/files")


async def get_other_user(current_user: User) -> User:
    return await User.aget_random_one({"_id": {"$ne": current_user.id}})
