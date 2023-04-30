from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.base.custom_types import ObjectIdStr
from app.user.schemas import PublicUserListOut


class TopicIn(BaseModel):
    name: str = Field(max_length=127)

    class Config:
        orm_mode = True


class TopicOut(BaseModel):
    id: ObjectIdStr
    name: str

    class Config:
        orm_mode = True


class PostListOut(BaseModel):
    id: ObjectIdStr
    author: Optional[PublicUserListOut]
    title: str = Field(max_length=255)
    short_description: Optional[str] = Field(max_length=512, default=None)
    cover_image: Optional[str] = None

    publish_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class PostCreate(BaseModel):
    title: str = Field(max_length=255)
    short_description: Optional[str] = Field(max_length=512, default=None)
    cover_image: Optional[str] = None

    publish_at: Optional[datetime] = None

    description: Optional[str] = None
    topic_ids: List[ObjectIdStr] = []

    class Config:
        orm_mode = True


class PostUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)
    short_description: Optional[str] = Field(default=None, max_length=512)
    cover_image: Optional[str] = None

    publish_at: Optional[datetime] = None

    description: Optional[str] = None
    topic_ids: List[ObjectIdStr] = []

    class Config:
        orm_mode = True


class PostDetailsOut(BaseModel):
    id: ObjectIdStr
    author: Optional[PublicUserListOut] = None
    title: str = Field(max_length=255)
    short_description: Optional[str] = Field(max_length=512, default=None)
    cover_image: Optional[str] = None

    publish_at: Optional[datetime] = None

    description: Optional[str] = None
    topics: List[TopicOut] = []

    class Config:
        orm_mode = True
