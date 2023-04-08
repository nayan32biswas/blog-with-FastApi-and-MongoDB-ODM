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

from ..models import Post, Tag
from ..schemas.posts import (
    PostCreate,
    PostDetailsOut,
    PostListOut,
    PostUpdate,
    TagIn,
    TagOut,
)

router = APIRouter(prefix="/api/v1")
logger = logging.getLogger(__name__)


@router.get("/tags", status_code=status.HTTP_200_OK)
def get_tags(
    page: int = 1,
    limit: int = 20,
    q: Optional[str] = Query(default=None),
    _: Optional[User] = Depends(get_authenticated_user_or_none),
) -> Any:
    offset = get_offset(page, limit)
    filter: Dict[str, Any] = {}
    if q:
        filter["name"] = re.compile(q, re.IGNORECASE)

    tag_qs = Tag.find(filter=filter, limit=limit, skip=offset)
    results = [TagOut.from_orm(tag) for tag in tag_qs]

    tag_count = Tag.count_documents(filter=filter)

    return {"count": tag_count, "results": results}


@router.post("/tags", status_code=status.HTTP_201_CREATED, response_model=TagOut)
def create_tags(
    tag_data: TagIn,
    user: User = Depends(get_authenticated_user),
) -> Any:
    name = tag_data.name.lower()

    tag, created = Tag.get_or_create({"name": name})
    if created:
        tag.user_id = user.id
        tag.update()

    return TagOut.from_orm(tag)


@router.get("/posts", status_code=status.HTTP_200_OK)
def get_posts(
    page: int = 1,
    limit: int = 20,
    q: Optional[str] = Query(default=None),
    tags: List[ObjectIdStr] = Query(default=[]),
    author_id: Optional[ObjectIdStr] = Query(default=None),
    _: Optional[User] = Depends(get_authenticated_user_or_none),
) -> Dict[str, Any]:
    offset = get_offset(page, limit)
    filter: Dict[str, Any] = {
        "publish_at": {"$ne": None, "$lt": datetime.utcnow()},
    }
    if author_id:
        filter["author_id"] = ObjectId(author_id)
    if tags:
        filter["tag_ids"] = {"$in": [ODMObjectId(id) for id in tags]}
    if q:
        filter["title"] = q

    """
    posts = []
    author_ids = []
    for post in Post.find(filter=filter, limit=limit, skip=offset):
        author_ids.append(post.author_id)
        posts.append(post)
    author_dict = {obj.id: obj for obj in User.find({"_id": {"$in": author_ids}})}

    results = []
    for post in posts:
        post.author = author_dict.get(post.author_id)
        results.append(PostListOut.from_orm(post).dict())
    """

    post_qs = Post.find(filter=filter, limit=limit, skip=offset)
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
        tag_ids=[ODMObjectId(id) for id in post_data.tag_ids],
    ).create()

    post.author = user
    post.tags = [
        TagOut.from_orm(tag) for tag in Tag.find({"_id": {"$in": post.tag_ids}})
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
    post.tags = [
        TagOut.from_orm(tag) for tag in Tag.find({"_id": {"$in": post.tag_ids}})
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
