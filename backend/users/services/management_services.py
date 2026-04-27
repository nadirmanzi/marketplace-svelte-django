"""
User management service: state transitions for User accounts.

Encapsulates business logic for user lifecycle operations so views
don't need to know field names or validation rules.

Methods raise typed exceptions from users.exceptions on failure,
which are handled by the global DRF exception handler.

Methods:
- soft_delete_user: Mark user as deleted (reversible, preserves data)
- deactivate_user: Temporarily disable login without deleting
- activate_user: Re-enable a deactivated or soft-deleted user
- set_staff_status: Grant/revoke staff (admin interface) access
- set_superuser_status: Grant/revoke superuser (all permissions) access
- manage_groups: Add/remove user from permission groups
- manage_permissions: Add/remove individual permissions from user
"""

from typing import List
from django.db import transaction, DatabaseError
from django.contrib.auth import get_user_model
from config.logging import audit_log
from users.exceptions import (
    ConflictError,
    ServiceValidationError,
    NotFoundError,
    PermissionDeniedError,
)

User = get_user_model()


class UserManagementService:
    """
    Encapsulates user state transitions.

    All methods are atomic transactions. On success, they return the updated
    user instance. On failure, they raise a specific ServiceError subclass.
    """

    @classmethod
    @transaction.atomic
    def soft_delete_user(cls, user) -> "User":
        """
        Mark user as soft-deleted (reversible).

        Sets is_soft_deleted=True and is_active=False, records soft_deleted_at timestamp.

        Args:
            user: User instance to soft-delete.

        Returns:
            User: Updated user instance.

        Raises:
            ConflictError: If user is already soft-deleted.
        """
        if getattr(user, "is_soft_deleted", False):
            audit_log.warning(
                action="user.soft_delete",
                message=f"Attempt to soft-delete already deleted user: {user.user_id}",
                status="failed",
                source="users.services.management_services",
                target_user_id=str(user.user_id),
            )
            raise ConflictError("User already deleted")

        try:
            user.is_soft_deleted = True
            user.save(update_fields=["is_soft_deleted", "is_active", "soft_deleted_at"])

            audit_log.info(
                action="user.soft_delete",
                message=f"User soft-deleted: {user.user_id}",
                status="success",
                source="users.services.management_services",
                target_user_id=str(user.user_id),
            )
            return user
        except DatabaseError as e:
            audit_log.error(
                action="user.soft_delete",
                message=f"Database error during soft-delete: {str(e)}",
                status="failed",
                source="users.services.management_services",
                target_user_id=str(user.user_id),
            )
            raise

    @classmethod
    @transaction.atomic
    def deactivate_user(cls, user) -> "User":
        """
        Temporarily disable a user account.

        Args:
            user: User instance to deactivate.

        Returns:
            User: Updated user instance.

        Raises:
            ConflictError: If already deactivated or soft-deleted.
        """
        if getattr(user, "is_soft_deleted", False):
            raise ConflictError("User has been deleted and cannot be deactivated")

        if not getattr(user, "is_active", True):
            raise ConflictError("User already deactivated")

        try:
            user.is_active = False
            user.save(update_fields=["is_active"])

            audit_log.info(
                action="user.deactivate",
                message=f"User deactivated: {user.user_id}",
                status="success",
                source="users.services.management_services",
                target_user_id=str(user.user_id),
            )
            return user
        except DatabaseError as e:
            audit_log.error(
                action="user.deactivate",
                message=f"Database error during deactivation: {str(e)}",
                status="failed",
                source="users.services.management_services",
                target_user_id=str(user.user_id),
            )
            raise

    @classmethod
    @transaction.atomic
    def activate_user(cls, user) -> "User":
        """
        Re-enable a deactivated or soft-deleted user account.

        Args:
            user: User instance to activate.

        Returns:
            User: Updated user instance.

        Raises:
            ConflictError: If already active.
        """
        if getattr(user, "is_active", True) and not getattr(
            user, "is_soft_deleted", False
        ):
            raise ConflictError("User already active")

        try:
            user.is_active = True
            user.is_soft_deleted = False
            user.save(update_fields=["is_active", "is_soft_deleted", "soft_deleted_at"])

            audit_log.info(
                action="user.activate",
                message=f"User activated: {user.user_id}",
                status="success",
                source="users.services.management_services",
                target_user_id=str(user.user_id),
            )
            return user
        except DatabaseError as e:
            audit_log.error(
                action="user.activate",
                message=f"Database error during activation: {str(e)}",
                status="failed",
                source="users.services.management_services",
                target_user_id=str(user.user_id),
            )
            raise

    @staticmethod
    @transaction.atomic
    def set_staff_status(user, is_staff: bool) -> "User":
        """
        Grant or revoke staff status.

        Args:
            user: User instance.
            is_staff: True to grant staff, False to revoke.

        Returns:
            User: Updated user instance.
        """
        if not isinstance(is_staff, bool):
            raise ServiceValidationError("is_staff must be a boolean.")

        try:
            user.is_staff = is_staff
            user.save(update_fields=["is_staff"])
            audit_log.info(
                action="user.set_staff_status",
                message=f"User staff status changed: {user.user_id} -> {is_staff}",
                status="success",
                source="users.services.management_services",
                target_user_id=str(user.user_id),
                extra={"is_staff": is_staff},
            )
            return user
        except DatabaseError as e:
            audit_log.error(
                action="user.set_staff_status",
                message=f"Database error setting staff status: {str(e)}",
                status="failed",
                source="users.services.management_services",
                target_user_id=str(user.user_id),
            )
            raise

    @staticmethod
    @transaction.atomic
    def set_superuser_status(user, is_superuser: bool) -> "User":
        """
        Grant or revoke superuser status.

        Includes safety guard to prevent zero superusers.

        Args:
            user: User instance.
            is_superuser: True to grant, False to revoke.

        Returns:
            User: Updated user instance.

        Raises:
            PermissionDeniedError: If revoking the last superuser.
            ServiceValidationError: If input is not boolean.
        """
        if is_superuser is None:
            raise ServiceValidationError("is_superuser field is required.")

        if not isinstance(is_superuser, bool):
            raise ServiceValidationError("is_superuser must be a boolean.")

        # Safety guard: Check for last superuser
        if not is_superuser and user.is_last_superuser:
            raise PermissionDeniedError(
                "Cannot remove superuser status from the last superuser."
            )

        try:
            user.is_superuser = is_superuser
            user.save(update_fields=["is_superuser"])
            audit_log.info(
                action="user.set_superuser_status",
                message=f"User superuser status changed: {user.user_id} -> {is_superuser}",
                status="success",
                source="users.services.management_services",
                target_user_id=str(user.user_id),
                extra={"is_superuser": is_superuser},
            )
            return user
        except DatabaseError as e:
            audit_log.error(
                action="user.set_superuser_status",
                message=f"Database error setting superuser status: {str(e)}",
                status="failed",
                source="users.services.management_services",
                target_user_id=str(user.user_id),
            )
            raise

    @staticmethod
    @transaction.atomic
    def manage_groups(user, action: str, group_ids: List[int]) -> "User":
        """
        Add or remove a user from permission groups.

        Args:
            user: User instance.
            action: 'add' or 'remove'.
            group_ids: List of group IDs.

        Returns:
            User: Updated user instance.

        Raises:
            ServiceValidationError: For invalid action.
            NotFoundError: If any provided group IDs are invalid.
        """
        if action not in ["add", "remove"]:
            raise ServiceValidationError("Action must be 'add' or 'remove'.")

        from django.contrib.auth.models import Group

        groups = Group.objects.filter(id__in=group_ids)

        if groups.count() != len(group_ids):
            found_ids = set(groups.values_list("id", flat=True))
            missing_ids = set(group_ids) - found_ids
            raise NotFoundError(f"Groups not found: {list(missing_ids)}")

        try:
            if action == "add":
                user.groups.add(*groups)
            else:
                user.groups.remove(*groups)

            audit_log.info(
                action=f"user.groups.{action}",
                message=f"User groups updated ({action}): {user.user_id}",
                status="success",
                source="users.services.management_services",
                target_user_id=str(user.user_id),
                extra={"group_ids": group_ids, "action": action},
            )
            return user
        except DatabaseError as e:
            audit_log.error(
                action="user.manage_groups",
                message=f"Database error managing groups: {str(e)}",
                status="failed",
                source="users.services.management_services",
                target_user_id=str(user.user_id),
            )
            raise

    @staticmethod
    @transaction.atomic
    def manage_permissions(user, action: str, permission_ids: List[int]) -> "User":
        """
        Add or remove individual permissions from a user.

        Args:
            user: User instance.
            action: 'add' or 'remove'.
            permission_ids: List of permission IDs.

        Returns:
            User: Updated user instance.

        Raises:
            ServiceValidationError: For invalid action.
            NotFoundError: If any provided permission IDs are invalid.
        """
        if action not in ["add", "remove"]:
            raise ServiceValidationError("Action must be 'add' or 'remove'.")

        from django.contrib.auth.models import Permission

        perms = Permission.objects.filter(id__in=permission_ids)

        if perms.count() != len(permission_ids):
            found_ids = set(perms.values_list("id", flat=True))
            missing_ids = set(permission_ids) - found_ids
            raise NotFoundError(f"Permissions not found: {list(missing_ids)}")

        try:
            if action == "add":
                user.user_permissions.add(*perms)
            else:
                user.user_permissions.remove(*perms)

            audit_log.info(
                action=f"user.permissions.{action}",
                message=f"User permissions updated ({action}): {user.user_id}",
                status="success",
                source="users.services.management_services",
                target_user_id=str(user.user_id),
                extra={"permission_ids": permission_ids, "action": action},
            )
            return user
        except DatabaseError as e:
            audit_log.error(
                action="user.manage_permissions",
                message=f"Database error managing permissions: {str(e)}",
                status="failed",
                source="users.services.management_services",
                target_user_id=str(user.user_id),
            )
            raise
