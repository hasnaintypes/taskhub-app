import logging

from rest_framework import exceptions as drf_exceptions
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Centralized DRF error handling [QA-05].

    Delegates to DRF's default handler for the actual response shape, and
    adds consistent logging for permission denials / auth failures so
    RBAC violations are auditable [QA-06].

    DRF's SessionAuthentication has no WWW-Authenticate challenge, so DRF
    itself downgrades NotAuthenticated to a 403 before this handler runs
    (see APIView.handle_exception). That collapses "not logged in" and
    "logged in but forbidden" into the same status code, which makes it
    impossible for the Angular interceptor to tell "redirect to login"
    apart from "show a permission error". Restoring 401 specifically for
    NotAuthenticated keeps that distinction for the frontend while leaving
    genuine PermissionDenied responses at 403 [FE-13].
    """
    response = exception_handler(exc, context)

    if response is not None and isinstance(exc, drf_exceptions.NotAuthenticated):
        response.status_code = 401

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
