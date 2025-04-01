from pydantic import BaseModel, Field


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


class UserIn(BaseModel):
    full_name: str | None = Field(default=None)
    image: str | None = Field(default=None)


class UserOut(BaseModel):
    username: str = Field(...)
    full_name: str = Field(...)
    image: str | None = Field(default=None)

    is_active: bool = True


class PublicUserListOut(BaseModel):
    username: str = Field(...)
    full_name: str = Field(...)
    image: str | None = Field(default=None)


class PublicUserProfile(BaseModel):
    username: str = Field(...)
    full_name: str = Field(...)
    image: str | None = Field(default=None)
