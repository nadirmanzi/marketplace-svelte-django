"""User lifecycle service: soft-delete, deactivate, reactivate.

This service encapsulates state transitions for User objects so controllers
(views) don't need to know field names or validation rules.
"""
from typing import Tuple, Optional
import logging

from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class UserLifecycleService:
    """Encapsulate user state transitions.

    Each method returns (user, None) on success or (None, error_message)
    on failure to keep the API simple and HTTP-agnostic.
    """

    @classmethod
    @transaction.atomic
    def soft_delete_user(cls, user) -> Tuple[Optional[object], Optional[str]]:
        """Mark the `user` as soft-deleted.

        Expected behavior:
        - If already soft-deleted, return an informative error
        - Otherwise set `is_soft_deleted = True` and save
        """
        if getattr(user, "is_soft_deleted", False):
            logger.info("Attempt to soft-delete already deleted user: %s", getattr(user, "pk", None))
            return None, "User already deleted"

        user.is_soft_deleted = True
        # Optionally also deactivate the account
        if hasattr(user, "is_active"):
            user.is_active = False

        # Set deletion timestamp if available
        if hasattr(user, "deleted_at"):
            user.deleted_at = timezone.now()

        # Build update_fields list only for attributes that exist on the model
        update_fields = []
        if hasattr(user, "is_soft_deleted"):
            update_fields.append("is_soft_deleted")
        if hasattr(user, "is_active"):
            update_fields.append("is_active")
        if hasattr(user, "deleted_at"):
            update_fields.append("deleted_at")

        # Validate and save changes
        try:
            if hasattr(user, "full_clean"):
                user.full_clean()
        except Exception:
            # Let caller decide how to present validation errors; still attempt save
            logger.exception("Validation failed during soft-delete for user=%s", getattr(user, "pk", None))

        if update_fields:
            user.save(update_fields=update_fields)
        else:
            # Fallback: full save if model lacks those fields (very unlikely)
            user.save()
        # Note: update_fields improves performance and avoids touching other fields
        logger.info("User soft-deleted: %s", user.pk)
        return user, None

    @classmethod
    @transaction.atomic
    def deactivate_user(cls, user) -> Tuple[Optional[object], Optional[str]]:
        """Deactivate (temporarily) a user account.

        - If already deactivated, return error
        - If soft-deleted, return error (can't deactivate a deleted account)
        """
        if getattr(user, "is_soft_deleted", False):
            return None, "User has been deleted and cannot be deactivated"

        if not getattr(user, "is_active", True):
            return None, "User already deactivated"

        user.is_active = False
        user.save(update_fields=["is_active"])
        logger.info("User deactivated: %s", user.pk)
        return user, None

    @classmethod
    @transaction.atomic
    def reactivate_user(cls, user) -> Tuple[Optional[object], Optional[str]]:
        """Reactivate a previously deactivated user.

        - If the user is soft-deleted, reactivation should not be allowed
          (unless the business rules differ).
        - If already active, return an informative error.
        """
        if getattr(user, "is_soft_deleted", False):
            return None, "Deleted accounts cannot be reactivated"

        if getattr(user, "is_active", True):
            return None, "User already active"

        # Restore active state and clear deletion metadata when present
        user.is_active = True
        if hasattr(user, "is_soft_deleted"):
            user.is_soft_deleted = False
        if hasattr(user, "deleted_at"):
            user.deleted_at = None

        update_fields = ["is_active"]
        if hasattr(user, "is_soft_deleted"):
            update_fields.append("is_soft_deleted")
        if hasattr(user, "deleted_at"):
            update_fields.append("deleted_at")

        # Validate and save
        try:
            if hasattr(user, "full_clean"):
                user.full_clean()
        except Exception:
            logger.exception("Validation failed during reactivate for user=%s", getattr(user, "pk", None))

        user.save(update_fields=update_fields)
        logger.info("User reactivated: %s", user.pk)
        return user, None
