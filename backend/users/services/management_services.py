"""
User management service: state transitions for User accounts.

Encapsulates business logic for user lifecycle operations so views
don't need to know field names or validation rules.

Each method returns (user, None) on success or (None, error_str) on failure,
keeping the API HTTP-agnostic.

Methods:
- soft_delete_user: Mark user as deleted (reversible, preserves data)
- deactivate_user: Temporarily disable login without deleting
- activate_user: Re-enable a deactivated or soft-deleted user
- set_staff_status: Grant/revoke staff (admin interface) access
- set_superuser_status: Grant/revoke superuser (all permissions) access
- manage_groups: Add/remove user from permission groups
- manage_permissions: Add/remove individual permissions from user
"""
from typing import Optional, Tuple
from django.db import transaction
from django.contrib.auth import get_user_model
from config.logging import audit_log
from django.utils import timezone

User = get_user_model()


class UserManagementService:
    """
    Encapsulates user state transitions.

    All methods are atomic transactions. Each returns (user, None) on success
    or (None, error_message) on failure.

    Example:
        user, error = UserManagementService.deactivate_user(user)
        if error:
            return Response({"error": error}, status=400)
    """

    @classmethod
    @transaction.atomic
    def soft_delete_user(cls, user) -> Tuple[Optional[object], Optional[str]]:
        """
        Mark user as soft-deleted (reversible).

        Sets is_soft_deleted=True and is_active=False, records soft_deleted_at timestamp.
        Data is preserved; user cannot log in.

        Args:
            user: User instance to soft-delete.

        Returns:
            (user, None) on success, (None, error_str) if already deleted.

        Example:
            user, err = UserManagementService.soft_delete_user(user)
        """
        if getattr(user, "is_soft_deleted", False):
            audit_log.warning(
                action="user.soft_delete",
                message=f"Attempt to soft-delete already deleted user: {getattr(user, 'user_id', None)}",
                status="failed",
                source="users.services.management_services",
                target_user_id=str(getattr(user, "user_id", "")),
            )
            return None, "User already deleted"

        user.is_soft_deleted = True
        if hasattr(user, "is_active"):
            user.is_active = False
        if hasattr(user, "soft_deleted_at"):
            user.soft_deleted_at = timezone.now()

        # Build update_fields only for fields that exist on the model
        update_fields = []
        if hasattr(user, "is_soft_deleted"):
            update_fields.append("is_soft_deleted")
        if hasattr(user, "is_active"):
            update_fields.append("is_active")
        if hasattr(user, "soft_deleted_at"):
            update_fields.append("soft_deleted_at")

        if update_fields:
            user.save(update_fields=update_fields)
        else:
            user.save()

        audit_log.info(
            action="user.soft_delete",
            message=f"User soft-deleted: {user.user_id}",
            status="success",
            source="users.services.management_services",
            target_user_id=str(user.user_id),
        )
        return user, None

    @classmethod
    @transaction.atomic
    def deactivate_user(cls, user) -> Tuple[Optional[object], Optional[str]]:
        """
        Temporarily disable a user account (keeps data, not a deletion).

        Args:
            user: User instance to deactivate.

        Returns:
            (user, None) on success, (None, error_str) if already deactivated or soft-deleted.

        Example:
            user, err = UserManagementService.deactivate_user(user)
        """
        if getattr(user, "is_soft_deleted", False):
            return None, "User has been deleted and cannot be deactivated"

        if not getattr(user, "is_active", True):
            return None, "User already deactivated"

        user.is_active = False
        user.save(update_fields=["is_active"])

        audit_log.info(
            action="user.deactivate",
            message=f"User deactivated: {user.user_id}",
            status="success",
            source="users.services.management_services",
            target_user_id=str(user.user_id),
        )
        return user, None

    @classmethod
    @transaction.atomic
    def activate_user(cls, user) -> Tuple[Optional[object], Optional[str]]:
        """
        Re-enable a deactivated or soft-deleted user account.

        Clears is_soft_deleted and soft_deleted_at if set, then sets is_active=True.

        Args:
            user: User instance to activate.

        Returns:
            (user, None) on success, (None, error_str) if already active.

        Example:
            user, err = UserManagementService.activate_user(user)
        """
        if getattr(user, "is_active", True) and not getattr(user, "is_soft_deleted", False):
            return None, "User already active"

        user.is_active = True
        if hasattr(user, "is_soft_deleted"):
            user.is_soft_deleted = False
        if hasattr(user, "soft_deleted_at"):
            user.soft_deleted_at = None

        update_fields = ["is_active"]
        if hasattr(user, "is_soft_deleted"):
            update_fields.append("is_soft_deleted")
        if hasattr(user, "soft_deleted_at"):
            update_fields.append("soft_deleted_at")

        user.save(update_fields=update_fields)

        audit_log.info(
            action="user.activate",
            message=f"User activated: {user.user_id}",
            status="success",
            source="users.services.management_services",
            target_user_id=str(user.user_id),
        )
        return user, None

    @staticmethod
    @transaction.atomic
    def set_staff_status(user, is_staff: bool) -> Tuple[Optional[object], Optional[str]]:
        """
        Grant or revoke staff status (access to Django admin interface).

        Args:
            user: User instance.
            is_staff (bool): True to grant staff, False to revoke.

        Returns:
            (user, None) on success.

        Example:
            user, err = UserManagementService.set_staff_status(user, True)
        """
        user.is_staff = is_staff
        user.save(update_fields=["is_staff"])
        audit_log.info(
            action="user.set_staff_status",
            message=f"User staff status changed: {user.user_id} -> {is_staff}",
            status="success",
            source="users.services.management_services",
            target_user_id=str(user.user_id),
            extra={"is_staff": is_staff}
        )
        return user, None

    @staticmethod
    @transaction.atomic
    def set_superuser_status(user, is_superuser: bool) -> Tuple[Optional[object], Optional[str]]:
        """
        Grant or revoke superuser status (all permissions, no explicit grants needed).

        Args:
            user: User instance.
            is_superuser (bool): True to grant superuser, False to revoke.

        Returns:
            (user, None) on success, (None, error_str) on invalid input.

        Note:
            Does not check if this is the last superuser — that guard lives in the serializer.

        Example:
            user, err = UserManagementService.set_superuser_status(user, False)
        """
        if is_superuser is None:
            return None, "is_superuser field is required."

        if not isinstance(is_superuser, bool):
            return None, "is_superuser must be a boolean."

        user.is_superuser = is_superuser
        user.save(update_fields=["is_superuser"])
        audit_log.info(
            action="user.set_superuser_status",
            message=f"User superuser status changed: {user.user_id} -> {is_superuser}",
            status="success",
            source="users.services.management_services",
            target_user_id=str(user.user_id),
            extra={"is_superuser": is_superuser}
        )
        return user, None

    @staticmethod
    @transaction.atomic
    def manage_groups(user, action: str, group_ids: list) -> Tuple[Optional[object], Optional[str]]:
        """
        Add or remove a user from permission groups.

        Args:
            user: User instance.
            action (str): 'add' or 'remove'.
            group_ids (list[int]): List of Group primary keys.

        Returns:
            (user, None) on success, (None, error_str) if action is invalid.

        Example:
            user, err = UserManagementService.manage_groups(user, "add", [1, 2])
        """
        if action not in ["add", "remove"]:
            return None, "Action must be 'add' or 'remove'."

        from django.contrib.auth.models import Group
        groups = Group.objects.filter(id__in=group_ids)

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
            extra={"group_ids": group_ids, "action": action}
        )
        return user, None

    @staticmethod
    @transaction.atomic
    def manage_permissions(user, action: str, permission_ids: list) -> Tuple[Optional[object], Optional[str]]:
        """
        Add or remove individual permissions from a user.

        Args:
            user: User instance.
            action (str): 'add' or 'remove'.
            permission_ids (list[int]): List of Permission primary keys.

        Returns:
            (user, None) on success, (None, error_str) if action is invalid.

        Example:
            user, err = UserManagementService.manage_permissions(user, "remove", [5])
        """
        if action not in ["add", "remove"]:
            return None, "Action must be 'add' or 'remove'."

        from django.contrib.auth.models import Permission
        permissions = Permission.objects.filter(id__in=permission_ids)

        if action == "add":
            user.user_permissions.add(*permissions)
        else:
            user.user_permissions.remove(*permissions)

        audit_log.info(
            action=f"user.permissions.{action}",
            message=f"User permissions updated ({action}): {user.user_id}",
            status="success",
            source="users.services.management_services",
            target_user_id=str(user.user_id),
            extra={"permission_ids": permission_ids, "action": action}
        )
        return user, None
