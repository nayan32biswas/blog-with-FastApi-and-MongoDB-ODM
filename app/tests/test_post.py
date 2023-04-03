from datetime import datetime

from faker import Faker
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.post.models import Post

from .config import get_header, get_user, init_config  # noqa

client = TestClient(app)
fake = Faker()


def test_get_tags():
    response = client.get("/api/v1/tags")
    assert response.status_code == status.HTTP_200_OK

    assert "count" in response.json()
    assert "results" in response.json()


def test_create_tags():
    payload = {"name": fake.word()}

    response = client.post("/api/v1/tags", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.post("/api/v1/tags", json=payload, headers=get_header())
    assert response.status_code == status.HTTP_201_CREATED


def test_get_posts():
    response = client.get("/api/v1/posts")
    assert response.status_code == status.HTTP_200_OK

    assert "count" in response.json()
    assert "results" in response.json()


def test_create_posts():
    payload = {
        "title": fake.sentence(),
        "publish_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
        "short_description": None,
        "description": fake.text(),
        "cover_image": None,
    }

    response = client.post("/api/v1/posts", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.post("/api/v1/posts", json=payload, headers=get_header())
    assert response.status_code == status.HTTP_201_CREATED


def test_get_post_details():
    post = Post.get({})
    response = client.get(f"/api/v1/posts/{post.id}")
    assert response.status_code == status.HTTP_200_OK


def test_update_post():
    user = get_user()
    post = Post.get({"author_id": user.id})
    payload = {
        "title": fake.sentence(),
        "publish_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
        "short_description": None,
        "cover_image": None,
    }
    response = client.patch(f"/api/v1/posts/{post.id}", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Testing patch
    response = client.patch(
        f"/api/v1/posts/{post.id}", json={"title": "new"}, headers=get_header()
    )
    assert response.status_code == status.HTTP_200_OK
    assert Post.get({"_id": post.id}).title == "new"

    # Try to update others post
    post = Post.get({"author_id": {"$ne": user.id}})
    response = client.patch(
        f"/api/v1/posts/{post.id}",
        json={"title": fake.sentence()},
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_delete_post():
    user = get_user()
    post = Post.get({"author_id": user.id})
    response = client.delete(f"/api/v1/posts/{post.id}", headers=get_header())
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Try to delete other post
    post = Post.get({"author_id": {"$ne": user.id}})
    response = client.delete(f"/api/v1/posts/{post.id}", headers=get_header())
    assert response.status_code == status.HTTP_400_BAD_REQUEST
