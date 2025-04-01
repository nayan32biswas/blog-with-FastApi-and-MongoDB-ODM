import logging
import os
from functools import cache
from typing import Any

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from mongodb_odm import connect, disconnect

from app.base import config
from app.main import app
from app.user.models import User

from .data import populate_dummy_data, users

logger = logging.getLogger(__name__)
client = TestClient(app)


@pytest.fixture(autouse=True)
def init_config() -> Any:
    connect(config.MONGO_URL)

    if not User.exists({"username": users[0]["username"]}):
        populate_dummy_data(total_user=10, total_post=100)

    yield None
    # clean_data()

    disconnect()


@cache
def get_user() -> User:
    return User.get({"username": users[0]["username"]})


@cache
def get_token() -> str:
    response = client.post(
        "/token",
        data={"username": users[0]["username"], "password": users[0]["password"]},
    )
    assert response.status_code == status.HTTP_200_OK
    return str(response.json()["access_token"])


@cache
def get_header() -> dict[str, Any]:
    token = get_token()
    return {
        "Authorization": f"Bearer {token}",
    }


def get_test_file_path() -> str:
    return os.path.join(config.BASE_DIR, "app/tests/files")
