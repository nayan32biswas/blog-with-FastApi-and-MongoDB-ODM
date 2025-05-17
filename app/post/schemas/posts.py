from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.user.schemas import PublicUserListOut


class TopicIn(BaseModel):
    name: str = Field(max_length=127)


class TopicOut(BaseModel):
    name: str
    slug: str


class PostCreate(BaseModel):
    title: str = Field(max_length=255)
    short_description: str | None = Field(max_length=255)
    cover_image: str | None = None

    publish_now: bool | None = None

    description: dict[Any, Any] | None = None
    topics: list[str] = []


class PostUpdate(BaseModel):
    title: str | None = Field(max_length=255)
    short_description: str | None = Field(max_length=255)
    cover_image: str | None = None
    publish_now: bool | None = None
    description: dict[Any, Any] | None = None
    topics: list[str] = []


class PostOut(BaseModel):
    title: str = Field(max_length=255)
    slug: str = Field(max_length=300)
    short_description: str | None = Field(default=None)
    cover_image: str | None = None

    publish_at: datetime | None = None
    topics: list[TopicOut] = []


class PostListOut(BaseModel):
    author: PublicUserListOut | None = None
    title: str = Field(max_length=255)
    slug: str = Field(max_length=300)
    short_description: str | None = Field(default=None)
    cover_image: str | None = None
    total_comment: int = Field(default=0)
    total_reaction: int = Field(default=0)

    publish_at: datetime | None = None


class PostDetailsOut(BaseModel):
    author: PublicUserListOut | None = None
    slug: str = Field(max_length=300)
    title: str = Field(max_length=255)
    short_description: str | None = Field(default=None)
    cover_image: str | None = None
    total_comment: int = Field(default=0)
    total_reaction: int = Field(default=0)

    publish_at: datetime | None = None

    description: dict[Any, Any] | None = None
    topics: list[TopicOut] = []
