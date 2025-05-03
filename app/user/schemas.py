from pydantic import BaseModel, Field

from app.user.models import EmbeddedUserLinks


class TokenData(BaseModel):
    id: str
    random_str: str


class Registration(BaseModel):
    username: str = Field(...)
    full_name: str = Field(...)
    password: str = Field(...)


class LoginIn(BaseModel):
    username: str = Field(...)
    password: str = Field(...)


class UpdateAccessTokenIn(BaseModel):
    refresh_token: str


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str


class UserOut(BaseModel):
    username: str = Field(...)
    full_name: str = Field(...)
    image: str | None = Field(default=None)

    is_active: bool = True


class UserDetailsIn(BaseModel):
    full_name: str
    email: str | None = Field(default=None)
    image: str | None = Field(default=None)
    bio: str | None = Field(default=None)
    address: str | None = Field(default=None)
    user_links: list[EmbeddedUserLinks] = Field(default_factory=list)


class UserDetailsOut(BaseModel):
    username: str = Field(...)
    full_name: str = Field(...)
    email: str | None = Field(default=None)
    image: str | None = Field(default=None)
    is_active: bool = True
    bio: str | None = Field(default=None)
    address: str | None = Field(default=None)
    user_links: list[EmbeddedUserLinks] = Field(default_factory=list)


class PublicUserListOut(BaseModel):
    username: str = Field(...)
    full_name: str = Field(...)
    image: str | None = Field(default=None)


class PublicUserProfile(BaseModel):
    username: str = Field(...)
    full_name: str = Field(...)
    image: str | None = Field(default=None)
