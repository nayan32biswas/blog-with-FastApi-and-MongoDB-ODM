from datetime import date, datetime
from typing import Any, no_type_check

from pydantic import BaseModel
from pydantic.v1.utils import deep_update


@no_type_check
def update_partially(target, source: BaseModel, exclude=None) -> Any:
    cls = target.__class__
    update_data = source.model_dump(exclude_unset=True, exclude=exclude)
    target = cls(
        **deep_update(
            target.model_dump(exclude=cls.get_relational_field_info().keys()),
            update_data,
        )
    )
    return target


def date_to_datetime(val: date) -> datetime:
    return datetime(val.year, val.month, val.day)
