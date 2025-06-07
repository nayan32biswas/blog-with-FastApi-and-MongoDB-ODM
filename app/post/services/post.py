import logging
from collections.abc import Iterator
from datetime import datetime
from typing import Any

from fastapi import status
from mongodb_odm import ODMObjectId
from slugify import slugify

from app.base.exceptions import CustomException, ExType, ObjectNotFoundException
from app.base.utils import update_partially
from app.base.utils.query import get_object_or_404
from app.base.utils.string import rand_slug_str
from app.post.models import Comment, Post, Reaction, Topic
from app.post.schemas.posts import PostUpdate
from app.user.models import User

logger = logging.getLogger(__name__)


def get_or_create_topic(
    topic_name: str, user_id: ODMObjectId | None = None
) -> tuple[Topic, bool]:
    topic = Topic.find_one({"name": topic_name})
    if topic:
        return topic, False

    slug = slugify(topic_name)

    for i in range(1, 20):
        try:
            topic = Topic(
                name=topic_name,
                slug=f"{slug}-{rand_slug_str(i)}",
                user_id=user_id,
            ).create()

            return topic, False
        except Exception:
            logger.info(
                f"Failed to create topic with name '{topic_name}'. Attempt {i}."
            )

    raise Exception("Unable to create the Topic")


def get_or_create_post_topics(topics_name: list[str], user: User) -> list[Topic]:
    topics: list[Topic] = []

    for topic_name in topics_name:
        topic, _ = get_or_create_topic(topic_name=topic_name, user_id=user.id)
        if topic:
            topics.append(topic)

    return topics


def get_topics(
    limit: int,
    after: str | ODMObjectId | None = None,
    q: str | None = None,
) -> Iterator[Topic]:
    filter: dict[str, Any] = {}

    if q:
        filter["$text"] = {"$search": q}
    if after:
        filter["_id"] = {"$lt": ODMObjectId(after)}

    sort = [("_id", -1)]

    return Topic.find(filter=filter, sort=sort, limit=limit)


def set_post_slug(post: Post) -> Post:
    slug = slugify(post.title)
    for i in range(1, 10):
        try:
            new_slug = f"{slug}-{rand_slug_str(i)}" if i > 1 else slug
            post.update(raw={"$set": {"slug": new_slug}})
            post.slug = new_slug

            return post
        except Exception:
            logger.info(
                f"Failed to set slug for post {post.id} with title '{post.title}'. \
                      Attempt {i}."
            )

    post.delete()

    raise CustomException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Title error",
        code=ExType.VALIDATION_ERROR,
        field="title",
    )


def create_post(
    user: User,
    title: str,
    topics: list[str],
    short_description: str | None = None,
    publish_now: bool | None = None,
    description: dict[str, Any] | None = None,
    cover_image: str | None = None,
) -> Post:
    topic_objects = get_or_create_post_topics(topics, user)

    publish_at = datetime.now() if publish_now else None

    post = Post(
        author_id=user.id,
        slug=str(ODMObjectId()),
        title=title,
        short_description=short_description,
        description=description,
        cover_image=cover_image,
        publish_at=publish_at,
        topic_ids=[topic.id for topic in topic_objects],
    ).create()

    post = set_post_slug(post)
    post.topics = topic_objects

    return post


def get_posts(
    limit: int,
    after: str | ODMObjectId | None = None,
    q: str | None = None,
    topics: list[str] | None = None,
    username: str | None = None,
    user: User | None = None,
) -> Iterator[Post]:
    filter: dict[str, Any] = {
        "publish_at": {"$ne": None, "$lt": datetime.now()},
    }

    if username:
        if user and user.username == username:
            filter["author_id"] = user.id
            filter.pop("publish_at")
        else:
            user = User.get({"username": username})
            filter["author_id"] = user.id

    if topics:
        topic_ids = [
            ODMObjectId(obj["_id"])
            for obj in Topic.find_raw({"slug": {"$in": topics}}, projection={"slug": 1})
        ]
        filter["topic_ids"] = {"$in": topic_ids}
    if q:
        filter["$text"] = {"$search": q}
    if after:
        filter["_id"] = {"$lt": ODMObjectId(after)}

    sort = [("_id", -1)]

    post_qs = Post.find(
        filter=filter,
        sort=sort,
        limit=limit,
        projection={"description": 0},
    )

    return post_qs


def get_post_details_or_404(slug: str, user_id: ODMObjectId | None = None) -> Post:
    filter: dict[str, Any] = {
        "slug": slug,
        # "publish_at": {"$ne": None, "$lt": datetime.now()},
    }

    post: Post = get_object_or_404(Post, filter=filter)

    if post.publish_at is None or post.publish_at > datetime.now():
        if user_id is None or user_id != post.author_id:
            logger.warning(
                f"User={user_id} trying to access unauthorized post={post.id}"
            )
            raise ObjectNotFoundException()

    return post


def update_post(user: User, post: Post, post_data: PostUpdate) -> Post:
    post = update_partially(post, post_data)

    post.short_description = post_data.short_description

    if post.publish_at is None and post_data.publish_now is True:
        post.publish_at = datetime.now()
    if post.publish_at and post_data.publish_now is False:
        post.publish_at = None

    if post_data.topics:
        topics = get_or_create_post_topics(post_data.topics, user)
        post.topic_ids = [topic.id for topic in topics]

    post.update()

    return post


def delete_post(post: Post) -> None:
    Comment.delete_many({"post_id": post.id})
    Reaction.delete_many({"post_id": post.id})

    post.delete()
