import logging
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, Depends, status

from app.base.custom_types import ObjectIdStr
from app.base.utils.query import get_object_or_404
from app.user.dependencies import get_authenticated_user
from app.user.models import User

from ..models import Post, Reaction

router = APIRouter(prefix="/api/v1")
logger = logging.getLogger(__name__)


@router.post("/posts/{post_id}/reactions", status_code=status.HTTP_200_OK)
def create_reactions(
    post_id: ObjectIdStr,
    user: User = Depends(get_authenticated_user),
) -> Any:
    post = get_object_or_404(Post, {"_id": ObjectId(post_id)})
    update_result = Reaction.update_one(
        {"post_id": post.id, "$where": "this.user_ids.length < 100"},
        {"$addToSet": {"user_ids": user.id}},
        upsert=True,
    )
    if update_result.upserted_id is not None:
        pass
        # Insert new one
        # update_result.matched_count and update_result.modified_count should be zero
    return {"message": "Reaction Added"}


@router.delete("/posts/{post_id}/reactions", status_code=status.HTTP_200_OK)
def delete_post_reactions(
    post_id: ObjectIdStr,
    user: User = Depends(get_authenticated_user),
) -> Any:
    post = get_object_or_404(Post, {"_id": ObjectId(post_id)})
    Reaction.update_one(
        {"post_id": post.id, "user_ids": {"$in": [user.id]}},
        {"$pull": {"user_ids": user.id}},
    )
    return {"message": "Reaction Deleted"}
