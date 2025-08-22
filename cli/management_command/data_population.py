import logging
import random
import string
from datetime import datetime
from typing import Any
from uuid import uuid4

from bson import ObjectId
from faker import Faker
from mongodb_odm import InsertOne
from mongodb_odm.connection import db
from mongodb_odm.utils.apply_indexes import async_apply_indexes
from slugify import slugify

from app.base.utils.decorator import async_lru_cache, async_timing
from app.post.models import Comment, EmbeddedReply, Post, Reaction, Topic
from app.post.utils import get_post_description_from_str
from app.user.models import User
from app.user.services.auth import AuthService

fake = Faker()
log = logging.getLogger(__name__)

WRITE_OPS_LIMIT = 10000

DEFAULT_USERS = [
    {"username": "username_1", "full_name": fake.name(), "password": "password-one"},
    {"username": "username_2", "full_name": fake.name(), "password": "password-two"},
]


def rand_str(total: int = 12) -> str:
    return "".join(
        random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits)
        for _ in range(total)
    )


def get_random_range(total: int, min_item: int, max_item: int) -> tuple[int, int]:
    total -= 1
    lo = random.randint(0, total)
    hi = min(lo + random.randint(min_item, max_item), total)
    return lo, hi


def get_hash_password(_: Any) -> Any:
    return AuthService.get_password_hash(fake.password())


@async_lru_cache(maxsize=1)
async def get_user_ids() -> list[Any]:
    return [user["_id"] async for user in User.afind_raw(projection={"_id": 1})]


@async_lru_cache(maxsize=1)
async def get_topic_ids() -> list[Any]:
    return [topic["_id"] async for topic in Topic.afind_raw(projection={"_id": 1})]


@async_lru_cache(maxsize=1)
async def get_post_ids() -> list[Any]:
    return [post["_id"] async for post in Post.afind_raw(projection={"_id": 1})]


async def _create_users(total_user: Any) -> bool:
    hash_passwords: list[Any] = []
    for _ in range(10):
        hash_passwords.append(get_hash_password(0))

    write_users: list[Any] = []
    for i in range(total_user):
        write_users.append(
            InsertOne(
                User.to_mongo(
                    User(
                        username=f"i{uuid4()}",
                        full_name=fake.name(),
                        password=hash_passwords[i % len(hash_passwords)],
                        random_str=User.new_random_str(),
                        joining_date=datetime.now(),
                    )
                )
            )
        )

        if len(write_users) >= WRITE_OPS_LIMIT:
            await User.abulk_write(requests=write_users)
            write_users = []

    if write_users:
        await User.abulk_write(requests=write_users)
        write_users = []
    return True


@async_timing
async def create_users(total: int) -> None:
    for user in DEFAULT_USERS:
        if await User.aexists({"username": user["username"]}) is False:
            await User(
                username=user["username"],
                full_name=user["full_name"],
                password=AuthService.get_password_hash(user["password"]),
                random_str=User.new_random_str(),
                joining_date=datetime.now(),
            ).acreate()

    await _create_users(total - len(DEFAULT_USERS))

    log.info(f"{total} user created")


async def create_topics(total: int) -> None:
    data_set = {" ".join(fake.words(random.randint(1, 3))) for _ in range(total)}
    if await Topic.aexists() is True:
        log.info("Topic already exists")
        return

    write_topics = [
        InsertOne(
            Topic.to_mongo(Topic(name=value, slug=f"{slugify(value)}-{ObjectId()}"))
        )
        for value in data_set
    ]

    if write_topics:
        await Topic.abulk_write(requests=write_topics)

    log.info(f"{len(data_set)} topic created")


def get_post() -> dict[str, Any]:
    title = fake.sentence()
    description_str = fake.text(random.randint(1000, 10000))
    description_obj = get_post_description_from_str(description_str)
    return {
        "title": title,
        "publish_at": datetime.now(),
        "short_description": description_str[: random.randint(100, 200)],
        "description": description_obj,
        "cover_image": None,
    }


