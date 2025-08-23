from faker import Faker
from fastapi import status
from httpx import AsyncClient

from app.tests.endpoints import Endpoints
from app.tests.post.helper import create_topic
from app.tests.utils import get_header

fake = Faker()


async def test_get_topics(async_client: AsyncClient) -> None:
    response = await async_client.get(Endpoints.TOPICS)
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.json()


async def test_get_topics_search(async_client: AsyncClient) -> None:
    search_text = "something"

    await create_topic(search_text)

    response = await async_client.get(Endpoints.TOPICS, params={"q": search_text})
    assert response.status_code == status.HTTP_200_OK


async def test_create_topics(async_client: AsyncClient) -> None:
    payload = {"name": fake.word()}

    response = await async_client.post(Endpoints.TOPICS, json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = await async_client.post(
        Endpoints.TOPICS, json=payload, headers=await get_header()
    )
    assert response.status_code == status.HTTP_201_CREATED


async def test_create_topics_multiple_time(async_client: AsyncClient) -> None:
    payload = {"name": fake.word()}

    response = await async_client.post(
        Endpoints.TOPICS, json=payload, headers=await get_header()
    )
    assert response.status_code == status.HTTP_201_CREATED

    response = await async_client.post(
        Endpoints.TOPICS, json=payload, headers=await get_header()
    )

    assert response.status_code == status.HTTP_201_CREATED
