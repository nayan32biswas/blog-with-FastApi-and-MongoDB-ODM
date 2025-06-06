from datetime import datetime

from app.user.models import User
from app.user.utils import get_password_hash

NEW_USERNAME = "username-exists"
NEW_PASS = "new-pass"
NEW_FULL_NAME = "Full Name"


def create_new_user() -> User:
    User.delete_many({"username": NEW_USERNAME})

    hash_password = get_password_hash(NEW_PASS)
    user = User(
        username=NEW_USERNAME,
        full_name=NEW_FULL_NAME,
        joining_date=datetime.now(),
        password=hash_password,
        random_str=User.new_random_str(),
    ).create()

    return user
