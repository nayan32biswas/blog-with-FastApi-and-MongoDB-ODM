import logging
from collections.abc import Iterator
from typing import Any

from fastapi import status
from mongodb_odm import ODMObjectId

from app.base.exceptions import CustomException, ExType
from app.base.utils.query import get_object_or_404
from app.post.models import Comment, EmbeddedReply, Post
from app.post.schemas.comments import CommentOut
from app.user.models import User

logger = logging.getLogger(__name__)


def update_total_comment(post_id: Any, val: int) -> None:
    Post.update_one({"_id": ODMObjectId(post_id)}, {"$inc": {"total_comment": val}})


def get_comments(
    post_id: ODMObjectId,
    limit: int,
    after: str | ODMObjectId | None = None,
) -> Iterator[Comment]:
    filter: dict[str, Any] = {"post_id": post_id}

    if after:
        filter["_id"] = {"$lt": ODMObjectId(after)}

    comment_qs = Comment.find(filter, sort=(("_id", -1),), limit=limit)

    return comment_qs


def load_comments_with_details(
    comment_qs: Iterator[Comment],
) -> tuple[ODMObjectId | None, list[dict[str, Any]]]:
    comments = Comment.load_related(comment_qs, fields=["user"])

    user_ids = list(
        {replies.user_id for comment in comments for replies in comment.replies}
    )
    users_dict = {
        user.id: user.model_dump() for user in User.find({"_id": {"$in": user_ids}})
    }

    results: list[dict[str, Any]] = []
    next_cursor = None

    for comment in comments:
        next_cursor = comment.id
        comment_dict = comment.model_dump()

        for reply in comment_dict["replies"]:
            # Assign child replies
            reply["user"] = users_dict.get(reply["user_id"])

        results.append(CommentOut(**comment_dict).model_dump())

    return next_cursor, results


def create_comment(
    user_id: ODMObjectId,
    post_id: ODMObjectId,
    description: str,
) -> Comment:
    comment = Comment(
        user_id=user_id,
        post_id=post_id,
        description=description,
    ).create()

    update_total_comment(post_id, 1)

    return comment


def get_comment_details_or_404(
    comment_id: ODMObjectId,
    post_id: ODMObjectId | None = None,
) -> Comment:
    filter: dict[str, Any] = {"_id": comment_id}
    if post_id:
        filter["post_id"] = post_id

    comment: Comment = get_object_or_404(Comment, filter)

    return comment


def update_comment(
    comment_id: ODMObjectId | str,
    user_id: ODMObjectId,
    post_id: ODMObjectId | None,
    description: str,
) -> Comment:
    comment = get_comment_details_or_404(ODMObjectId(comment_id), post_id)

    if comment.user_id != user_id:
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ExType.PERMISSION_ERROR,
            detail="You don't have access to update this comment.",
        )

    comment.description = description
    comment.update()

    return comment


def delete_comment(
    comment_id: ODMObjectId | str, user_id: ODMObjectId, post_id: ODMObjectId
) -> None:
    comment = get_comment_details_or_404(ODMObjectId(comment_id), post_id)

    if comment.user_id != user_id:
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ExType.PERMISSION_ERROR,
            detail="You don't have access to delete this comment.",
        )

    comment.delete()
    update_total_comment(post_id, -1)


def create_reply(
    comment_id: ODMObjectId | str, user_id: ODMObjectId, description: str
) -> EmbeddedReply:
    comment = get_comment_details_or_404(ODMObjectId(comment_id))

    if len(comment.replies) >= 100:
        # Limit the number of replies to 100 for a single comment
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ExType.VALIDATION_ERROR,
            detail="Comment should have less then 100 replies.",
        )

    reply = EmbeddedReply(id=ODMObjectId(), user_id=user_id, description=description)
    comment.update(raw={"$push": {"replies": reply.model_dump()}})

    return reply


def update_reply(
    comment_id: ODMObjectId | str,
    reply_id: ODMObjectId | str,
    user_id: ODMObjectId,
    description: str,
) -> bool:
    reply_id = ODMObjectId(reply_id)

    update_comment = Comment.update_one(
        {
            "_id": ODMObjectId(comment_id),
            "replies.id": reply_id,
            "replies.user_id": user_id,
        },
        {"$set": {"replies.$[reply].description": description}},
        array_filters=[{"reply.id": reply_id}],
    )

    if update_comment.modified_count != 1:
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ExType.PERMISSION_ERROR,
            detail="You don't have permission to update this replies",
        )

    return True


def delete_reply(
    comment_id: ODMObjectId | str,
    reply_id: ODMObjectId | str,
    user_id: ODMObjectId,
) -> bool:
    reply_id = ODMObjectId(reply_id)

    update_comment = Comment.update_one(
        {
            "_id": ODMObjectId(comment_id),
            "replies": {
                "$elemMatch": {
                    "id": reply_id,
                    "user_id": user_id,
                }
            },
        },
        {
            "$pull": {
                "replies": {
                    "id": reply_id,
                    "user_id": user_id,
                },
            }
        },
    )

    if update_comment.modified_count != 1:
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ExType.PERMISSION_ERROR,
            detail="You don't have permission to delete this replies",
        )

    return True
