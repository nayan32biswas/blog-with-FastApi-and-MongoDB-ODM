from faker import Faker
from fastapi import status
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.post.models import Reaction
from app.tests.endpoints import Endpoints
from app.tests.post.helper import create_public_post
from app.tests.utils import get_header, get_user

client = TestClient(app)
fake = Faker()


async def test_reactions(async_client: AsyncClient) -> None:
    test_user = await get_user()
    post = await create_public_post(test_user.id)

    response = await async_client.post(
        Endpoints.REACTIONS.format(slug=post.slug), headers=await get_header()
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert (
        await Reaction.aexists({"post_id": post.id, "user_ids": test_user.id}) is True
    )

    # Delete reaction
    response = await async_client.delete(
        Endpoints.REACTIONS.format(slug=post.slug), headers=await get_header()
    )
    assert response.status_code == status.HTTP_200_OK
    assert (
        await Reaction.aexists({"post_id": post.id, "user_ids": test_user.id}) is False
    )


async def test_reactions_auth(async_client: AsyncClient) -> None:
    test_user = await get_user()
    post = await create_public_post(test_user.id)

    response = await async_client.post(Endpoints.REACTIONS.format(slug=post.slug))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = await async_client.delete(Endpoints.REACTIONS.format(slug=post.slug))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
