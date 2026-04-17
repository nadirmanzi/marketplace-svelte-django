"""
Global DRF exception handler.

Registered via REST_FRAMEWORK["EXCEPTION_HANDLER"] in settings/base.py.
Ensures all API errors return JSON (never Django HTML error pages) with a
consistent response shape.

Unified Response Schema (all errors):
    {
        "success": false,
        "code": "<error_code>",
        "detail": "Human-readable summary.",
        "errors": { ... }   # field-level validation errors, or {}
    }

Handled exception types:
    ServiceError subclasses  → mapped to their http_status (400/403/404/409)
    DRF ValidationError      → 400
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
from rest_framework.exceptions import (
    ValidationError as DRFValidationError,
    APIException,
)

from users.exceptions import ServiceError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Map ServiceError subclass http_status -> code string
_STATUS_TO_CODE = {
    400: "validation_error",
    401: "authentication_failed",
    403: "permission_denied",
    404: "not_found",
    409: "conflict",
    500: "server_error",
}


def _resolve_code(http_status: int, exc=None) -> str:
    """
    Determine a machine-readable error code.

    Priority:
      1. DRF exc.get_codes() if available and returns a string.
      2. Lookup table by status code.
      3. Fallback "error".
    """
    if exc and hasattr(exc, "get_codes"):
        codes = exc.get_codes()
        if isinstance(codes, str):
            return codes
    return _STATUS_TO_CODE.get(http_status, "error")


def _normalize_validation_data(data):
    """
    Normalize DRF ValidationError.detail into (detail_str, errors_dict).

    Rules (per the approved plan):
      • If data is a list (non-field errors only) → consolidate into detail, errors = {}
      • If data is a dict with ONLY 'non_field_errors' → consolidate into detail, errors = {}
      • If data is a dict with field errors (may also contain non_field_errors) →
          detail = "Validation failed.", errors = field dict (non_field_errors stripped
          and folded into detail if present)
      • Anything else → str(data) into detail
    """
    if isinstance(data, list):
        # Pure non-field errors (e.g. raise ValidationError(["msg"]))
        return " ".join(str(m) for m in data), {}

    if isinstance(data, dict):
        field_errors = {k: v for k, v in data.items() if k != "non_field_errors"}
        non_field = data.get("non_field_errors", [])

        if not field_errors:
            # Only non-field errors → consolidate into detail
            detail = " ".join(str(m) for m in non_field) if non_field else "Validation failed."
            return detail, {}

        # Has real field errors
        detail_parts = []
        if non_field:
            detail_parts.append(" ".join(str(m) for m in non_field))
        detail = " ".join(detail_parts) if detail_parts else "Validation failed."
        return detail, field_errors

    return str(data), {}


def _build_error_response(http_status, code, detail, errors=None):
    """Build the unified error response envelope."""
    return Response(
        {
            "success": False,
            "code": code,
            "detail": detail,
            "errors": errors or {},
        },
        status=http_status,
    )


# ---------------------------------------------------------------------------
# Main handler
# ---------------------------------------------------------------------------


def custom_exception_handler(exc, context):
    """
    Central exception handler for all DRF views.

    Returns every error in the unified schema:
        {"success": false, "code": "...", "detail": "...", "errors": {...}}
    """
    # --- 1. Service-layer typed exceptions ---
    if isinstance(exc, ServiceError):
        _log_service_error(exc, context)
        code = _STATUS_TO_CODE.get(exc.http_status, "service_error")
        return _build_error_response(exc.http_status, code, exc.message)

    # --- 2. SimpleJWT TokenError ---
    from rest_framework_simplejwt.exceptions import TokenError
    if isinstance(exc, TokenError):
        return _build_error_response(
            status.HTTP_401_UNAUTHORIZED,
            "token_error",
            str(exc),
        )

    # --- 3. DRF built-in exceptions ---
    response = drf_exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, DRFValidationError):
            detail, errors = _normalize_validation_data(response.data)
            return _build_error_response(
                response.status_code,
                "validation_error",
                detail,
                errors,
            )

        # All other DRF exceptions (auth, permission, not-found, throttled, etc.)
        detail_str = (
            response.data.get("detail", str(exc))
            if isinstance(response.data, dict)
            else str(exc)
        )
        code = _resolve_code(response.status_code, exc)
        return _build_error_response(response.status_code, code, str(detail_str))

    # --- 4. Unhandled exceptions → 500 ---
    _log_unhandled_exception(exc, context)
    return _build_error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "server_error",
        "An unexpected error occurred. Please try again later.",
    )


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

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
