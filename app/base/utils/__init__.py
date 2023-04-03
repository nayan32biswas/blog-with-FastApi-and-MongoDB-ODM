import json
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel
from pydantic.utils import deep_update


def calculate_offset(page: int, limit: int):
    return (page - 1) * limit


def get_offset(page: int, limit: int):
    if not 1 <= limit <= 100:
        raise ValueError("Invalid pagination limit")
    return calculate_offset(page, limit)


def update_partially(target, source: BaseModel, exclude=None):
    cls = target.__class__
    update_data = source.dict(exclude_unset=True, exclude=exclude)
    target = cls(**deep_update(cls.to_mongo(target), update_data))
    return target


def date_to_datetime(val: date):
    return datetime(val.year, val.month, val.day)


def print_pretty(data):
    if type(data) == list:
        for each in data:
            print(json.dumps(each, indent=4, default=str, sort_keys=True))
    else:
        print(json.dumps(data, indent=4, default=str, sort_keys=True))


class EnumValue:
    def __init__(self, name: str, value: Any):
        self.name = name
        self.value = value
