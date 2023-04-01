import logging
from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.base.utils import update_partially
from app.base.utils.string import rand_str

from .dependencies import get_authenticated_user
from .models import User
from .schemas import Registration, UpdateAccessTokenIn, UserIn, UserOut
from .utils import (
    authenticate_user,
    create_access_token,
    create_access_token_from_refresh_token,
    create_refresh_token,
    get_password_hash,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/api/v1/registration", status_code=status.HTTP_201_CREATED, response_model=UserOut
)
def registration(data: Registration):
    if User.exists({"username": data.username}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists."
        )

    try:
        hash_password = get_password_hash(data.password)
        user = User(
            username=data.username,
            full_name=data.full_name,
            joining_date=datetime.utcnow(),
            password=hash_password,
            rand_str=rand_str(31),
        ).create()
    except Exception as ex:
        logger.warning(f"Raise error while creating user error:{ex}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Something wrong try again."
        )

    return UserOut.from_orm(user)


@router.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = authenticate_user(form_data.username, form_data.password)
    if not user or user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"id": str(user.id), "r_str": str(user.rand_str)}
    )
    refresh_token = create_refresh_token(
        data={"id": str(user.id), "r_str": str(user.rand_str)}
    )
    user.update(raw={"$set": {"last_login": datetime.utcnow()}})
    return {
        "token_type": "Bearer",
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@router.post("/api/v1/update-access-token")
def update_access_token(
    data: UpdateAccessTokenIn = Body(...),
):
    access_token = create_access_token_from_refresh_token(data.refresh_token)
    return {"access_token": access_token}


@router.get("/api/v1/me", response_model=UserOut)
def ger_me(user: User = Depends(get_authenticated_user)):
    return UserOut.from_orm(user)


@router.patch("/api/v1/update-user", response_model=UserOut)
def update_user(user_data: UserIn, user: User = Depends(get_authenticated_user)):
    user = update_partially(user, user_data)
    user.update()
    return UserOut.from_orm(user)


@router.put("/api/v1/logout-from-all-device")
def logout_from_all_device(user: User = Depends(get_authenticated_user)):
    user.rand_str = rand_str(31)
    user.update()
    return {"message": "Logged out."}
