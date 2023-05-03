import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from mongodb_odm import ODMObjectId

from app.base.custom_types import ObjectIdStr
from app.base.utils import get_offset, update_partially
from app.base.utils.query import get_object_or_404
from app.user.dependencies import get_authenticated_user, get_authenticated_user_or_none
from app.user.models import User

from ..models import Post, Topic
from ..schemas.posts import (
    PostCreate,
    PostDetailsOut,
    PostListOut,
    PostUpdate,
    TopicIn,
    TopicOut,
)

router = APIRouter(prefix="/api/v1")
logger = logging.getLogger(__name__)


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
        filter["name"] = re.compile(q, re.IGNORECASE)

    topic_qs = Topic.find(filter=filter, limit=limit, skip=offset)
    results = [TopicOut.from_orm(topic) for topic in topic_qs]

    topic_count = Topic.count_documents(filter=filter)

    return {"count": topic_count, "results": results}


@router.post("/topics", status_code=status.HTTP_201_CREATED, response_model=TopicOut)
def create_topics(
    topic_data: TopicIn,
    user: User = Depends(get_authenticated_user),
) -> Any:
    name = topic_data.name.lower()

    topic, created = Topic.get_or_create({"name": name})
    if created:
        topic.user_id = user.id
        topic.update()

    return TopicOut.from_orm(topic)


@router.get("/posts", status_code=status.HTTP_200_OK)
def get_posts(
    page: int = 1,
    limit: int = 20,
    q: Optional[str] = Query(default=None),
    topics: List[ObjectIdStr] = Query(default=[]),
    author_id: Optional[ObjectIdStr] = Query(default=None),
    _: Optional[User] = Depends(get_authenticated_user_or_none),
) -> Dict[str, Any]:
    offset = get_offset(page, limit)
    filter: Dict[str, Any] = {
        "publish_at": {"$ne": None, "$lt": datetime.utcnow()},
    }
    if author_id:
        filter["author_id"] = ObjectId(author_id)
    if topics:
        filter["topic_ids"] = {"$in": [ODMObjectId(id) for id in topics]}
    if q:
        filter["title"] = q

    post_qs = Post.find(
        filter=filter, limit=limit, skip=offset, projection={"description": 0}
    )
    results = [PostListOut.from_orm(post).dict() for post in Post.load_related(post_qs)]

    post_count = Post.count_documents(filter=filter)

    return {"count": post_count, "results": results}


def get_short_description(description: Optional[str]) -> str:
    if description:
        return description[:200]
    return ""


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

    post = Post(
        author_id=user.id,
        title=post_data.title,
        short_description=short_description,
        description=post_data.description,
        cover_image=post_data.cover_image,
        publish_at=post_data.publish_at,
        topic_ids=[ODMObjectId(id) for id in post_data.topic_ids],
    ).create()

    post.author = user
    post.topics = [
        TopicOut.from_orm(topic) for topic in Topic.find({"_id": {"$in": post.topic_ids}})
    ]

    return PostDetailsOut.from_orm(post)


@router.get("/posts/{post_id}", status_code=status.HTTP_200_OK)
def get_post_details(
    post_id: ObjectIdStr,
    _: Optional[User] = Depends(get_authenticated_user_or_none),
) -> Any:
    filter: Dict[str, Any] = {
        "_id": ObjectId(post_id),
        "publish_at": {"$ne": None, "$lt": datetime.utcnow()},
    }
    try:
        post = Post.get(filter=filter)
        post.author = User.get({"_id": post.author_id})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Object not found."
        )
    post.topics = [
        TopicOut.from_orm(topic) for topic in Topic.find({"_id": {"$in": post.topic_ids}})
    ]

    return PostDetailsOut.from_orm(post)


@router.patch(
    "/posts/{post_id}",
    status_code=status.HTTP_200_OK,
    response_model=PostDetailsOut,
)
def update_posts(
    post_id: ObjectIdStr,
    post_data: PostUpdate,
    user: User = Depends(get_authenticated_user),
) -> Any:
    post = get_object_or_404(Post, {"_id": ObjectId(post_id)})

    if post.author_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to update this post.",
        )

    post = update_partially(post, post_data)

    post.short_description = post_data.short_description
    if not post.short_description and post_data.description:
        post.short_description = get_short_description(post_data.description)
    post.update()

    post.author = user

    return PostDetailsOut.from_orm(post)


@router.delete("/posts/{post_id}", status_code=status.HTTP_200_OK)
def delete_post(
    post_id: ObjectIdStr,
    user: User = Depends(get_authenticated_user),
) -> Any:
    post = get_object_or_404(Post, {"_id": ObjectId(post_id)})

    if post.author_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to delete this post.",
        )
    return {"message": "Deleted"}
