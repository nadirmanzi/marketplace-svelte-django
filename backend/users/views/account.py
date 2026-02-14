import logging
from django.contrib.auth import get_user_model
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.services.user_service import UserLifecycleService
from users.services.account_lockout_service import AccountLockoutService
from config.logging import audit_log
from users.serializers import ReadOnlyUserSerializer
from users.utils.permission_utils import can_access_user

logger = logging.getLogger(__name__)
User = get_user_model()


class AccountViewSet(viewsets.GenericViewSet):
    """
    ViewSet for user account lifecycle and self-service actions.
    """

    queryset = User.objects.all()
    lookup_field = "user_id"

    def check_object_permissions(self, request, obj):
        """Enforce object-level permissions by delegating to `permission_utils.can_access_user`.

        This centralizes the access rules and keeps the view method small.
        """
        if can_access_user(request.user, obj):
            return
        self.permission_denied(
            request, message="You do not have permission to access this user."
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def soft_delete(self, request, user_id=None):
        """Mark user as deleted while preserving all data (reversible deletion)."""
        user = self.get_object()
        self.check_object_permissions(request, user)

        user, error = UserLifecycleService.soft_delete_user(user)
        if error:
            audit_log.warning(
                action="user.soft_delete",
                message=f"Soft delete failed: {error}",
                status="failed",
                source="users.views.account.AccountViewSet.soft_delete",
                extra={"target_user_id": str(user_id)},
            )
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        audit_log.info(
            action="user.soft_delete",
            message="User soft-deleted successfully",
            status="success",
            source="users.views.account.AccountViewSet.soft_delete",
            extra={"target_user_id": str(user.user_id)},
        )
        return Response(
            {
                "message": "User has been soft-deleted.",
                "user": ReadOnlyUserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def deactivate(self, request, user_id=None):
        """Deactivate user account temporarily (keeps data intact and unsoftdeleted)."""
        user = self.get_object()
        self.check_object_permissions(request, user)

        user, error = UserLifecycleService.deactivate_user(user)
        if error:
            audit_log.warning(
                action="user.deactivate",
                message=f"Deactivation failed: {error}",
                status="failed",
                source="users.views.account.AccountViewSet.deactivate",
                extra={"target_user_id": str(user_id)},
            )
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        audit_log.info(
            action="user.deactivate",
            message="User deactivated successfully",
            status="success",
            source="users.views.account.AccountViewSet.deactivate",
            extra={"target_user_id": str(user.user_id)},
        )
        return Response(
            {
                "message": "User has been deactivated.",
                "user": ReadOnlyUserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def reactivate(self, request, user_id=None):
        """Reactivate a deactivated or soft-deleted user account (staff only)."""
        if not request.user.is_staff:
            audit_log.warning(
                action="user.reactivate",
                message="Reactivation denied - not staff",
                status="denied",
                source="users.views.account.AccountViewSet.reactivate",
                extra={"target_user_id": str(user_id)},
            )
            return Response(
                {"error": "Only staff can reactivate users."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = self.get_object()

        user, error = UserLifecycleService.reactivate_user(user)
        if error:
            audit_log.warning(
                action="user.reactivate",
                message=f"Reactivation failed: {error}",
                status="failed",
                source="users.views.account.AccountViewSet.reactivate",
                extra={"target_user_id": str(user_id)},
            )
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        audit_log.info(
            action="user.reactivate",
            message="User reactivated successfully",
            status="success",
            source="users.views.account.AccountViewSet.reactivate",
            extra={"target_user_id": str(user.user_id)},
        )
        return Response(
            {
                "message": "User has been reactivated.",
                "user": ReadOnlyUserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def unlock(self, request, user_id=None):
        """Unlock a locked user account (staff only).
        
        Unlocks an account that has been locked due to too many failed login attempts.
        Resets the failed login attempts counter and clears the lockout status.
        """
        if not request.user.is_staff:
            audit_log.warning(
                action="account.unlock",
                message="Unlock denied - not staff",
                status="denied",
                source="users.views.account.AccountViewSet.unlock",
                extra={"target_user_id": str(user_id)},
            )
            return Response(
                {"error": "Only staff can unlock accounts."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = self.get_object()

        if not user.is_locked:
            return Response(
                {"message": "Account is not locked."},
                status=status.HTTP_200_OK,
            )

        success = AccountLockoutService.unlock_account(user.email)
        if success:
            # Refresh user from database
            user.refresh_from_db()
            audit_log.info(
                action="account.unlock",
                message="Account unlocked successfully by admin",
                status="success",
                source="users.views.account.AccountViewSet.unlock",
                extra={
                    "target_user_id": str(user.user_id),
                    "unlocked_by": str(request.user.user_id),
                },
            )
            return Response(
                {
                    "message": "Account has been unlocked.",
                    "user": ReadOnlyUserSerializer(user).data,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Failed to unlock account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
