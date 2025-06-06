from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.tests.endpoints import Endpoints
from app.tests.utils import get_header, get_user
from cli.management_command.data_population import users

client = TestClient(app)


def test_get_me() -> None:
    response = client.get(Endpoints.ME, headers=get_header())
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == users[0]["username"]


def test_get_user_details() -> None:
    user = get_user()
    response = client.get(Endpoints.USER_PROFILE, headers=get_header())

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == user.username


def test_update_user() -> None:
    new_full_name = "New Name"
    response = client.patch(
        Endpoints.USER_UPDATE, json={"full_name": new_full_name}, headers=get_header()
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["full_name"] == new_full_name
    assert response.json()["username"] == users[0]["username"]


def test_user_public_profile() -> None:
    user = get_user()
    response = client.get(Endpoints.PUBLIC_PROFILE.format(username=user.username))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == user.username, "'username' does not match"
