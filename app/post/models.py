from datetime import datetime
from typing import Any

from mongodb_odm import (
    ASCENDING,
    BaseModel,
    Document,
    Field,
    IndexModel,
    ODMObjectId,
    Relationship,
)
from pymongo import TEXT

from app.user.models import User


class Topic(Document):
    user_id: ODMObjectId | None = None
    name: str = Field(max_length=127)
    slug: str = Field(...)
    description: str | None = Field(default=None)

    class ODMConfig(Document.ODMConfig):
        indexes = [
            IndexModel([("slug", ASCENDING)], unique=True),
            IndexModel([("name", TEXT)]),
        ]


class Post(Document):
    author_id: ODMObjectId = Field(...)

    title: str = Field(max_length=255)
    slug: str = Field(max_length=300)
    short_description: str | None = Field(max_length=512, default=None)
    cover_image: str | None = None
    description: dict[Any, Any] | None = None
    total_comment: int = Field(default=0)
    total_reaction: int = Field(default=0)

    publish_at: datetime | None = None

    topic_ids: list[ODMObjectId] = []

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    author: User | None = Relationship(local_field="author_id")

    class ODMConfig(Document.ODMConfig):
        indexes = [
            IndexModel([("slug", ASCENDING)], unique=True),
            IndexModel([("author", ASCENDING)]),
            IndexModel([("topics", ASCENDING)]),
            IndexModel([("title", TEXT), ("short_description", TEXT)]),
        ]


class EmbeddedReply(BaseModel):
    id: ODMObjectId = Field(default_factory=ODMObjectId)
    user_id: ODMObjectId = Field(...)
    description: str = Field(...)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Comment(Document):
    user_id: ODMObjectId = Field(...)
    post_id: ODMObjectId = Field(...)

    replies: list[EmbeddedReply] = []
    description: str = Field(...)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    post: Post | None = Relationship(local_field="post_id")
    user: User | None = Relationship(local_field="user_id")

    class ODMConfig(Document.ODMConfig):
        collection_name = "comment"
        indexes = [
            IndexModel([("post_id", ASCENDING)]),
        ]


class Reaction(Document):
    post_id: ODMObjectId = Field(...)
    user_ids: list[ODMObjectId] = []

    post: Post | None = Relationship(local_field="post_id")

    class ODMConfig(Document.ODMConfig):
        collection_name = "reaction"
        indexes = [
            IndexModel([("post_id", ASCENDING)]),
        ]
