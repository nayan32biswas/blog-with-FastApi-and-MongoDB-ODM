import logging
from datetime import datetime
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, Depends, Query, status
from mongodb_odm import ObjectIdStr, ODMObjectId
from slugify import slugify

from app.base.exceptions import CustomException, ExType
from app.base.utils import update_partially
from app.base.utils.query import get_object_or_404
from app.base.utils.string import rand_slug_str
from app.user.dependencies import get_authenticated_user, get_authenticated_user_or_none
from app.user.models import User

from ..models import Comment, Post, Reaction, Topic
from ..schemas.posts import (
    PostCreate,
    PostDetailsOut,
    PostListOut,
    PostOut,
    PostUpdate,
    TopicIn,
    TopicOut,
)

router = APIRouter(prefix="/api/v1")
logger = logging.getLogger(__name__)


def get_or_create_topic(
    topic_name: str, user: User | None = None
) -> tuple[Topic, bool]:
    user_id = user.id if user else None
    try:
        topic = Topic.get({"name": topic_name})
        return topic, False
    except Exception:
        pass
    slug = slugify(topic_name)
    for i in range(3, 20):
        try:
            return (
                Topic(
                    name=topic_name,
                    slug=f"{slug}-{rand_slug_str(i)}",
                    user_id=user_id,
                ).create(),
                True,
            )
        except Exception:
            pass
    raise Exception("Unable to create the Topic")


@router.post("/topics", status_code=status.HTTP_201_CREATED, response_model=TopicOut)
async def create_topics(
    topic_data: TopicIn,
    user: User = Depends(get_authenticated_user),
) -> Any:
    topic, _ = get_or_create_topic(topic_name=topic_data.name, user=user)
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
) -> Any:
    filter: dict[str, Any] = {}
    if q:
        filter["$text"] = {"$search": q}
    if after:
        filter["_id"] = {"$lt": ObjectId(after)}

    sort = [("_id", -1)]

    results = []
    next_cursor = None
    topic_qs = Topic.find(filter=filter, sort=sort, limit=limit)
    for topic in topic_qs:
        next_cursor = topic.id
        results.append(TopicOut(**topic.model_dump()).model_dump())

    next_cursor = next_cursor if len(results) == limit else None

    return {"after": ObjectIdStr(next_cursor), "results": results}


def get_or_create_post_topics(topics_name: list[str], user: User) -> list[Topic]:
    topics: list[Topic] = []
    for topic_name in topics_name:
        topic, _ = get_or_create_topic(topic_name=topic_name, user=user)
        if topic:
            topics.append(topic)
    return topics


@router.post(
    "/posts",
    status_code=status.HTTP_201_CREATED,
    response_model=PostDetailsOut,
)
async def create_posts(
    post_data: PostCreate, user: User = Depends(get_authenticated_user)
) -> Any:
    short_description = post_data.short_description

    topics = get_or_create_post_topics(post_data.topics, user)

    publish_at = datetime.now() if post_data.publish_now else None

    post = Post(
        author_id=user.id,
        slug=str(ObjectId()),
        title=post_data.title,
        short_description=short_description,
        description=post_data.description,
        cover_image=post_data.cover_image,
        publish_at=publish_at,
        topic_ids=[topic.id for topic in topics],
    ).create()

    is_slug_saved = False
    slug = slugify(post.title)
    for i in range(1, 10):
        try:
            new_slug = f"{slug}-{rand_slug_str(i)}" if i > 1 else slug
            post.update(raw={"$set": {"slug": new_slug}})
            post.slug = new_slug
            is_slug_saved = True
            break
        except Exception:
            pass
    if is_slug_saved is False:
        post.delete()
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title error",
            code=ExType.VALIDATION_ERROR,
            field="title",
        )
    post.topics = topics
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
    filter: dict[str, Any] = {
        "publish_at": {"$ne": None, "$lt": datetime.now()},
    }
    if username:
        if user and user.username == username:
            filter["author_id"] = user.id
            filter.pop("publish_at")
        else:
            user = User.get({"username": username})
            filter["author_id"] = user.id
    if topics:
        topic_ids = [
            ODMObjectId(obj["_id"])
            for obj in Topic.find_raw({"slug": {"$in": topics}}, projection={"slug": 1})
        ]
        filter["topic_ids"] = {"$in": topic_ids}
    if q:
        filter["$text"] = {"$search": q}
    if after:
        filter["_id"] = {"$lt": ObjectId(after)}

    sort = [("_id", -1)]

    post_qs = Post.find(
        filter=filter,
        sort=sort,
        limit=limit,
        projection={"description": 0},
    )
    results = []
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
    filter: dict[str, Any] = {
        "slug": slug,
        # "publish_at": {"$ne": None, "$lt": datetime.now()},
    }

    try:
        post = Post.get(filter=filter)
        if post.publish_at is None or post.publish_at > datetime.now():
            if user is None or user.id != post.author_id:
                raise CustomException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    code=ExType.PERMISSION_ERROR,
                    detail="You don't have permission to get this object.",
                )
        post.author = User.get({"_id": post.author_id})
    except Exception as e:
        logger.error(f"Error getting post: {e}")
        raise CustomException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ExType.OBJECT_NOT_FOUND,
            detail="Object not found.",
        ) from e
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
    post = get_object_or_404(Post, {"slug": slug})

    if post.author_id != user.id:
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ExType.PERMISSION_ERROR,
            detail="You don't have access to update this post.",
        )

    post = update_partially(post, post_data)

    post.short_description = post_data.short_description

    if post.publish_at is None and post_data.publish_now is True:
        post.publish_at = datetime.now()
    if post.publish_at and post_data.publish_now is False:
        post.publish_at = None

    if post_data.topics:
        topics = get_or_create_post_topics(post_data.topics, user)
        post.topic_ids = [topic.id for topic in topics]
    post.update()

    return {"message": "Post Updated"}


@router.delete("/posts/{slug}", status_code=status.HTTP_200_OK)
async def delete_post(
    slug: str,
    user: User = Depends(get_authenticated_user),
) -> Any:
    post = get_object_or_404(Post, {"slug": slug})

    if post.author_id != user.id:
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ExType.PERMISSION_ERROR,
            detail="You don't have access to delete this post.",
        )
    Comment.delete_many({"post_id": post.id})
    Reaction.delete_many({"post_id": post.id})
    post.delete()

    return {"message": "Deleted"}
