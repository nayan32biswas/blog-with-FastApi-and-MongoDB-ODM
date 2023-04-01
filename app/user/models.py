from datetime import datetime
from typing import Optional

from mongodb_odm import ASCENDING, Document, Field, IndexModel


class User(Document):
    username: str = Field(...)
    full_name: str = Field(...)
    image: Optional[str] = Field(default=None)

    is_active: bool = True
    joining_date: datetime
    last_login: Optional[datetime] = None

    password: Optional[str] = Field(default=None)
    # rand_str will be used to log out from all devices.
    rand_str: Optional[str] = Field(default=None, max_length=32)

    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config(Document.Config):
        collection_name = "user"
        indexes = (IndexModel([("username", ASCENDING)], unique=True),)
