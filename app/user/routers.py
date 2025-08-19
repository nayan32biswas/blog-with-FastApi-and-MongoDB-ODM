import logging
from typing import Any

from fastapi import APIRouter, Body, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.base.exceptions import CustomException, ExType
from app.base.utils import update_partially
from app.base.utils.query import get_object_or_404
from app.user.dependencies import get_authenticated_user, get_authenticated_user_or_none
from app.user.models import User
from app.user.schemas import (
    ChangePasswordIn,
    LoginIn,
    PublicUserProfile,
    Registration,
    UpdateAccessTokenIn,
    UserDetailsIn,
    UserDetailsOut,
    UserOut,
)
from app.user.services import token as token_service
from app.user.services import user as user_service
from app.user.services.auth import AuthService
from app.user.services.token import TokenService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/api/v1/registration", status_code=status.HTTP_201_CREATED, response_model=UserOut
)
async def registration(data: Registration) -> Any:
    user = await user_service.create_user(
        username=data.username,
        full_name=data.full_name,
        plain_password=data.password,
    )

    return UserOut(**user.model_dump())


@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    return await token_service.token_response(form_data.username, form_data.password)


@router.post("/api/v1/token")
async def login(data: LoginIn) -> Any:
    return await token_service.token_response(data.username, data.password)


@router.post("/api/v1/update-access-token")
async def update_access_token(
    data: UpdateAccessTokenIn = Body(...),
) -> Any:
    access_token = await TokenService.create_access_token_from_refresh_token(
        data.refresh_token
    )
    return {"access_token": access_token}


@router.post("/api/v1/change-password")
async def change_password(
    data: ChangePasswordIn, user: User = Depends(get_authenticated_user)
) -> Any:
    if not user.password or not AuthService.verify_password(
        data.current_password, user.password
    ):
        raise CustomException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code=ExType.AUTHENTICATION_ERROR,
            field="current_password",
            detail="Password did not match",
        )

    hash_password = AuthService.get_password_hash(data.new_password)

    await user.aupdate(raw={"$set": {"password": hash_password}})

    return {"message": "Password changed successfully."}


@router.put("/api/v1/logout-from-all-device")
async def logout_from_all_device(user: User = Depends(get_authenticated_user)) -> Any:
    user.random_str = User.new_random_str()
    await user.aupdate()

    return {"message": "Logged out."}


@router.get("/api/v1/users/me", response_model=UserOut)
async def get_me(user: User = Depends(get_authenticated_user)) -> Any:
    return UserOut(**user.model_dump())


@router.get("/api/v1/users/details", response_model=UserDetailsOut)
async def get_user_details(
    user: User = Depends(get_authenticated_user),
) -> UserDetailsOut:
    user_details = await User.afind_one({"_id": user.id})

    return UserDetailsOut(**user_details.model_dump())  # type: ignore


@router.patch("/api/v1/users/update", response_model=UserOut)
async def update_user(
    user_data: UserDetailsIn, user: User = Depends(get_authenticated_user)
) -> Any:
    user_details = await User.afind_one({"_id": user.id})

    user_details = update_partially(user_details, user_data)
    await user_details.aupdate()

    return UserOut(**user_details.model_dump())


@router.get("/api/v1/users/{username}", response_model=UserOut)
async def ger_user_public_profile(
    username: str,
    _: User | None = Depends(get_authenticated_user_or_none),
) -> Any:
    public_user: User = await get_object_or_404(User, filter={"username": username})
    user_dump = public_user.model_dump()

    return PublicUserProfile(**user_dump)
