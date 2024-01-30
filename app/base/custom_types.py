from typing import Any, Union

from bson import ObjectId
from pydantic_core import core_schema


class ObjectIdStr(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        object_id_schema = core_schema.chain_schema(
            [
                core_schema.no_info_plain_validator_function(cls.validate),
            ]
        )
        return core_schema.json_or_python_schema(
            json_schema=object_id_schema,
            python_schema=core_schema.union_schema(
                [core_schema.is_instance_schema(str), object_id_schema]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, v: Union[str, ObjectId]) -> str:
        if isinstance(v, ObjectId):
            return str(v)
        elif isinstance(v, str):
            try:
                ObjectId(v)
            except Exception as e:
                raise TypeError("Invalid ObjectId") from e
            return v
        raise TypeError("ObjectId required")
