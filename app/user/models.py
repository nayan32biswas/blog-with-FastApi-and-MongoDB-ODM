from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from mongodb_odm import ASCENDING, Document, Field, IndexModel
from pydantic import BaseModel


class UserLinkType(StrEnum):
    GITHUB = "GITHUB"
    TWITTER = "TWITTER"
    LINKEDIN = "LINKEDIN"
    INSTAGRAM = "INSTAGRAM"
    FACEBOOK = "FACEBOOK"
    YOUTUBE = "YOUTUBE"
    DISCORD = "DISCORD"
    TELEGRAM = "TELEGRAM"
    WEBSITE = "WEBSITE"
    OTHER = "OTHER"


class EmbeddedUserLinks(BaseModel):
    type: UserLinkType
    link: str
    is_public: bool = False


class User(Document):
    username: str = Field(...)
    email: str | None = Field(default=None)
    full_name: str = Field(...)
    image: str | None = Field(default=None)

    is_active: bool = True
    joining_date: datetime
    last_login: datetime | None = None

    password: str | None = Field(default=None)
    # random_str will be used to log out from all devices.
    random_str: str | None = Field(default=None, max_length=64)
    bio: str | None = Field(default=None)
    address: str | None = Field(default=None)
    user_links: list[EmbeddedUserLinks] = Field(default_factory=list)

    updated_at: datetime = Field(default_factory=datetime.now)

    class ODMConfig(Document.ODMConfig):
        collection_name = "user"
        indexes = [
            IndexModel([("username", ASCENDING)], unique=True),
        ]

    @classmethod
    def new_random_str(cls) -> str:
        return str(uuid4())
