from datetime import date, datetime
from typing import Any

from pydantic import BaseModel
from pydantic.utils import deep_update


def calculate_offset(page: int, limit: int) -> int:
    return (page - 1) * limit


def get_offset(page: int, limit: int) -> int:
    if not 1 <= limit <= 100:
        raise ValueError("Invalid pagination limit")
    return calculate_offset(page, limit)


def update_partially(target, source: BaseModel, exclude=None) -> Any:
    cls = target.__class__
    update_data = source.dict(exclude_unset=True, exclude=exclude)
    target = cls(
        **deep_update(
            target.dict(exclude=cls.get_relational_field_info().keys()), update_data
        )
    )
    return target


def date_to_datetime(val: date) -> datetime:
    return datetime(val.year, val.month, val.day)
