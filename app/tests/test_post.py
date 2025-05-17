from datetime import datetime, timedelta
from typing import Any

from faker import Faker
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.post.models import Comment, EmbeddedReply, Post, Reaction, Topic
from app.post.utils import get_post_description_from_str
from app.user.models import User

from .config import get_header, get_user, init_config  # noqa

client = TestClient(app)
fake = Faker()


def get_published_filter() -> dict[str, Any]:
    return {"publish_at": {"$ne": None, "$lte": datetime.now()}}


def get_post_description() -> dict[Any, Any]:
    return get_post_description_from_str(fake.text())


def test_get_topics() -> None:
    response = client.get("/api/v1/topics")
    assert response.status_code == status.HTTP_200_OK

    assert "results" in response.json()

    response = client.get("/api/v1/topics", params={"q": "abc"})
    assert response.status_code == status.HTTP_200_OK


def test_create_topics() -> None:
    payload = {"name": fake.word()}

    response = client.post("/api/v1/topics", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.post("/api/v1/topics", json=payload, headers=get_header())
    assert response.status_code == status.HTTP_201_CREATED


def test_get_posts() -> None:
    response = client.get("/api/v1/posts")
    assert response.status_code == status.HTTP_200_OK

    assert "results" in response.json()

    # Get posts with valid credentials
    response = client.get("/api/v1/posts", headers=get_header())
    assert response.status_code == status.HTTP_200_OK

    user = get_user()
    topic = Topic.get({})
    response = client.get(
        "/api/v1/posts",
        params={"q": "abc", "topics": [str(topic.id)], "author_id": str(user.id)},
    )
    assert response.status_code == status.HTTP_200_OK


def test_get_user_posts() -> None:
    user = get_user()
    response = client.get(f"/api/v1/posts?username={user.username}")
    assert response.status_code == status.HTTP_200_OK

    assert "results" in response.json()


def test_get_user_own_posts() -> None:
    user = get_user()
    response = client.get(
        f"/api/v1/posts?username={user.username}", headers=get_header()
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

    response = client.post("/api/v1/posts", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.post("/api/v1/posts", json=payload, headers=get_header())
    assert response.status_code == status.HTTP_201_CREATED


def test_get_post_details() -> None:
    post = Post.get(get_published_filter())
    response = client.get(f"/api/v1/posts/{post.slug}")
    assert response.status_code == status.HTTP_200_OK


def test_update_post() -> None:
    user = get_user()
    post = Post.get({"author_id": user.id})

    published_at = (datetime.now() - timedelta(seconds=5)).strftime("%Y-%m-%dT%H:%M:%S")
    payload = {
        "title": fake.sentence(),
        "publish_at": published_at,
        "short_description": None,
        "cover_image": None,
    }
    response = client.patch(f"/api/v1/posts/{post.slug}", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Try to update others post
    post = Post.get({"author_id": {"$ne": user.id}})
    response = client.patch(
        f"/api/v1/posts/{post.slug}",
        json={
            "title": fake.sentence(),
            "short_description": "",
            "published_at": published_at,
        },
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_post() -> None:
    user = get_user()
    post = Post.get({"author_id": user.id})
    response = client.delete(f"/api/v1/posts/{post.slug}", headers=get_header())
    assert response.status_code == status.HTTP_200_OK

    # Try to delete others post
    post = Post.get({"author_id": {"$ne": user.id}})
    response = client.delete(f"/api/v1/posts/{post.slug}", headers=get_header())
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Post.exists({"slug": post.slug}) is True, "Post was not deleted"


def test_get_comments() -> None:
    post = Post.get({})

    response = client.get(f"/api/v1/posts/{post.slug}/comments")
    assert response.status_code == status.HTTP_200_OK


def get_other_user(current_user: User) -> User:
    return User.get_random_one({"_id": {"$ne": current_user.id}})


def test_create_comment_on_any_post() -> None:
    user = get_user()

    post = Post.get_random_one({"author_id": user.id, **get_published_filter()})
    response = client.post(
        f"/api/v1/posts/{post.slug}/comments",
        json={"description": fake.text()},
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_201_CREATED

    # Comment on others post valid action
    post = Post.get_random_one({"author_id": {"$ne": user.id}})
    response = client.post(
        f"/api/v1/posts/{post.slug}/comments",
        json={"description": fake.text()},
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_update_comment() -> None:
    user = get_user()
    comment = Comment.get_random_one({"user_id": user.id})
    post = Post.get({"_id": comment.post_id})
    response = client.put(
        f"/api/v1/posts/{post.slug}/comments/{comment.id}",
        json={"description": fake.text()},
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_200_OK

    # Try to update others comment should get 403
    comment = Comment.get_random_one({"user_id": {"$ne": user.id}})
    post = Post.get({"_id": comment.post_id})
    response = client.put(
        f"/api/v1/posts/{post.slug}/comments/{comment.id}",
        json={"description": fake.text()},
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_comment() -> None:
    user = get_user()
    comment = Comment.get_random_one({"user_id": user.id})
    post = Post.get({"_id": comment.post_id})
    response = client.delete(
        f"/api/v1/posts/{post.slug}/comments/{comment.id}", headers=get_header()
    )
    assert response.status_code == status.HTTP_200_OK

    # Try to delete others comment should get 403
    comment = Comment.get_random_one({"user_id": {"$ne": user.id}})
    post = Post.get({"_id": comment.post_id})
    response = client.delete(
        f"/api/v1/posts/{post.slug}/comments/{comment.id}", headers=get_header()
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_replies() -> None:
    user = get_user()
    comment = Comment.get_random_one({"user_id": user.id})
    post = Post.get({"_id": comment.post_id})
    response = client.post(
        f"/api/v1/posts/{post.slug}/comments/{comment.id}/replies",
        json={"description": fake.text()},
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_201_CREATED

    # Reply on others comment
    comment = Comment.get_random_one({"user_id": {"$ne": user.id}})
    post = Post.get({"_id": comment.post_id})
    response = client.post(
        f"/api/v1/posts/{post.slug}/comments/{comment.id}/replies",
        json={"description": fake.text()},
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_201_CREATED


def get_my_reply(user: User) -> tuple[Comment, EmbeddedReply]:
    comment = Comment.get({"replies.user_id": user.id})
    reply: EmbeddedReply
    for reply in comment.replies:
        if reply.user_id == user.id:
            reply = reply
            return comment, reply
    raise Exception("Reply not found")


def get_others_reply(user: User) -> tuple[Comment, EmbeddedReply]:
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
    post = Post.get({"_id": comment.post_id})
    response = client.put(
        f"/api/v1/posts/{post.slug}/comments/{comment.id}/replies/{reply.id}",
        json={"description": fake.text()},
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_200_OK

    # Try to update others replies. Should get 403
    comment, reply = get_others_reply(user)
    post = Post.get({"_id": comment.post_id})
    response = client.put(
        f"/api/v1/posts/{post.slug}/comments/{comment.id}/replies/{reply.id}",
        json={"description": fake.text()},
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_replies() -> None:
    user = get_user()
    comment, reply = get_my_reply(user)
    post = Post.get({"_id": comment.post_id})
    response = client.delete(
        f"/api/v1/posts/{post.slug}/comments/{comment.id}/replies/{reply.id}",
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_200_OK

    # Try to delete others replies. Should get 403
    comment, reply = get_others_reply(user)
    post = Post.get({"_id": comment.post_id})
    response = client.delete(
        f"/api/v1/posts/{post.slug}/comments/{comment.id}/replies/{reply.id}",
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_reactions() -> None:
    user = get_user()
    post = Post.get(get_published_filter())
    response = client.post(f"/api/v1/posts/{post.slug}/reactions", headers=get_header())
    assert response.status_code == status.HTTP_201_CREATED
    assert Reaction.exists({"post_id": post.id, "user_ids": user.id}) is True

    # Delete reaction
    response = client.delete(
        f"/api/v1/posts/{post.slug}/reactions", headers=get_header()
    )
    assert response.status_code == status.HTTP_200_OK
    assert Reaction.exists({"post_id": post.id, "user_ids": user.id}) is False


def test_reactions_auth() -> None:
    post = Post.get({})
    response = client.post(f"/api/v1/posts/{post.slug}/reactions")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.delete(f"/api/v1/posts/{post.slug}/reactions")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
