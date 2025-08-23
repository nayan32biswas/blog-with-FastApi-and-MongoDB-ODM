from fastapi import status
from httpx import AsyncClient

from app.tests.endpoints import Endpoints
from app.tests.utils import get_header, get_user
from cli.management_command.data_population import DEFAULT_USERS


async def test_get_me(async_client: AsyncClient) -> None:
    response = await async_client.get(Endpoints.ME, headers=await get_header())
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == DEFAULT_USERS[0]["username"]


async def test_get_user_details(async_client: AsyncClient) -> None:
    test_user = await get_user()
    response = await async_client.get(
        Endpoints.USER_PROFILE, headers=await get_header()
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == test_user.username


async def test_update_user(async_client: AsyncClient) -> None:
    new_full_name = "New Name"
    response = await async_client.patch(
        Endpoints.USER_UPDATE,
        json={"full_name": new_full_name},
        headers=await get_header(),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["full_name"] == new_full_name
    assert response.json()["username"] == DEFAULT_USERS[0]["username"]


async def test_user_public_profile(async_client: AsyncClient) -> None:
    test_user = await get_user()
    response = await async_client.get(
        Endpoints.PUBLIC_PROFILE.format(username=test_user.username)
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == test_user.username, (
        "'username' does not match"
    )
