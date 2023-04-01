import logging
from typing import Dict

from fastapi import HTTPException, status
from mongodb_odm.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)


def get_object_or_404(
    Model,
    filter: Dict,
    detail="Object Not Found",
    **kwargs,
):
    try:
        return Model.get(filter, **kwargs)
    except ObjectDoesNotExist:
        logger.warning(f"404 on:{Model.__name__} filter:{kwargs}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
