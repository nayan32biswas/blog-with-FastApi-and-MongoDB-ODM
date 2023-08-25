from datetime import datetime
from typing import List, Optional

from mongodb_odm import (
    ASCENDING,
    BaseModel,
    Document,
    Field,
    IndexModel,
    ODMObjectId,
    Relationship,
)

from app.user.models import User


class Topic(Document):
    user_id: Optional[ODMObjectId] = None
    name: str = Field(max_length=127)
    description: Optional[str] = Field(default=None)

    class Config(Document.Config):
        indexes = [
            IndexModel([("name", ASCENDING)], unique=True),
        ]


class Post(Document):
    author_id: ODMObjectId = Field(...)

    title: str = Field(max_length=255)
    slug: str = Field(max_length=300)
    short_description: Optional[str] = Field(max_length=512, default=None)
    cover_image: Optional[str] = None
    description: Optional[str] = None
    total_comment: int = Field(default=0)
    total_reaction: int = Field(default=0)

    publish_at: Optional[datetime] = None

    topic_ids: List[ODMObjectId] = []

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    author: Optional[User] = Relationship(local_field="author_id")

    class Config(Document.Config):
        indexes = [
            IndexModel([("slug", ASCENDING)], unique=True),
            IndexModel([("author", ASCENDING)]),
            IndexModel([("topics", ASCENDING)]),
        ]


class EmbeddedReply(BaseModel):
    id: ODMObjectId = Field(default_factory=ODMObjectId)
    user_id: ODMObjectId = Field(...)
    description: str = Field(...)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Comment(Document):
    user_id: ODMObjectId = Field(...)
    post_id: ODMObjectId = Field(...)

    replies: List[EmbeddedReply] = []
    description: str = Field(...)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    post: Optional[Post] = Relationship(local_field="post_id")
    user: Optional[User] = Relationship(local_field="user_id")

    class Config(Document.Config):
        collection_name = "comment"
        indexes = [
            IndexModel([("post_id", ASCENDING)]),
        ]


class Reaction(Document):
    post_id: ODMObjectId = Field(...)
    user_ids: List[ODMObjectId] = []

    post: Optional[Post] = Relationship(local_field="post_id")

    class Config(Document.Config):
        collection_name = "reaction"
        indexes = [
            IndexModel([("post_id", ASCENDING)]),
        ]
