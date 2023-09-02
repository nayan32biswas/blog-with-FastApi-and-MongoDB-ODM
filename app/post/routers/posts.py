import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, Query, status
from mongodb_odm import ODMObjectId
from slugify import slugify

from app.base.exceptions import CustomException, ExType
from app.base.utils import get_offset, update_partially
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


def create_topic(topic_name: str, user: User) -> Topic:
    topic_name = topic_name.lower()

    topic, created = Topic.get_or_create({"name": topic_name})
    if created:
        topic.update(raw={"$set": {"user_id": user.id}})
        topic.user_id = user.id
    return topic


@router.post("/topics", status_code=status.HTTP_201_CREATED, response_model=TopicOut)
def create_topics(
    topic_data: TopicIn,
    user: User = Depends(get_authenticated_user),
) -> Any:
    topic = create_topic(topic_data.name, user)
    if not topic:
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ExType.VALIDATION_ERROR,
            field="topics",
            detail="Invalid Topic name",
        )
    return TopicOut.from_orm(topic)


@router.get("/topics", status_code=status.HTTP_200_OK)
def get_topics(
    page: int = 1,
    limit: int = 20,
    q: Optional[str] = Query(default=None),
    _: Optional[User] = Depends(get_authenticated_user_or_none),
) -> Any:
    offset = get_offset(page, limit)
    filter: Dict[str, Any] = {}
    if q:
        filter["$text"] = {"$search": q}

    topic_qs = Topic.find(filter=filter, limit=limit, skip=offset)
    results = [TopicOut.from_orm(topic) for topic in topic_qs]

    topic_count = Topic.count_documents(filter=filter)

    return {"count": topic_count, "results": results}


def get_short_description(description: Optional[str]) -> str:
    if description:
        return description[:200]
    return ""


def get_or_create_post_topics(topics_name: List[str], user: User) -> List[Topic]:
    topics: List[Topic] = []
    for topic_name in topics_name:
        topic = create_topic(topic_name, user)
        if topic:
            topics.append(topic)
    return topics


@router.post(
    "/posts",
    status_code=status.HTTP_201_CREATED,
    response_model=PostDetailsOut,
)
def create_posts(
    post_data: PostCreate, user: User = Depends(get_authenticated_user)
) -> Any:
    short_description = post_data.short_description

    if not post_data.short_description:
        short_description = get_short_description(post_data.description)

    topics = get_or_create_post_topics(post_data.topics, user)

    if post_data.publish_at and post_data.publish_at < datetime.utcnow():
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please choose future date.",
            code=ExType.VALIDATION_ERROR,
            field="publish_at",
        )
    if post_data.publish_now:
        post_data.publish_at = datetime.utcnow()

    post = Post(
        author_id=user.id,
        slug=str(ObjectId()),
        title=post_data.title,
        short_description=short_description,
        description=post_data.description,
        cover_image=post_data.cover_image,
        publish_at=post_data.publish_at,
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
    return PostOut.from_orm(post).dict()


@router.get("/posts", status_code=status.HTTP_200_OK)
def get_posts(
    page: int = 1,
    limit: int = 20,
    q: Optional[str] = Query(default=None),
    topics: List[str] = Query(default=[]),
    username: Optional[str] = Query(default=None),
    user: Optional[User] = Depends(get_authenticated_user_or_none),
) -> Dict[str, Any]:
    offset = get_offset(page, limit)
    filter: Dict[str, Any] = {
        "publish_at": {"$ne": None, "$lt": datetime.utcnow()},
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

    sort = [("_id", -1)]

    post_qs = Post.find(
        filter=filter,
        sort=sort,
        limit=limit,
        skip=offset,
        projection={"description": 0},
    )
    results = [PostListOut.from_orm(post).dict() for post in Post.load_related(post_qs)]

    post_count = Post.count_documents(filter=filter)

    return {"count": post_count, "results": results}


@router.get("/posts/{slug}", status_code=status.HTTP_200_OK)
def get_post_details(
    slug: str,
    user: Optional[User] = Depends(get_authenticated_user_or_none),
) -> Any:
    filter: Dict[str, Any] = {
        "slug": slug,
        # "publish_at": {"$ne": None, "$lt": datetime.utcnow()},
    }

    try:
        post = Post.get(filter=filter)
        if post.publish_at is None or post.publish_at > datetime.utcnow():
            if user is None or user.id != post.author_id:
                raise CustomException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    code=ExType.PERMISSION_ERROR,
                    detail="You don't have permission to get this object.",
                )
        post.author = User.get({"_id": post.author_id})
    except Exception:
        raise CustomException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ExType.OBJECT_NOT_FOUND,
            detail="Object not found.",
        )
    post.topics = [
        TopicOut.from_orm(topic)
        for topic in Topic.find({"_id": {"$in": post.topic_ids}})
    ]

    return PostDetailsOut.from_orm(post).dict()


@router.patch("/posts/{slug}", status_code=status.HTTP_200_OK)
def update_posts(
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

    if post_data.publish_at and post.publish_at != post_data.publish_at:
        if post_data.publish_at < datetime.utcnow():
            raise CustomException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please choose future date.",
                code=ExType.VALIDATION_ERROR,
                field="publish_at",
            )
    if post_data.publish_now:
        post_data.publish_at = datetime.utcnow()

    post = update_partially(post, post_data)

    post.short_description = post_data.short_description
    if not post.short_description and post_data.description:
        post.short_description = get_short_description(post_data.description)

    if post_data.topics:
        topics = get_or_create_post_topics(post_data.topics, user)
        post.topic_ids = [topic.id for topic in topics]
    post.update()

    return {"message": "Post Updated"}


@router.delete("/posts/{slug}", status_code=status.HTTP_200_OK)
def delete_post(
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
