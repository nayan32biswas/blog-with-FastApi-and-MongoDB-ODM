import logging
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from mongodb_odm import ObjectIdStr

from app.base.exceptions import CustomException, ExType
from app.post.models import Post, Topic
from app.post.schemas.posts import (
    PostCreate,
    PostDetailsOut,
    PostListOut,
    PostOut,
    PostUpdate,
    TopicIn,
    TopicOut,
)
from app.post.services import post as post_service
from app.user.dependencies import get_authenticated_user, get_authenticated_user_or_none
from app.user.models import User

router = APIRouter(prefix="/api/v1")
logger = logging.getLogger(__name__)


@router.post("/topics", status_code=status.HTTP_201_CREATED, response_model=TopicOut)
async def create_topics(
    topic_data: TopicIn,
    user: User = Depends(get_authenticated_user),
) -> Any:
    topic, _ = post_service.get_or_create_topic(
        topic_name=topic_data.name, user_id=user.id
    )
    if not topic:
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ExType.VALIDATION_ERROR,
            field="topics",
            detail="Invalid Topic name",
        )

    return TopicOut(**topic.model_dump())


@router.get("/topics", status_code=status.HTTP_200_OK)
async def get_topics(
    limit: int = Query(default=20, le=100),
    after: ObjectIdStr | None = Query(default=None),
    q: str | None = Query(default=None),
    _: User | None = Depends(get_authenticated_user_or_none),
) -> dict[str, Any]:
    topic_qs = post_service.get_topics(
        limit=limit,
        after=after,
        q=q,
    )

    results: list[dict[str, Any]] = []
    next_cursor = None

    for topic in topic_qs:
        next_cursor = topic.id
        results.append(TopicOut(**topic.model_dump()).model_dump())

    next_cursor = next_cursor if len(results) == limit else None

    return {"after": ObjectIdStr(next_cursor), "results": results}


@router.post(
    "/posts",
    status_code=status.HTTP_201_CREATED,
    response_model=PostDetailsOut,
)
async def create_posts(
    post_data: PostCreate, user: User = Depends(get_authenticated_user)
) -> Any:
    post = post_service.create_post(
        user,
        title=post_data.title,
        topics=post_data.topics,
        publish_now=post_data.publish_now,
        short_description=post_data.short_description,
        description=post_data.description,
        cover_image=post_data.cover_image,
    )

    return PostOut(**post.model_dump()).model_dump()


@router.get("/posts", status_code=status.HTTP_200_OK)
async def get_posts(
    limit: int = Query(default=20, le=100),
    after: ObjectIdStr | None = Query(default=None),
    q: str | None = Query(default=None),
    topics: list[str] = Query(default=[]),
    username: str | None = Query(default=None),
    user: User | None = Depends(get_authenticated_user_or_none),
) -> dict[str, Any]:
    post_qs = post_service.get_posts(
        limit=limit,
        after=after,
        topics=topics,
        q=q,
        username=username,
        user=user,
    )

    results: list[dict[str, Any]] = []
    next_cursor = None

    for post in Post.load_related(post_qs):
        next_cursor = post.id
        results.append(PostListOut(**post.model_dump()).model_dump())

    next_cursor = next_cursor if len(results) == limit else None

    return {"after": ObjectIdStr(next_cursor), "results": results}


@router.get("/posts/{slug}", status_code=status.HTTP_200_OK)
async def get_post_details(
    slug: str,
    user: User | None = Depends(get_authenticated_user_or_none),
) -> Any:
    user_id = user.id if user else None
    post = post_service.get_post_details_or_404(slug, user_id)

    post.author = User.find_one({"_id": post.author_id})
    post.topics = [
        TopicOut(**topic.model_dump())
        for topic in Topic.find({"_id": {"$in": post.topic_ids}})
    ]

    return PostDetailsOut(**post.model_dump()).model_dump()


@router.patch("/posts/{slug}", status_code=status.HTTP_200_OK)
async def update_posts(
    slug: str,
    post_data: PostUpdate,
    user: User = Depends(get_authenticated_user),
) -> Any:
    post = post_service.get_post_details_or_404(slug, user.id)

    if post.author_id != user.id:
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ExType.PERMISSION_ERROR,
            detail="You don't have access to update this post.",
        )

    post = post_service.update_post(user, post, post_data)

    return {"message": "Post Updated"}


@router.delete("/posts/{slug}", status_code=status.HTTP_200_OK)
async def delete_post(
    slug: str,
    user: User = Depends(get_authenticated_user),
) -> Any:
    post = post_service.get_post_details_or_404(slug, user.id)

    if post.author_id != user.id:
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ExType.PERMISSION_ERROR,
            detail="You don't have access to delete this post.",
        )

    post_service.delete_post(post)

    return {"message": "Deleted"}
