from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.user.models import User

from .config import get_token, init_config  # noqa

client = TestClient(app)

NEW_USERNAME = "username-exists"
NEW_PASS = "new-pass"
NEW_FULL_NAME = "Full Name"


def test_registration_and_auth():
    _ = User.delete_many({"username": NEW_USERNAME})

    response = client.post(
        "/api/v1/registration",
        json={
            "username": NEW_USERNAME,
            "password": NEW_PASS,
            "full_name": NEW_FULL_NAME,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED

    response = client.post(
        "/token", data={"username": NEW_USERNAME, "password": NEW_PASS}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["access_token"]


def test_duplicate_registration():
    _ = User.delete_many({"username": NEW_USERNAME})

    response = client.post(
        "/api/v1/registration",
        json={
            "username": NEW_USERNAME,
            "password": NEW_PASS,
            "full_name": NEW_FULL_NAME,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED

    response = client.post(
        "/api/v1/registration",
        json={
            "username": NEW_USERNAME,
            "password": NEW_PASS,
            "full_name": NEW_FULL_NAME,
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
