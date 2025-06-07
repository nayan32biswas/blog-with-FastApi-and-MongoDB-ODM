import logging
from typing import Any

from mongodb_odm import ODMObjectId

from app.post.models import Post, Reaction

logger = logging.getLogger(__name__)


def update_total_reaction(post_id: Any, val: int) -> None:
    Post.update_one({"_id": ODMObjectId(post_id)}, {"$inc": {"total_reaction": val}})


def create_reaction(post_id: ODMObjectId, user_id: ODMObjectId) -> bool:
    update_result = Reaction.update_one(
        {"post_id": post_id, "$where": "this.user_ids.length < 100"},
        {"$addToSet": {"user_ids": user_id}},
        upsert=True,
    )

    if update_result.upserted_id is not None:
        pass
        # Insert new one
        # update_result.matched_count and update_result.modified_count should be zero
    if update_result.modified_count or update_result.upserted_id is not None:
        # increase total comment for post
        update_total_reaction(post_id, 1)
        return True

    return False


def delete_reaction(post_id: ODMObjectId, user_id: ODMObjectId) -> bool:
    update_result = Reaction.update_one(
        {"post_id": post_id, "user_ids": user_id},
        {"$pull": {"user_ids": user_id}},
    )

    if update_result.modified_count:
        # decrease total comment for post
        update_total_reaction(post_id, -1)
        return True

    return False
