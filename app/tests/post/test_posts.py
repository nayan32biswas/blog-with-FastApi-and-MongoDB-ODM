from faker import Faker
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.post.models import Post, Topic
from app.tests.endpoints import Endpoints
from app.tests.post.helper import get_post_description, get_published_filter
from app.tests.utils import get_header, get_user

client = TestClient(app)
fake = Faker()


def test_get_posts() -> None:
    response = client.get(Endpoints.POSTS)
    assert response.status_code == status.HTTP_200_OK

    assert "results" in response.json()

    # Get posts with valid credentials
    response = client.get(Endpoints.POSTS, headers=get_header())
    assert response.status_code == status.HTTP_200_OK

    user = get_user()
    topic = Topic.get({})
    response = client.get(
        Endpoints.POSTS,
        params={"q": "abc", "topics": [str(topic.id)], "author_id": str(user.id)},
    )
    assert response.status_code == status.HTTP_200_OK


def test_get_user_posts() -> None:
    user = get_user()
    response = client.get(f"{Endpoints.POSTS}?username={user.username}")
    assert response.status_code == status.HTTP_200_OK

    assert "results" in response.json()


def test_get_user_own_posts() -> None:
    user = get_user()
    response = client.get(
        f"{Endpoints.POSTS}?username={user.username}", headers=get_header()
    )
    assert response.status_code == status.HTTP_200_OK

    assert "results" in response.json()


def test_create_posts() -> None:
    payload = {
        "title": fake.sentence(),
        "publish_now": True,
        "short_description": None,
        "description": get_post_description(),
        "cover_image": None,
        "topics": [],
    }

    response = client.post(Endpoints.POSTS, json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.post(Endpoints.POSTS, json=payload, headers=get_header())
    assert response.status_code == status.HTTP_201_CREATED


def test_get_post_details() -> None:
    post = Post.get(get_published_filter())
    response = client.get(Endpoints.POSTS_DETAIL.format(slug=post.slug))
    assert response.status_code == status.HTTP_200_OK


def test_update_post() -> None:
    user = get_user()
    post = Post.get({"author_id": user.id})

    payload = {
        "title": fake.sentence(),
        "publish_now": True,
        "short_description": None,
        "cover_image": None,
    }
    response = client.patch(Endpoints.POSTS_DETAIL.format(slug=post.slug), json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Try to update others post
    post = Post.get({"author_id": {"$ne": user.id}})
    response = client.patch(
        Endpoints.POSTS_DETAIL.format(slug=post.slug),
        json={
            "title": fake.sentence(),
            "short_description": "",
            "publish_now": True,
        },
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_post() -> None:
    user = get_user()
    post = Post.get({"author_id": user.id})
    response = client.delete(
        Endpoints.POSTS_DETAIL.format(slug=post.slug), headers=get_header()
    )
    assert response.status_code == status.HTTP_200_OK

    # Try to delete others post
    post = Post.get({"author_id": {"$ne": user.id}})
    response = client.delete(
        Endpoints.POSTS_DETAIL.format(slug=post.slug), headers=get_header()
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Post.exists({"slug": post.slug}) is True, "Post was not deleted"
