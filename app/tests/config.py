import logging
import os
from functools import lru_cache
from typing import Any, Dict, Generator

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
def init_config() -> Generator:
    connect(config.MONGO_HOST)

    if not User.exists({"username": users[0]["username"]}):
        populate_dummy_data()

    yield None
    # clean_data()

    disconnect()


@lru_cache(maxsize=None)
def get_user() -> User:
    return User.get({"username": users[0]["username"]})


@lru_cache(maxsize=None)
def get_token() -> str:
    response = client.post(
        "/token",
        data={"username": users[0]["username"], "password": users[0]["password"]},
    )
    assert response.status_code == status.HTTP_200_OK
    return str(response.json()["access_token"])


@lru_cache(maxsize=None)
def get_header() -> Dict[str, Any]:
    token = get_token()
    return {
        "Authorization": f"Bearer {token}",
    }


def get_test_file_path() -> str:
    return os.path.join(config.BASE_DIR, "app/tests/files")
