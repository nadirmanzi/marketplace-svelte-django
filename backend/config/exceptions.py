"""
Global DRF exception handler.

Registered via REST_FRAMEWORK["EXCEPTION_HANDLER"] in settings/base.py.
Ensures all API errors return JSON (never Django HTML error pages) with a
consistent response shape.

Response shapes:
    Single error:      {"detail": "Human-readable message."}
    Validation error:  {"errors": {"field": ["message"]}}

Handled exception types:
    ServiceError subclasses  → mapped to their http_status (400/403/404/409)
    DRF ValidationError      → 400 with {"errors": {...}}
    DRF AuthenticationFailed → 401
    DRF PermissionDenied     → 403
    DRF NotFound             → 404
    TokenError               → 401
    Unhandled Exception      → 500 with generic message (logged as error)
"""
import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.exceptions import ValidationError as DRFValidationError

from users.exceptions import ServiceError

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Central exception handler for all DRF views.
    """
    # --- 1. Service-layer typed exceptions ---
    if isinstance(exc, ServiceError):
        _log_service_error(exc, context)
        return Response(
            {"detail": exc.message},
            status=exc.http_status,
        )

    # --- 2. SimpleJWT TokenError ---
    from rest_framework_simplejwt.exceptions import TokenError
    if isinstance(exc, TokenError):
        return Response(
            {"detail": str(exc)},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # --- 3. DRF built-in exceptions (auth, permission, validation, etc.) ---
    response = drf_exception_handler(exc, context)

    if response is not None:
        # Normalize DRF ValidationError → {"errors": {...}}
        if isinstance(exc, DRFValidationError):
            return Response(
                {"errors": _normalize_validation_errors(response.data)},
                status=response.status_code,
            )
        # All other DRF exceptions: ensure {"detail": "..."} shape
        if "detail" not in response.data:
            response.data = {"detail": str(exc)}
        return response

    # --- 3. Unhandled exceptions → 500 ---
    _log_unhandled_exception(exc, context)
    return Response(
        {"detail": "An unexpected error occurred. Please try again later."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_validation_errors(data) -> dict:
    """
    Flatten DRF ValidationError data into a consistent dict.

    DRF can return either a list (non-field errors) or a dict (field errors).
    We normalize both to a dict so the client always gets {"errors": {...}}.

    Args:
        data: response.data from a DRF ValidationError response.

    Returns:
        dict: Normalized error dict, e.g. {"non_field_errors": [...]} or
              {"email": ["Already exists."]}.
    """
    if isinstance(data, list):
        return {"non_field_errors": data}
    if isinstance(data, dict):
        return data
    return {"non_field_errors": [str(data)]}


def _log_service_error(exc: ServiceError, context: dict) -> None:
    """
    Log a ServiceError at WARNING level with request context.

    Args:
        exc: The ServiceError instance.
        context: DRF exception context.
    """
    request = context.get("request")
    view = context.get("view")
    logger.warning(
        "Service error [%s] in %s: %s",
        type(exc).__name__,
        type(view).__name__ if view else "unknown",
        exc.message,
        extra={
            "path": getattr(request, "path", None),
            "method": getattr(request, "method", None),
        },
    )


def _log_unhandled_exception(exc: Exception, context: dict) -> None:
    """
    Log an unhandled exception at ERROR level with full traceback.

    Args:
        exc: The unhandled exception.
        context: DRF exception context.
    """
    request = context.get("request")
    view = context.get("view")
    logger.error(
        "Unhandled exception in %s: %s",
        type(view).__name__ if view else "unknown",
        str(exc),
        exc_info=True,
        extra={
            "path": getattr(request, "path", None),
            "method": getattr(request, "method", None),
        },
    )
