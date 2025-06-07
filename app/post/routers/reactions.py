import logging
from typing import Any

from fastapi import APIRouter, Depends, status
from mongodb_odm import ODMObjectId

from app.post.models import Post
from app.post.services import post as post_service
from app.post.services import reaction as reaction_service
from app.user.dependencies import get_authenticated_user
from app.user.models import User

router = APIRouter(prefix="/api/v1")
logger = logging.getLogger(__name__)


def update_total_reaction(post_id: Any, val: int) -> None:
    Post.update_one({"_id": ODMObjectId(post_id)}, {"$inc": {"total_reaction": val}})


@router.post("/posts/{slug}/reactions", status_code=status.HTTP_201_CREATED)
async def create_reactions(
    slug: str,
    user: User = Depends(get_authenticated_user),
) -> Any:
    post = post_service.get_post_details_or_404(slug, user.id)

    is_added = reaction_service.create_reaction(post_id=post.id, user_id=user.id)

    if is_added:
        message = "Reaction Added"
    else:
        message = "You already have a reaction on this post"

    return {"message": message}


@router.delete("/posts/{slug}/reactions", status_code=status.HTTP_200_OK)
async def delete_post_reactions(
    slug: str,
    user: User = Depends(get_authenticated_user),
) -> Any:
    post = post_service.get_post_details_or_404(slug, user.id)

    is_deleted = reaction_service.delete_reaction(post_id=post.id, user_id=user.id)

    if not is_deleted:
        message = "You don't have a reaction on this post"
    else:
        message = "Reaction Deleted"

    return {"message": message}
