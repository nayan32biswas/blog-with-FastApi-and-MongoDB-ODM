import logging
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from mongodb_odm import ObjectIdStr

from app.post.schemas.comments import CommentIn, CommentOut, ReplyIn, ReplyOut
from app.post.services import comment as comment_service
from app.post.services import post as post_service
from app.user.dependencies import get_authenticated_user, get_authenticated_user_or_none
from app.user.models import User

router = APIRouter(prefix="/api/v1")
logger = logging.getLogger(__name__)


@router.get("/posts/{slug}/comments")
def get_comments(
    slug: str,
    limit: int = Query(default=20, le=100),
    after: ObjectIdStr | None = Query(default=None),
    user: User | None = Depends(get_authenticated_user_or_none),
) -> Any:
    user_id = user.id if user else None
    post = post_service.get_post_details_or_404(slug, user_id)

    comment_qs = comment_service.get_comments(post.id, limit, after)
    next_cursor, results = comment_service.load_comments_with_details(comment_qs)

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
    post = post_service.get_post_details_or_404(slug, user.id)

    comment = comment_service.create_comment(post.id, user.id, comment_data.description)

    comment.user = user
    return CommentOut(**comment.model_dump()).model_dump()


@router.put("/posts/{slug}/comments/{comment_id}", status_code=status.HTTP_200_OK)
async def update_comments(
    comment_id: ObjectIdStr,
    slug: str,
    comment_data: CommentIn,
    user: User = Depends(get_authenticated_user),
) -> Any:
    post = post_service.get_post_details_or_404(slug, user.id)

    _ = comment_service.update_comment(
        comment_id=comment_id,
        post_id=post.id,
        user_id=user.id,
        description=comment_data.description,
    )

    return {"message": "Comment Updated"}


@router.delete("/posts/{slug}/comments/{comment_id}", status_code=status.HTTP_200_OK)
async def delete_comments(
    slug: str,
    comment_id: ObjectIdStr,
    user: User = Depends(get_authenticated_user),
) -> Any:
    post = post_service.get_post_details_or_404(slug, user.id)

    comment_service.delete_comment(
        comment_id=comment_id,
        post_id=post.id,
        user_id=user.id,
    )

    return {"message": "Deleted"}


@router.post(
    "/posts/{slug}/comments/{comment_id}/replies",
    status_code=status.HTTP_201_CREATED,
    response_model=ReplyOut,
)
async def create_replies(
    comment_id: ObjectIdStr,
    reply_data: ReplyIn,
    user: User = Depends(get_authenticated_user),
) -> Any:
    reply = comment_service.create_reply(
        comment_id=comment_id,
        user_id=user.id,
        description=reply_data.description,
    )

    reply_dict = reply.model_dump()

    reply_dict["user"] = user.model_dump()
    reply_out = ReplyOut(**reply_dict)

    return reply_out


@router.put(
    "/posts/{slug}/comments/{comment_id}/replies/{reply_id}",
    status_code=status.HTTP_200_OK,
)
async def update_replies(
    comment_id: ObjectIdStr,
    reply_id: ObjectIdStr,
    reply_data: ReplyIn,
    user: User = Depends(get_authenticated_user),
) -> Any:
    comment_service.update_reply(
        comment_id=comment_id,
        reply_id=reply_id,
        user_id=user.id,
        description=reply_data.description,
    )

    return {"message": "Updated"}


@router.delete(
    "/posts/{slug}/comments/{comment_id}/replies/{reply_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_replies(
    comment_id: ObjectIdStr,
    reply_id: ObjectIdStr,
    user: User = Depends(get_authenticated_user),
) -> Any:
    comment_service.delete_reply(
        comment_id=comment_id,
        reply_id=reply_id,
        user_id=user.id,
    )

    return {"message": "Deleted"}
