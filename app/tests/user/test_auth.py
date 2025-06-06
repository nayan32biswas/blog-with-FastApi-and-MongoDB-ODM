from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.tests.endpoints import Endpoints
from app.tests.user.helper import (
    NEW_FULL_NAME,
    NEW_PASS,
    NEW_USERNAME,
    create_new_user,
)
from app.user.models import User
from app.user.utils import (
    create_access_token,
    create_access_token_from_user,
    create_refresh_token,
    create_refresh_token_from_user,
)

client = TestClient(app)


def test_registration_and_auth() -> None:
    _ = User.delete_many({"username": NEW_USERNAME})

    response = client.post(
        Endpoints.REGISTRATION,
        json={
            "username": NEW_USERNAME,
            "password": NEW_PASS,
            "full_name": NEW_FULL_NAME,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED

    response = client.post(
        Endpoints.TOKEN, json={"username": NEW_USERNAME, "password": NEW_PASS}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["access_token"]

    _ = User.delete_many({"username": NEW_USERNAME})


def test_duplicate_registration() -> None:
    _ = User.delete_many({"username": NEW_USERNAME})

    response = client.post(
        Endpoints.REGISTRATION,
        json={
            "username": NEW_USERNAME,
            "password": NEW_PASS,
            "full_name": NEW_FULL_NAME,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED

    response = client.post(
        Endpoints.REGISTRATION,
        json={
            "username": NEW_USERNAME,
            "password": NEW_PASS,
            "full_name": NEW_FULL_NAME,
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    _ = User.delete_many({"username": NEW_USERNAME})


def test_update_access_token() -> None:
    user = create_new_user()
    refresh_token = create_refresh_token_from_user(user)

    response = client.post(
        Endpoints.UPDATE_ACCESS_TOKEN,
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == status.HTTP_200_OK


def test_logout_from_all_device() -> None:
    user = create_new_user()
    access_token = create_access_token_from_user(user)
    refresh_token = create_refresh_token_from_user(user)

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    response = client.get(Endpoints.ME, headers=headers)
    assert response.status_code == status.HTTP_200_OK

    response = client.put(Endpoints.LOGOUT_FROM_ALL_DEVICES, headers=headers)
    assert response.status_code == status.HTTP_200_OK

    response = client.get(Endpoints.ME, headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.post(
        Endpoints.UPDATE_ACCESS_TOKEN, json={"refresh_token": refresh_token}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_token_validation() -> None:
    # Try to get me without token
    response = client.get(Endpoints.ME)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    invalid_access_token = create_access_token({})
    invalid_refresh_token = create_refresh_token({})
    response = client.get(
        Endpoints.ME, headers={"Authorization": f"Bearer {invalid_access_token}"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    response = client.get(
        Endpoints.ME, headers={"Authorization": f"Bearer {invalid_refresh_token}"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_change_password() -> None:
    user = create_new_user()
    access_token = create_access_token_from_user(user)

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    updated_pass = "updated-pass"

    payload = {"current_password": NEW_PASS, "new_password": updated_pass}
    response = client.post(Endpoints.CHANGE_PASSWORD, json=payload, headers=headers)

    assert response.status_code == status.HTTP_200_OK

    response = client.post(
        Endpoints.TOKEN,
        json={"username": NEW_USERNAME, "password": NEW_PASS},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
        "User should get error with new password"
    )

    response = client.post(
        Endpoints.TOKEN,
        json={"username": NEW_USERNAME, "password": updated_pass},
    )
    assert response.status_code == status.HTTP_200_OK, (
        "User should be able to login with updated password"
    )

    _ = User.delete_many({"username": NEW_USERNAME})
