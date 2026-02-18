"""
Typed exception hierarchy for the users service layer.

These exceptions are raised by service methods and caught by the global
DRF exception handler in config/exceptions.py, which maps them to the
appropriate HTTP status codes.

Hierarchy:
    ServiceError (base)
    ├── ConflictError      → 409 Conflict
    ├── ServiceValidationError → 400 Bad Request
    ├── NotFoundError      → 404 Not Found
    └── PermissionDeniedError  → 403 Forbidden

Usage:
    from users.exceptions import ConflictError

    if user.is_soft_deleted:
        raise ConflictError("User is already deleted.")
"""


class ServiceError(Exception):
    """
    Base class for all service-layer exceptions.

    Carries a human-readable message and an optional HTTP status code hint.
    The global exception handler reads `http_status` to determine the response code.

    Args:
        message (str): Human-readable error description.
    """

    http_status: int = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ConflictError(ServiceError):
    """
    Raised when an operation conflicts with the current resource state.

    Examples:
        - Deactivating a user who is already deactivated.
        - Soft-deleting a user who is already soft-deleted.
        - Activating a user who is already active.

    Maps to HTTP 409 Conflict.
    """

    http_status = 409


class ServiceValidationError(ServiceError):
    """
    Raised when service input fails business-rule validation.

    Distinct from DRF's serializer ValidationError — this is raised by
    service methods when they receive logically invalid arguments (e.g.
    a non-boolean value for is_superuser).

    Maps to HTTP 400 Bad Request.
    """

    http_status = 400


class NotFoundError(ServiceError):
    """
    Raised when a referenced resource does not exist.

    Examples:
        - Group IDs that don't exist in the database.
        - Permission IDs that don't exist.

    Maps to HTTP 404 Not Found.
    """

    http_status = 404


class PermissionDeniedError(ServiceError):
    """
    Raised when an operation is forbidden by business rules.

    Distinct from DRF's PermissionDenied (which is for HTTP-level auth checks).
    This is for domain-level guards, e.g. preventing removal of the last superuser.

    Maps to HTTP 403 Forbidden.
    """

    http_status = 403
