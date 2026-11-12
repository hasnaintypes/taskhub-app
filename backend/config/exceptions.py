import logging

from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Centralized DRF error handling [QA-05].

    Delegates to DRF's default handler for the actual response shape, and
    adds consistent logging for permission denials / auth failures so
    RBAC violations are auditable [QA-06].
    """
    response = exception_handler(exc, context)

    if response is not None and response.status_code in (401, 403):
        request = context.get("request")
        user = getattr(request, "user", None)
        logger.warning(
            "access_denied",
            extra={
                "status_code": response.status_code,
                "path": getattr(request, "path", None),
                "user_id": getattr(user, "id", None),
            },
        )

    return response
