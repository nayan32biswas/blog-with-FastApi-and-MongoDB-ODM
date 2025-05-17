from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.user.models import User
from app.user.utils import create_access_token, create_refresh_token

from .config import get_header, get_user, init_config  # noqa
from .data import users

client = TestClient(app)

NEW_USERNAME = "username-exists"
NEW_PASS = "new-pass"
NEW_FULL_NAME = "Full Name"


def test_registration_and_auth() -> None:
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
        "/api/v1/token", json={"username": NEW_USERNAME, "password": NEW_PASS}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["access_token"]

    _ = User.delete_many({"username": NEW_USERNAME})


def test_duplicate_registration() -> None:
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

    _ = User.delete_many({"username": NEW_USERNAME})


def test_update_access_token() -> None:
    response = client.post(
        "/api/v1/token",
        json={"username": users[0]["username"], "password": users[0]["password"]},
    )

    response = client.post(
        "/api/v1/update-access-token",
        json={"refresh_token": response.json()["refresh_token"]},
    )
    assert response.status_code == status.HTTP_200_OK


def test_get_me() -> None:
    response = client.get("/api/v1/users/me", headers=get_header())
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == users[0]["username"]


def test_get_user_details() -> None:
    user = get_user()
    response = client.get("/api/v1/users/details", headers=get_header())

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == user.username


def test_update_user() -> None:
    new_full_name = "New Name"
    response = client.patch(
        "/api/v1/users/update", json={"full_name": new_full_name}, headers=get_header()
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["full_name"] == new_full_name
    assert response.json()["username"] == users[0]["username"]


def test_logout_from_all_device() -> None:
    response = client.post(
        "/api/v1/token",
        json={"username": users[0]["username"], "password": users[0]["password"]},
    )
    assert response.status_code == status.HTTP_200_OK
    access_token = response.json()["access_token"]
    refresh_token = response.json()["refresh_token"]
    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK

    response = client.put("/api/v1/logout-from-all-device", headers=headers)
    assert response.status_code == status.HTTP_200_OK

    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.post(
        "/api/v1/update-access-token", json={"refresh_token": refresh_token}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_token_validation() -> None:
    # Try to get me without token
    response = client.get("/api/v1/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    invalid_access_token = create_access_token({})
    invalid_refresh_token = create_refresh_token({})
    response = client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {invalid_access_token}"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    response = client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {invalid_refresh_token}"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_change_password() -> None:
    _ = User.delete_many({"username": NEW_USERNAME})
    payload = {"current_password": "str", "new_password": "str"}

    response = client.post(
        "/api/v1/registration",
        json={
            "username": NEW_USERNAME,
            "password": NEW_PASS,
            "full_name": NEW_FULL_NAME,
        },
    )

    response = client.post(
        "/api/v1/token",
        json={"username": NEW_USERNAME, "password": NEW_PASS},
    )
    assert response.status_code == status.HTTP_200_OK

    access_token = response.json()["access_token"]
    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    updated_pass = "updated-pass"

    payload = {"current_password": NEW_PASS, "new_password": updated_pass}
    response = client.post("/api/v1/change-password", json=payload, headers=headers)

    assert response.status_code == status.HTTP_200_OK

    response = client.post(
        "/api/v1/token",
        json={"username": NEW_USERNAME, "password": NEW_PASS},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
        "User should get error with new password"
    )

    _ = User.delete_many({"username": NEW_USERNAME})


def test_user_public_profile() -> None:
    user = get_user()
    response = client.get(f"/api/v1/users/{user.username}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == user.username, "'username' does not match"
