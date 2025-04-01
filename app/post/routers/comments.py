import logging
from typing import Any, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, Query, status
from mongodb_odm import ODMObjectId, ObjectIdStr

from app.base.exceptions import CustomException, ExType
from app.base.utils.query import get_object_or_404
from app.user.dependencies import get_authenticated_user, get_authenticated_user_or_none
from app.user.models import User

from ..models import Comment, EmbeddedReply, Post
from ..schemas.comments import CommentIn, CommentOut, ReplyIn, ReplyOut

router = APIRouter(prefix="/api/v1")
logger = logging.getLogger(__name__)


def update_total_comment(post_id: Any, val: int) -> None:
    Post.update_one({"_id": ODMObjectId(post_id)}, {"$inc": {"total_comment": val}})


@router.get("/posts/{slug}/comments")
def get_comments(
    slug: str,
    limit: int = Query(default=20, le=100),
    after: Optional[ObjectIdStr] = Query(default=None),
    _: User = Depends(get_authenticated_user_or_none),
) -> Any:
    post = get_object_or_404(Post, filter={"slug": slug})
    filter = {"post_id": post.id}
    if after:
        filter["_id"] = {"$lt": ObjectId(after)}

    comment_qs = Comment.find(filter, sort=(("_id", -1),), limit=limit)
    # Load related user only
    comments = Comment.load_related(comment_qs, fields=["user"])

    user_ids = list(
        {replies.user_id for comment in comments for replies in comment.replies}
    )
    users_dict = {
        user.id: user.model_dump() for user in User.find({"_id": {"$in": user_ids}})
    }

    results = []
    next_cursor = None
    for comment in comments:
        next_cursor = comment.id
        comment_dict = comment.model_dump()
        for reply in comment_dict["replies"]:
            # Assign child replies
            reply["user"] = users_dict.get(reply["user_id"])
        results.append(CommentOut(**comment_dict).model_dump())

    next_cursor = next_cursor if len(results) == limit else None

    return {"after": ObjectIdStr(next_cursor), "results": results}


@router.post(
    "/posts/{slug}/comments",
    status_code=status.HTTP_201_CREATED,
    response_model=CommentOut,
)
async def create_comments(
    slug: str,
    comment_data: CommentIn,
    user: User = Depends(get_authenticated_user),
) -> Any:
    post = get_object_or_404(Post, filter={"slug": slug})
    comment = Comment(
        user_id=user.id,
        post_id=post.id,
        description=comment_data.description,
    ).create()
    # increase total comment for post
    update_total_comment(post.id, 1)

    comment.user = user
    return CommentOut(**comment.model_dump()).model_dump()


@router.put("/posts/{slug}/comments/{comment_id}", status_code=status.HTTP_200_OK)
async def update_comments(
    comment_id: ObjectIdStr,
    slug: str,
    comment_data: CommentIn,
    user: User = Depends(get_authenticated_user),
) -> Any:
    post = get_object_or_404(Post, filter={"slug": slug})
    comment = get_object_or_404(
        Comment,
        {
            "_id": ODMObjectId(comment_id),
            "post_id": post.id,
        },
    )
    if comment.user_id != user.id:
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ExType.PERMISSION_ERROR,
            detail="You don't have access to update this comment.",
        )

    comment.description = comment_data.description
    comment.update()

    return {"message": "Comment Updated"}


@router.delete("/posts/{slug}/comments/{comment_id}", status_code=status.HTTP_200_OK)
async def delete_comments(
    slug: str,
    comment_id: ObjectIdStr,
    user: User = Depends(get_authenticated_user),
) -> Any:
    post = get_object_or_404(Post, filter={"slug": slug})
    comment = get_object_or_404(
        Comment,
        {"_id": ODMObjectId(comment_id), "post_id": post.id},
    )
    if comment.user_id != user.id:
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ExType.PERMISSION_ERROR,
            detail="You don't have access to delete this comment.",
        )

    comment.delete()
    # decrease total comment for post
    update_total_comment(post.id, -1)

    return {"message": "Deleted"}


@router.post(
    "/posts/{slug}/comments/{comment_id}/replies",
    status_code=status.HTTP_201_CREATED,
    response_model=ReplyOut,
)
async def create_replies(
    slug: str,
    comment_id: ObjectIdStr,
    reply_data: ReplyIn,
    user: User = Depends(get_authenticated_user),
) -> Any:
    post = get_object_or_404(Post, filter={"slug": slug})
    comment = get_object_or_404(
        Comment,
        {
            "_id": ODMObjectId(comment_id),
            "post_id": post.id,
        },
    )
    if len(comment.replies) >= 100:
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ExType.VALIDATION_ERROR,
            detail="Comment should have less then 100 comment.",
        )

    reply_dict = EmbeddedReply(
        id=ODMObjectId(), user_id=user.id, description=reply_data.description
    ).model_dump()
    comment.update(raw={"$push": {"replies": reply_dict}})

    reply_dict["user"] = user.model_dump()
    reply_out = ReplyOut(**reply_dict)

    return reply_out


@router.put(
    "/posts/{slug}/comments/{comment_id}/replies/{reply_id}",
    status_code=status.HTTP_200_OK,
)
async def update_replies(
    slug: str,
    comment_id: ObjectIdStr,
    reply_id: ObjectIdStr,
    reply_data: ReplyIn,
    user: User = Depends(get_authenticated_user),
) -> Any:
    post = get_object_or_404(Post, filter={"slug": slug})
    r_id = ODMObjectId(reply_id)
    update_comment = Comment.update_one(
        {
            "_id": ODMObjectId(comment_id),
            "post_id": post.id,
            "replies.id": r_id,
            "replies.user_id": user.id,
        },
        {"$set": {"replies.$[reply].description": reply_data.description}},
        array_filters=[{"reply.id": r_id}],
    )

    if update_comment.modified_count != 1:
        raise CustomException(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ExType.PERMISSION_ERROR,
            detail="You don't have permission to update this replies",
        )
    return {"message": "Updated"}


@router.delete(
    "/posts/{slug}/comments/{comment_id}/replies/{reply_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_replies(
    slug: str,
    comment_id: ObjectIdStr,
    reply_id: ObjectIdStr,
    user: User = Depends(get_authenticated_user),
) -> Any:
    post = get_object_or_404(Post, filter={"slug": slug})
    r_id = ODMObjectId(reply_id)
    update_comment = Comment.update_one(
        {
            "_id": ODMObjectId(comment_id),
            "post_id": post.id,
            "replies": {
                "$elemMatch": {
                    "id": r_id,
                    "user_id": user.id,
                }
            },
        },
        {
            "$pull": {
                "replies": {
                    "id": r_id,
                    "user_id": user.id,
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

    return {"message": "Deleted"}
