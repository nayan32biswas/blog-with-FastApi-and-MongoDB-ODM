from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from bson import ObjectId
from faker import Faker
from mongodb_odm import ODMObjectId
from slugify import slugify

from app.post.models import Comment, EmbeddedReply, Post, Topic
from app.post.utils import get_post_description_from_str

fake = Faker()

TEST_POST_TITLE = "Test Post"


def get_published_filter() -> dict[str, Any]:
    return {"publish_at": {"$ne": None, "$lte": datetime.now()}}


def get_post_description() -> dict[Any, Any]:
    return get_post_description_from_str(fake.text())


def create_topic(name: str) -> Topic:
    topic = Topic(
        name=name,
        slug=f"test-{uuid4()}",
        description=None,
    ).create()

    return topic


def create_public_post(author_id: ODMObjectId, title: str = TEST_POST_TITLE) -> Post:
    description = "Description"
    short_description = "Short Description"
    description_obj = get_post_description_from_str(description)
    slug = f"{slugify(title)}-{ObjectId()}"

    post = Post(
        title=title,
        publish_at=datetime.now() - timedelta(hours=1),
        short_description=short_description,
        description=description_obj,
        cover_image=None,
        slug=slug,
        author_id=author_id,
    ).create()

    return post


def create_comment(user_id: ODMObjectId, post_id: ODMObjectId) -> Comment:
    comment = Comment(
        user_id=user_id,
        post_id=post_id,
        description="Description",
    ).create()

    return comment


def create_reply(
    user_id: ODMObjectId, comment: Comment, description: str
) -> EmbeddedReply:
    reply = EmbeddedReply(
        id=ODMObjectId(),
        user_id=user_id,
        description=description,
    )
    comment.update(raw={"$push": {"replies": reply.model_dump()}})

    return reply
