from typing import Annotated

from bson import ObjectId
from pydantic import BeforeValidator


def validate_object_id(value: str) -> str:
    if not ObjectId.is_valid(value):
        raise ValueError("Invalid ObjectId")

    return value


# Annotated type with validator
ObjectIdStr = Annotated[str, BeforeValidator(validate_object_id)]
