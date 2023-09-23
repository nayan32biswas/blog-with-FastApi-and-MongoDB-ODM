import logging
from typing import Any

from fastapi import APIRouter, Depends, status
from mongodb_odm import ODMObjectId

from app.base.utils.query import get_object_or_404
from app.user.dependencies import get_authenticated_user
from app.user.models import User

from ..models import Post, Reaction

router = APIRouter(prefix="/api/v1")
logger = logging.getLogger(__name__)


def update_total_reaction(post_id: Any, val: int) -> None:
    Post.update_one({"_id": ODMObjectId(post_id)}, {"$inc": {"total_reaction": val}})


@router.post("/posts/{slug}/reactions", status_code=status.HTTP_201_CREATED)
async def create_reactions(
    slug: str,
    user: User = Depends(get_authenticated_user),
) -> Any:
    post = get_object_or_404(Post, {"slug": slug})
    update_result = Reaction.update_one(
        {"post_id": post.id, "$where": "this.user_ids.length < 100"},
        {"$addToSet": {"user_ids": user.id}},
        upsert=True,
    )
    if update_result.upserted_id is not None:
        pass
        # Insert new one
        # update_result.matched_count and update_result.modified_count should be zero

    if update_result.modified_count or update_result.upserted_id is not None:
        # increase total comment for post
        update_total_reaction(post.id, 1)
        message = "Reaction Added"
    else:
        message = "You already have an reaction in this post"
    return {"message": message}


@router.delete("/posts/{slug}/reactions", status_code=status.HTTP_200_OK)
async def delete_post_reactions(
    slug: str,
    user: User = Depends(get_authenticated_user),
) -> Any:
    post = get_object_or_404(Post, {"slug": slug})
    update_result = Reaction.update_one(
        {"post_id": post.id, "user_ids": user.id},
        {"$pull": {"user_ids": user.id}},
    )
    if update_result.modified_count:
        # decrease total comment for post
        update_total_reaction(post.id, -1)

    return {"message": "Reaction Deleted"}
