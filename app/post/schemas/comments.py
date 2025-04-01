from datetime import datetime

from mongodb_odm import ObjectIdStr
from pydantic import BaseModel

from app.user.schemas import PublicUserListOut


class CommentIn(BaseModel):
    description: str


class ReplyIn(BaseModel):
    description: str


class ReplyOut(BaseModel):
    id: ObjectIdStr
    user: PublicUserListOut | None = None
    description: str

    created_at: datetime
    updated_at: datetime


class CommentOut(BaseModel):
    id: ObjectIdStr
    user: PublicUserListOut | None = None

    description: str
    replies: list[ReplyOut] = []

    created_at: datetime
    updated_at: datetime
