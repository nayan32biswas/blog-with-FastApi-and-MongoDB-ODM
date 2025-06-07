from passlib.context import CryptContext

from app.base.base_class import StaticBase
from app.user.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService(StaticBase):
    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def get_password_hash(cls, password: str) -> str:
        return pwd_context.hash(password)

    @classmethod
    def authenticate_user(cls, username: str, password: str) -> User | None:
        user = User.find_one({"username": username})

        if not user:
            return None
        if not user.password:
            return None
        if not cls.verify_password(password, user.password):
            return None

        return user
