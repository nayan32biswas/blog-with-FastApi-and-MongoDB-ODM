import logging
import os
from functools import lru_cache

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
def init_config():
    connect(config.MONGO_HOST)

    if not User.exists({"username": users[0]["username"]}):
        populate_dummy_data()

    yield None
    # clean_data()

    disconnect()


@lru_cache(maxsize=None)
def get_user():
    return User.get({"username": users[0]["username"]})


@lru_cache(maxsize=None)
def get_token():
    response = client.post(
        "/token",
        data={"username": users[0]["username"], "password": users[0]["password"]},
    )
    assert response.status_code == status.HTTP_200_OK
    return response.json()["access_token"]


@lru_cache(maxsize=None)
def get_header():
    token = get_token()
    return {
        "Authorization": f"Bearer {token}",
    }


def get_test_file_path():
    return os.path.join(config.BASE_DIR, "app/tests/files")
