from datetime import datetime
from typing import Tuple

from faker import Faker
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.post.models import Comment, EmbeddedReply, Post, Reaction, Tag
from app.user.models import User

from .config import get_header, get_user, init_config  # noqa

client = TestClient(app)
fake = Faker()


def test_get_tags() -> None:
    response = client.get("/api/v1/tags")
    assert response.status_code == status.HTTP_200_OK

    assert "count" in response.json()
    assert "results" in response.json()

    response = client.get("/api/v1/tags", params={"q": "abc"})
    assert response.status_code == status.HTTP_200_OK


def test_create_tags() -> None:
    payload = {"name": fake.word()}

    response = client.post("/api/v1/tags", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.post("/api/v1/tags", json=payload, headers=get_header())
    assert response.status_code == status.HTTP_201_CREATED


def test_get_posts() -> None:
    response = client.get("/api/v1/posts")
    assert response.status_code == status.HTTP_200_OK

    assert "count" in response.json()
    assert "results" in response.json()

    # Get posts with valid credentials
    response = client.get("/api/v1/posts", headers=get_header())
    assert response.status_code == status.HTTP_200_OK

    user = get_user()
    tag = Tag.get({})
    response = client.get(
        "/api/v1/posts",
        params={"q": "abc", "tags": [str(tag.id)], "author_id": str(user.id)},
    )
    assert response.status_code == status.HTTP_200_OK


def test_create_posts() -> None:
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


def test_get_post_details() -> None:
    post = Post.get({})
    response = client.get(f"/api/v1/posts/{post.id}")
    assert response.status_code == status.HTTP_200_OK


def test_update_post() -> None:
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
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_post() -> None:
    user = get_user()
    post = Post.get({"author_id": user.id})
    response = client.delete(f"/api/v1/posts/{post.id}", headers=get_header())
    assert response.status_code == status.HTTP_200_OK

    # Try to delete others post
    post = Post.get({"author_id": {"$ne": user.id}})
    response = client.delete(f"/api/v1/posts/{post.id}", headers=get_header())
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_comments() -> None:
    post = Post.get({})

    response = client.get(f"/api/v1/posts/{post.id}/comments")
    assert response.status_code == status.HTTP_200_OK


def test_create_comment_on_any_post() -> None:
    user = get_user()
    post = Post.get_random_one({"author_id": user.id})
    response = client.post(
        f"/api/v1/posts/{post.id}/comments",
        json={"description": fake.text()},
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_201_CREATED

    # Comment on others post valid action
    post = Post.get_random_one({"author_id": {"$ne": user.id}})
    response = client.post(
        f"/api/v1/posts/{post.id}/comments",
        json={"description": fake.text()},
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_update_comment() -> None:
    user = get_user()
    comment = Comment.get_random_one({"user_id": user.id})
    response = client.put(
        f"/api/v1/posts/{comment.post_id}/comments/{comment.id}",
        json={"description": fake.text()},
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_200_OK

    # Try to update others comment should get 403
    comment = Comment.get_random_one({"user_id": {"$ne": user.id}})
    response = client.put(
        f"/api/v1/posts/{comment.post_id}/comments/{comment.id}",
        json={"description": fake.text()},
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_comment() -> None:
    user = get_user()
    comment = Comment.get_random_one({"user_id": user.id})
    response = client.delete(
        f"/api/v1/posts/{comment.post_id}/comments/{comment.id}", headers=get_header()
    )
    assert response.status_code == status.HTTP_200_OK

    # Try to delete others comment should get 403
    comment = Comment.get_random_one({"user_id": {"$ne": user.id}})
    response = client.delete(
        f"/api/v1/posts/{comment.post_id}/comments/{comment.id}", headers=get_header()
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_replies() -> None:
    user = get_user()
    comment = Comment.get_random_one({"user_id": user.id})
    response = client.post(
        f"/api/v1/posts/{comment.post_id}/comments/{comment.id}/replies",
        json={"description": fake.text()},
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_201_CREATED

    # Reply on others comment
    comment = Comment.get_random_one({"user_id": {"$ne": user.id}})
    response = client.post(
        f"/api/v1/posts/{comment.post_id}/comments/{comment.id}/replies",
        json={"description": fake.text()},
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_201_CREATED


def get_my_reply(user: User) -> Tuple[Comment, EmbeddedReply]:
    comment = Comment.get({"replies.user_id": user.id})
    reply: EmbeddedReply
    for reply in comment.replies:
        if reply.user_id == user.id:
            reply = reply
            return comment, reply
    raise Exception("Reply not found")


def get_others_reply(user: User) -> Tuple[Comment, EmbeddedReply]:
    comment = Comment.get({"replies.user_id": {"$ne": user.id}})
    reply: EmbeddedReply
    for reply in comment.replies:
        if reply.user_id != user.id:
            reply = reply
            return comment, reply
    raise Exception("Reply not found")


def test_update_replies() -> None:
    user = get_user()
    comment, reply = get_my_reply(user)
    response = client.put(
        f"/api/v1/posts/{comment.post_id}/comments/{comment.id}/replies/{reply.id}",
        json={"description": fake.text()},
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_200_OK

    # Try to update others replies. Should get 403
    comment, reply = get_others_reply(user)
    response = client.put(
        f"/api/v1/posts/{comment.post_id}/comments/{comment.id}/replies/{reply.id}",
        json={"description": fake.text()},
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_replies() -> None:
    user = get_user()
    comment, reply = get_my_reply(user)
    response = client.delete(
        f"/api/v1/posts/{comment.post_id}/comments/{comment.id}/replies/{reply.id}",
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_200_OK

    # Try to delete others replies. Should get 403
    comment, reply = get_others_reply(user)
    response = client.delete(
        f"/api/v1/posts/{comment.post_id}/comments/{comment.id}/replies/{reply.id}",
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_reactions() -> None:
    user = get_user()
    post = Post.get({})
    response = client.post(f"/api/v1/posts/{post.id}/reactions", headers=get_header())
    assert response.status_code == status.HTTP_200_OK
    assert Reaction.exists({"post_id": post.id, "user_ids": {"$in": [user.id]}}) is True

    # Delete reaction
    response = client.delete(f"/api/v1/posts/{post.id}/reactions", headers=get_header())
    assert response.status_code == status.HTTP_200_OK
    assert (
        Reaction.exists({"post_id": post.id, "user_ids": {"$in": [user.id]}}) is False
    )


def test_reactions_auth() -> None:
    post = Post.get({})
    response = client.post(f"/api/v1/posts/{post.id}/reactions")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.delete(f"/api/v1/posts/{post.id}/reactions")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
