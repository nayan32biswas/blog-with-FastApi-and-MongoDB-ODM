from typing import Any

from faker import Faker
from fastapi import status
from httpx import AsyncClient

from app.post.models import Post, Topic
from app.tests.endpoints import Endpoints
from app.tests.post.helper import get_post_description, get_published_filter
from app.tests.utils import get_header, get_user

fake = Faker()


async def test_get_posts(async_client: AsyncClient) -> None:
    test_user = await get_user()
    response = await async_client.get(Endpoints.POSTS)
    assert response.status_code == status.HTTP_200_OK

    assert "results" in response.json()

    # Get posts with valid credentials
    response = await async_client.get(Endpoints.POSTS, headers=await get_header())
    assert response.status_code == status.HTTP_200_OK

    topic = await Topic.aget({})
    response = await async_client.get(
        Endpoints.POSTS,
        params={"q": "abc", "topics": [str(topic.id)], "author_id": str(test_user.id)},
    )
    assert response.status_code == status.HTTP_200_OK


async def test_get_user_posts(async_client: AsyncClient) -> None:
    test_user = await get_user()
    response = await async_client.get(
        f"{Endpoints.POSTS}?username={test_user.username}", headers=await get_header()
    )
    assert response.status_code == status.HTTP_200_OK

    assert "results" in response.json()


async def test_get_user_own_posts(async_client: AsyncClient) -> None:
    test_user = await get_user()
    response = await async_client.get(
        f"{Endpoints.POSTS}?username={test_user.username}", headers=await get_header()
    )
    assert response.status_code == status.HTTP_200_OK

    assert "results" in response.json()


async def test_create_posts(async_client: AsyncClient) -> None:
    payload: Any = {
        "title": fake.sentence(),
        "publish_now": True,
        "short_description": None,
        "description": get_post_description(),
        "cover_image": None,
        "topics": [],
    }

    response = await async_client.post(Endpoints.POSTS, json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = await async_client.post(
        Endpoints.POSTS, json=payload, headers=await get_header()
    )
    assert response.status_code == status.HTTP_201_CREATED


async def test_get_post_details(async_client: AsyncClient) -> None:
    post = await Post.aget(get_published_filter())
    response = await async_client.get(Endpoints.POSTS_DETAIL.format(slug=post.slug))
    assert response.status_code == status.HTTP_200_OK


async def test_update_post(async_client: AsyncClient) -> None:
    test_user = await get_user()
    post = await Post.aget({"author_id": test_user.id})

    payload: Any = {
        "title": fake.sentence(),
        "publish_now": True,
        "short_description": None,
        "cover_image": None,
    }
    response = await async_client.patch(
        Endpoints.POSTS_DETAIL.format(slug=post.slug), json=payload
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Try to update others post
    post = await Post.aget({"author_id": {"$ne": test_user.id}})
    response = await async_client.patch(
        Endpoints.POSTS_DETAIL.format(slug=post.slug),
        json={
            "title": fake.sentence(),
            "short_description": "",
            "publish_now": True,
        },
        headers=await get_header(),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_delete_post(async_client: AsyncClient) -> None:
    test_user = await get_user()
    post = await Post.aget({"author_id": test_user.id})
    response = await async_client.delete(
        Endpoints.POSTS_DETAIL.format(slug=post.slug), headers=await get_header()
    )
    assert response.status_code == status.HTTP_200_OK

    # Try to delete others post
    post = await Post.aget({"author_id": {"$ne": test_user.id}})
    response = await async_client.delete(
        Endpoints.POSTS_DETAIL.format(slug=post.slug), headers=await get_header()
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert await Post.aexists({"slug": post.slug}) is True, "Post was not deleted"
