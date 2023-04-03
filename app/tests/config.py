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

logger = logging.getLogger(__name__)
client = TestClient(app)

TEST_USERNAME = os.environ.get("TEST_USERNAME", "username")
TEST_PASS = os.environ.get("TEST_PASS", "testpass")


@pytest.fixture(autouse=True)
def init_config():
    connect(config.MONGO_HOST)

    user = User.find_one({"username": TEST_USERNAME})
    if not user:
        response = client.post(
            "/api/v1/registration",
            json={
                "username": TEST_USERNAME,
                "password": TEST_PASS,
                "full_name": "Test Name",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        user = User.get({"username": TEST_USERNAME})

    yield None

    disconnect()


@lru_cache(maxsize=None)
def get_token():
    response = client.post(
        "/token", data={"username": TEST_USERNAME, "password": TEST_PASS}
    )
    assert response.status_code == status.HTTP_200_OK
    return response.json()["access_token"]


@lru_cache(maxsize=None)
def get_header():
    token = get_token()
    return {
        "Authorization": f"Bearer {token}",
    }
