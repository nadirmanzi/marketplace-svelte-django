"""Permission helper utilities for user-level checks.

Keep permission logic centralized so both views and services can rely on
consistent rules and unit-test the permission functions separately.
"""

def can_access_user(requesting_user, target_user):
    """Return True if `requesting_user` may access `target_user`.

    Rules:
    - Staff users (is_staff=True) can access any target
    - Regular users can access only themselves (compare user_id or pk)
    - Anonymous users cannot access any user (return False)
    """
    if not getattr(requesting_user, "is_authenticated", False):
        return False
    if getattr(requesting_user, "is_staff", False):
        return True
    # Compare user identifiers (prefer `user_id` when available)
    if hasattr(requesting_user, "user_id") and hasattr(target_user, "user_id"):
        return requesting_user.user_id == target_user.user_id
    return getattr(requesting_user, "pk", None) == getattr(target_user, "pk", None)


def can_reactivate_user(requesting_user):
    """Return True if `requesting_user` may reactivate other users.

    Business rule: only staff may reactivate users.
    """
    return bool(getattr(requesting_user, "is_staff", False))
