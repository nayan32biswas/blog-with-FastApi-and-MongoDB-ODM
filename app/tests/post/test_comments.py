from faker import Faker
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.post.models import Comment, Post
from app.tests.endpoints import Endpoints
from app.tests.post.helper import (
    create_comment,
    create_public_post,
    create_reply,
)
from app.tests.utils import get_header, get_header_by_user, get_other_user, get_user

client = TestClient(app)
fake = Faker()


def test_get_comments() -> None:
    user = get_user()
    post = create_public_post(user.id)

    response = client.get(Endpoints.COMMENTS.format(slug=post.slug))
    assert response.status_code == status.HTTP_200_OK


def test_create_comment_on_any_post() -> None:
    user = get_user()
    post = create_public_post(user.id)

    # Comment on others post valid action
    post = Post.get_random_one({"author_id": {"$ne": user.id}})
    response = client.post(
        Endpoints.COMMENTS.format(slug=post.slug),
        json={"description": "Unittest"},
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_update_comment() -> None:
    user = get_user()
    post = create_public_post(user.id)
    comment = create_comment(user.id, post.id)

    updated_text = "Updated Text"

    response = client.put(
        Endpoints.COMMENTS_DETAIL.format(slug=post.slug, comment_id=comment.id),
        json={"description": updated_text},
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_200_OK

    updated_comment = Comment.find_one({"_id": comment.id})
    assert updated_comment and updated_comment.description == updated_text

    # Try to update others comment should get 403
    other_user = get_other_user(user)

    response = client.put(
        Endpoints.COMMENTS_DETAIL.format(slug=post.slug, comment_id=comment.id),
        json={"description": fake.text()},
        headers=get_header_by_user(other_user),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_comment() -> None:
    user = get_user()
    post = create_public_post(user.id)
    comment = create_comment(user.id, post.id)

    response = client.delete(
        Endpoints.COMMENTS_DETAIL.format(slug=post.slug, comment_id=comment.id),
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_200_OK

    # Try to delete others comment should get 403
    other_user = get_other_user(user)
    comment = create_comment(other_user.id, post.id)

    response = client.delete(
        Endpoints.COMMENTS_DETAIL.format(slug=post.slug, comment_id=comment.id),
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_replies() -> None:
    user = get_user()
    post = create_public_post(user.id)
    comment = create_comment(user.id, post.id)

    response = client.post(
        Endpoints.REPLIES.format(slug=post.slug, comment_id=comment.id),
        json={"description": fake.text()},
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_201_CREATED

    # Reply on others comment
    other_user = get_other_user(user)
    other_comment = create_comment(other_user.id, post.id)

    response = client.post(
        Endpoints.REPLIES.format(slug=post.slug, comment_id=other_comment.id),
        json={"description": fake.text()},
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_update_replies() -> None:
    user = get_user()
    post = create_public_post(user.id)
    comment = create_comment(user.id, post.id)
    reply = create_reply(user.id, comment, description=fake.text())

    response = client.put(
        Endpoints.REPLIES_DETAIL.format(
            slug=post.slug, comment_id=comment.id, reply_id=reply.id
        ),
        json={"description": fake.text()},
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_200_OK

    # Try to update others replies. Should get 403
    other_user = get_other_user(user)

    response = client.put(
        Endpoints.REPLIES_DETAIL.format(
            slug=post.slug, comment_id=comment.id, reply_id=reply.id
        ),
        json={"description": fake.text()},
        headers=get_header_by_user(other_user),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_replies() -> None:
    user = get_user()
    post = create_public_post(user.id)
    comment = create_comment(user.id, post.id)
    reply = create_reply(user.id, comment, description=fake.text())

    response = client.delete(
        Endpoints.REPLIES_DETAIL.format(
            slug=post.slug, comment_id=comment.id, reply_id=reply.id
        ),
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_200_OK

    # Try to delete others replies. Should get 403
    other_user = get_other_user(user)
    reply = create_reply(other_user.id, comment, description=fake.text())

    response = client.delete(
        Endpoints.REPLIES_DETAIL.format(
            slug=post.slug, comment_id=comment.id, reply_id=reply.id
        ),
        headers=get_header(),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
