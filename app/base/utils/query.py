import logging
from typing import Any, no_type_check

from fastapi import status
from mongodb_odm.exceptions import ObjectDoesNotExist

from app.base.exceptions import CustomException, ExType

logger = logging.getLogger(__name__)


@no_type_check
def get_object_or_404(
    Model,
    filter: dict[str, Any],
    detail: str = "Object Not Found",
    **kwargs: dict[str, Any],
):
    try:
        return Model.get(filter, **kwargs)
    except ObjectDoesNotExist as e:
        logger.warning(f"404 on:{Model.__name__} filter:{kwargs}")
        raise CustomException(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ExType.OBJECT_NOT_FOUND,
            detail=detail,
        ) from e
