import logging
from typing import Any

from mongodb_odm.exceptions import ObjectDoesNotExist

from app.base.exceptions import ObjectNotFoundException

logger = logging.getLogger(__name__)


def get_object_or_404(
    model: Any,
    filter: dict[str, Any],
    detail: str = "Object Not Found",
    **kwargs: dict[str, Any],
) -> Any:
    try:
        return model.get(filter, **kwargs)
    except ObjectDoesNotExist as e:
        logger.warning(f"404 on:{model.__name__} filter:{kwargs}")
        raise ObjectNotFoundException(
            detail=detail,
        ) from e
