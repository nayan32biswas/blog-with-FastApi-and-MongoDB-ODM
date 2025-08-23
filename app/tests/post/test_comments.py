from faker import Faker
from fastapi import status
from httpx import AsyncClient

from app.post.models import Comment, Post
from app.tests.endpoints import Endpoints
from app.tests.post.helper import (
    create_comment,
    create_public_post,
    create_reply,
)
from app.tests.utils import get_header, get_header_by_user, get_other_user, get_user

fake = Faker()


async def test_get_comments(async_client: AsyncClient) -> None:
    test_user = await get_user()
    post = await create_public_post(test_user.id)

    response = await async_client.get(Endpoints.COMMENTS.format(slug=post.slug))
    assert response.status_code == status.HTTP_200_OK


async def test_create_comment_on_any_post(
    async_client: AsyncClient,
) -> None:
    test_user = await get_user()
    post = await create_public_post(test_user.id)

    # Comment on others post valid action
    post = await Post.aget_random_one({"author_id": {"$ne": test_user.id}})
    response = await async_client.post(
        Endpoints.COMMENTS.format(slug=post.slug),
        json={"description": "Unittest"},
        headers=await get_header(),
    )
    assert response.status_code == status.HTTP_201_CREATED


async def test_update_comment(async_client: AsyncClient) -> None:
    test_user = await get_user()
    post = await create_public_post(test_user.id)
    comment = await create_comment(test_user.id, post.id)

    updated_text = "Updated Text"

    response = await async_client.put(
        Endpoints.COMMENTS_DETAIL.format(slug=post.slug, comment_id=comment.id),
        json={"description": updated_text},
        headers=await get_header(),
    )
    assert response.status_code == status.HTTP_200_OK

    updated_comment = await Comment.afind_one({"_id": comment.id})
    assert updated_comment and updated_comment.description == updated_text

    # Try to update others comment should get 403
    other_user = await get_other_user(test_user)

    response = await async_client.put(
        Endpoints.COMMENTS_DETAIL.format(slug=post.slug, comment_id=comment.id),
        json={"description": fake.text()},
        headers=get_header_by_user(other_user),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_delete_comment(async_client: AsyncClient) -> None:
    test_user = await get_user()
    post = await create_public_post(test_user.id)
    comment = await create_comment(test_user.id, post.id)

    response = await async_client.delete(
        Endpoints.COMMENTS_DETAIL.format(slug=post.slug, comment_id=comment.id),
        headers=await get_header(),
    )
    assert response.status_code == status.HTTP_200_OK

    # Try to delete others comment should get 403
    other_user = await get_other_user(test_user)
    comment = await create_comment(other_user.id, post.id)

    response = await async_client.delete(
        Endpoints.COMMENTS_DETAIL.format(slug=post.slug, comment_id=comment.id),
        headers=await get_header(),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_create_replies(async_client: AsyncClient) -> None:
    test_user = await get_user()
    post = await create_public_post(test_user.id)
    comment = await create_comment(test_user.id, post.id)

    response = await async_client.post(
        Endpoints.REPLIES.format(slug=post.slug, comment_id=comment.id),
        json={"description": fake.text()},
        headers=await get_header(),
    )
    assert response.status_code == status.HTTP_201_CREATED

    # Reply on others comment
    other_user = await get_other_user(test_user)
    other_comment = await create_comment(other_user.id, post.id)

    response = await async_client.post(
        Endpoints.REPLIES.format(slug=post.slug, comment_id=other_comment.id),
        json={"description": fake.text()},
        headers=await get_header(),
    )
    assert response.status_code == status.HTTP_201_CREATED


async def test_update_replies(async_client: AsyncClient) -> None:
    test_user = await get_user()
    post = await create_public_post(test_user.id)
    comment = await create_comment(test_user.id, post.id)
    reply = await create_reply(test_user.id, comment, description=fake.text())

    response = await async_client.put(
        Endpoints.REPLIES_DETAIL.format(
            slug=post.slug, comment_id=comment.id, reply_id=reply.id
        ),
        json={"description": fake.text()},
        headers=await get_header(),
    )
    assert response.status_code == status.HTTP_200_OK

    # Try to update others replies. Should get 403
    other_user = await get_other_user(test_user)

    response = await async_client.put(
        Endpoints.REPLIES_DETAIL.format(
            slug=post.slug, comment_id=comment.id, reply_id=reply.id
        ),
        json={"description": fake.text()},
        headers=get_header_by_user(other_user),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_delete_replies(async_client: AsyncClient) -> None:
    test_user = await get_user()
    post = await create_public_post(test_user.id)
    comment = await create_comment(test_user.id, post.id)
    reply = await create_reply(test_user.id, comment, description=fake.text())

    response = await async_client.delete(
        Endpoints.REPLIES_DETAIL.format(
            slug=post.slug, comment_id=comment.id, reply_id=reply.id
        ),
        headers=await get_header(),
    )
    assert response.status_code == status.HTTP_200_OK

    # Try to delete others replies. Should get 403
    other_user = await get_other_user(test_user)
    reply = await create_reply(other_user.id, comment, description=fake.text())

    response = await async_client.delete(
        Endpoints.REPLIES_DETAIL.format(
            slug=post.slug, comment_id=comment.id, reply_id=reply.id
        ),
        headers=await get_header(),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
