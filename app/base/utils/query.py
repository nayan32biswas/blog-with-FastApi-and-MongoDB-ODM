import logging
from typing import Any, Dict, no_type_check

from fastapi import HTTPException, status
from mongodb_odm.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)


@no_type_check
def get_object_or_404(
    Model,
    filter: Dict[str, Any],
    detail: str = "Object Not Found",
    **kwargs: Dict[str, Any],
):
    try:
        return Model.get(filter, **kwargs)
    except ObjectDoesNotExist:
        logger.warning(f"404 on:{Model.__name__} filter:{kwargs}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
