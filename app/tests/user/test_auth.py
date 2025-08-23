from fastapi import status
from httpx import AsyncClient

from app.tests.endpoints import Endpoints
from app.tests.user.helper import (
    NEW_FULL_NAME,
    NEW_PASS,
    NEW_USERNAME,
    create_new_user,
)
from app.user.models import User
from app.user.services.token import TokenService


async def test_registration_and_auth(async_client: AsyncClient) -> None:
    _ = await User.adelete_many({"username": NEW_USERNAME})

    response = await async_client.post(
        Endpoints.REGISTRATION,
        json={
            "username": NEW_USERNAME,
            "password": NEW_PASS,
            "full_name": NEW_FULL_NAME,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED

    response = await async_client.post(
        Endpoints.TOKEN, json={"username": NEW_USERNAME, "password": NEW_PASS}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["access_token"]

    _ = await User.adelete_many({"username": NEW_USERNAME})


async def test_duplicate_registration(async_client: AsyncClient) -> None:
    _ = await User.adelete_many({"username": NEW_USERNAME})

    response = await async_client.post(
        Endpoints.REGISTRATION,
        json={
            "username": NEW_USERNAME,
            "password": NEW_PASS,
            "full_name": NEW_FULL_NAME,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED

    response = await async_client.post(
        Endpoints.REGISTRATION,
        json={
            "username": NEW_USERNAME,
            "password": NEW_PASS,
            "full_name": NEW_FULL_NAME,
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    _ = await User.adelete_many({"username": NEW_USERNAME})


async def test_update_access_token(async_client: AsyncClient) -> None:
    user = await create_new_user()
    refresh_token = TokenService.create_refresh_token_from_user(user)

    response = await async_client.post(
        Endpoints.UPDATE_ACCESS_TOKEN,
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == status.HTTP_200_OK


async def test_logout_from_all_device(async_client: AsyncClient) -> None:
    user = await create_new_user()
    access_token = TokenService.create_access_token_from_user(user)
    refresh_token = TokenService.create_refresh_token_from_user(user)

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    response = await async_client.get(Endpoints.ME, headers=headers)
    assert response.status_code == status.HTTP_200_OK

    response = await async_client.put(
        Endpoints.LOGOUT_FROM_ALL_DEVICES, headers=headers
    )
    assert response.status_code == status.HTTP_200_OK

    response = await async_client.get(Endpoints.ME, headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = await async_client.post(
        Endpoints.UPDATE_ACCESS_TOKEN, json={"refresh_token": refresh_token}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_token_validation(async_client: AsyncClient) -> None:
    # Try to get me without token
    response = await async_client.get(Endpoints.ME)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    invalid_access_token = TokenService.create_access_token({})
    invalid_refresh_token = TokenService.create_refresh_token({})
    response = await async_client.get(
        Endpoints.ME, headers={"Authorization": f"Bearer {invalid_access_token}"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    response = await async_client.get(
        Endpoints.ME, headers={"Authorization": f"Bearer {invalid_refresh_token}"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_change_password(async_client: AsyncClient) -> None:
    user = await create_new_user()
    access_token = TokenService.create_access_token_from_user(user)

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    updated_pass = "updated-pass"

    payload = {"current_password": NEW_PASS, "new_password": updated_pass}
    response = await async_client.post(
        Endpoints.CHANGE_PASSWORD, json=payload, headers=headers
    )

    assert response.status_code == status.HTTP_200_OK

    response = await async_client.post(
        Endpoints.TOKEN,
        json={"username": NEW_USERNAME, "password": NEW_PASS},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
        "User should get error with new password"
    )

    response = await async_client.post(
        Endpoints.TOKEN,
        json={"username": NEW_USERNAME, "password": updated_pass},
    )
    assert response.status_code == status.HTTP_200_OK, (
        "User should be able to login with updated password"
    )

    _ = await User.adelete_many({"username": NEW_USERNAME})