async def _create_posts(total_post: Any) -> bool:
    user_ids = await get_user_ids()
    topic_ids = [topic["_id"] async for topic in Topic.afind_raw(projection={"_id": 1})]

    random.shuffle(user_ids)
    random.shuffle(topic_ids)
    total_user, total_topic = len(user_ids), len(topic_ids)

    write_posts: list[Any] = []
    for i in range(total_post):
        topic_lo, topic_hi = get_random_range(total_topic, 5, 10)
        post_data = get_post()
        write_posts.append(
            InsertOne(
                Post.to_mongo(
                    Post(
                        **post_data,
                        slug=f"{slugify(post_data['title'])}-{ObjectId()}",
                        author_id=user_ids[i % total_user],
                        topic_ids=topic_ids[topic_lo:topic_hi],
                    )
                )
            )
        )

        if len(write_posts) >= WRITE_OPS_LIMIT:
            await Post.abulk_write(requests=write_posts)
            write_posts = []

    if write_posts:
        await Post.abulk_write(requests=write_posts)

    return True


@async_timing
async def create_posts(total: int) -> None:
    await _create_posts(total)

    log.info(f"{total} post inserted")


async def _create_reactions(total_reaction: Any) -> None:
    user_ids = await get_user_ids()
    post_ids = await get_post_ids()

    total_post, total_user = len(post_ids), len(user_ids)
    random.shuffle(post_ids)
    random.shuffle(user_ids)

    write_reactions: list[Any] = []
    for i in range(total_reaction):
        lo, hi = get_random_range(total_user, 20, 100)
        write_reactions.append(
            InsertOne(
                Reaction.to_mongo(
                    Reaction(
                        post_id=post_ids[i % total_post],
                        user_ids=user_ids[lo:hi],
                    )
                )
            )
        )

        if len(write_reactions) >= WRITE_OPS_LIMIT:
            await Reaction.abulk_write(requests=write_reactions)
            write_reactions = []

    if write_reactions:
        await Reaction.abulk_write(requests=write_reactions)
        write_reactions = []


@async_timing
async def create_reactions() -> None:
    n = await Post.acount_documents()

    await _create_reactions(n)

    log.info(f"{n} reaction inserted")


async def _create_comments(total_comment: Any) -> None:
    user_ids = await get_user_ids()
    post_ids = await get_post_ids()

    total_post, total_user = len(post_ids), len(user_ids)
    random.shuffle(post_ids)
    random.shuffle(user_ids)

    write_comments: list[Any] = []
    for i in range(total_comment):
        post_id = post_ids[i % total_post]
        total_comment = random.randint(1, random.randint(1, random.randint(1, 100)))
        for j in range(total_comment):
            replies = [
                EmbeddedReply(
                    user_id=user_ids[(i + k) % total_user], description=fake.text()
                )
                for k in range(random.randint(1, random.randint(1, 20)))
            ]
            write_comments.append(
                InsertOne(
                    Comment.to_mongo(
                        Comment(
                            user_id=user_ids[(i + j) % total_user],
                            post_id=post_id,
                            description=fake.text(),
                            replies=replies,
                        )
                    )
                )
            )
        if len(write_comments) >= WRITE_OPS_LIMIT:
            await Comment.abulk_write(requests=write_comments)
            write_comments = []

    if write_comments:
        await Comment.abulk_write(requests=write_comments)


@async_timing
async def create_comments() -> None:
    total_post = await Post.acount_documents()
    n = total_post // 3

    await _create_comments(n)

    log.info(f"{n} comment inserted")


@async_timing
async def populate_dummy_data(
    total_user: int = 100, total_post: int = 100, is_unittest: bool = False
) -> None:
    log.info("Applying indexes...")
    await async_apply_indexes()

    log.info("Inserting data...")

    await create_users(total_user)
    await create_topics(min(max(total_post // 10, 10), 100000))
    await create_posts(total_post)
    if not is_unittest:
        await create_reactions()
        await create_comments()

    log.info("Data insertion complete")


async def clean_data() -> None:
    await db().command("dropDatabase")  # type: ignore
    log.info("Database deleted")
