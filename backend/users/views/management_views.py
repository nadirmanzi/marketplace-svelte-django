"""
User management ViewSet: registration, profile, and admin actions.

Handles:
- POST   /users/management/          -> create (public registration)
- GET    /users/management/          -> list (staff/superuser only)
- GET    /users/management/{pk}/     -> retrieve (self or staff)
- PUT    /users/management/{pk}/     -> update (self or staff)
- PATCH  /users/management/{pk}/     -> partial_update (self or staff)
- GET    /users/management/me/       -> current user profile
- POST   /users/management/{pk}/deactivate/       -> deactivate (staff)
- POST   /users/management/{pk}/activate/         -> activate (staff)
- POST   /users/management/{pk}/soft-delete/      -> soft-delete (staff)
- POST   /users/management/{pk}/set-staff-status/ -> set staff (superuser)
- POST   /users/management/{pk}/set-superuser-status/ -> set superuser (superuser)
- POST   /users/management/{pk}/manage-groups/    -> manage groups (superuser)
- POST   /users/management/{pk}/manage-permissions/ -> manage permissions (superuser)
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from django.contrib.auth.models import Group, Permission
from config.logging import audit_log

import logging

from users.serializers import (
    AdminUserActionSerializer,
    UpdateUserSerializer,
    StaffUserActionSerializer,
    ReadOnlyUserSerializer,
    RegisterSerializer,
)
from users.utils.permissions import UserActionPermission
from users.models import User
from users.throttling import UserActionThrottle, RegistrationRateThrottle
from users.services.management_services import UserManagementService


logger = logging.getLogger(__name__)


class UserManagementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user CRUD and admin lifecycle actions.

    Permission model:
    - Registration (create): public
    - Profile (me): authenticated
    - List/retrieve: staff with view_user or superuser
    - Update: self (own profile fields) or staff with change_user
    - Admin actions (deactivate, activate, soft-delete): staff with specific perms
    - Superuser-only actions (set-staff, set-superuser, groups, permissions): superuser
    """
    permission_classes = [UserActionPermission()]

    def get_queryset(self):
        """
        Return queryset scoped to the requesting user's access level.

        - Superusers: all users including soft-deleted (all_objects)
        - Staff with view_user: active users only
        - Regular users: only themselves

        Returns:
            QuerySet[User]
        """
        user = self.request.user

        if user.is_superuser:
            # Superusers see ALL users including soft-deleted
            return User.objects.all_objects()

        if user.has_perm("users.view_user"):
            # Staff see active users (not soft-deleted)
            return User.objects.all()

        # Regular users only see themselves
        return User.objects.filter(user_id=user.user_id)

    def get_serializer_class(self):
        """
        Return the appropriate serializer for the current action.

        Mapping:
        - create -> RegisterSerializer
        - update/partial_update -> UpdateUserSerializer
        - deactivate/activate/soft_delete -> StaffUserActionSerializer
        - set_staff_status/set_superuser_status/manage_groups/manage_permissions -> AdminUserActionSerializer
        - all others -> ReadOnlyUserSerializer
        """
        if self.action == "create":
            return RegisterSerializer
        if self.action in ["update", "partial_update"]:
            return UpdateUserSerializer
        elif self.action in ["deactivate", "activate", "soft_delete"]:
            return StaffUserActionSerializer
        elif self.action in [
            "set_staff_status",
            "set_superuser_status",
            "manage_groups",
            "manage_permissions",
        ]:
            return AdminUserActionSerializer
        return ReadOnlyUserSerializer

    def get_permissions(self):
        """
        Return permission classes for the current action.

        - create: AllowAny (public registration)
        - me: AllowAny + IsAuthenticated (authenticated users only)
        - all others: IsAuthenticated + UserActionPermission
        """
        if self.action == "create":
            return [AllowAny()]

        if self.action == "me":
            return [AllowAny(), IsAuthenticated()]
        return [IsAuthenticated(), UserActionPermission()]

    def get_throttles(self):
        """
        Apply RegistrationRateThrottle for create, UserActionThrottle for everything else.
        """
        if self.action == "create":
            return [RegistrationRateThrottle()]
        return [UserActionThrottle()]

    def create(self, request, *args, **kwargs):
        """
        Register a new user account (public endpoint).

        POST /users/management/
        Body: {
            "email": "user@example.com",
            "full_name": "John Doe",
            "telephone_number": "+1234567890",  # optional
            "password": "secure_password"
        }

        Returns:
            201: User profile + tokens (tokens attached by post_save signal).
            400: Validation errors.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create user — post_save signal fires and attaches _auth_tokens
        user = serializer.save()

        response_data = ReadOnlyUserSerializer(user).data

        # Tokens are attached to user instance by assign_tokens_on_creation signal
        if hasattr(user, "_auth_tokens"):
            response_data["tokens"] = user._auth_tokens

        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        """
        Temporarily disable a user account (staff only).

        POST /users/management/{pk}/deactivate/

        Returns:
            200: {"message": ..., "user": {user_id, email}}
            400: {"error": reason} if already deactivated or soft-deleted.
        """
        user = self.get_object()

        user, error = UserManagementService.deactivate_user(user)
        if error:
            audit_log.warning(
                action="user.deactivate",
                message=f"Deactivation failed: {error}",
                status="failed",
                source="users.views.management_views.deactivate",
                target_user_id=str(request.user.user_id),
            )
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        audit_log.info(
            action="user.deactivate",
            message="User deactivated successfully",
            status="success",
            source="users.views.management_views.deactivate",
            target_user_id=str(request.user.user_id),
        )
        return Response(
            {
                "message": "User has been deactivated.",
                "user": ReadOnlyUserSerializer(user, fields=["user_id", "email"]).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        """
        Re-enable a deactivated or soft-deleted user account (staff only).

        POST /users/management/{pk}/activate/

        Returns:
            200: {"message": ..., "user": {user_id, email}}
            400: {"error": reason} if already active.
        """
        user = self.get_object()

        user, error = UserManagementService.activate_user(user)
        if error:
            audit_log.warning(
                action="user.activate",
                message=f"Activation failed: {error}",
                status="failed",
                source="users.views.management_views.activate",
                target_user_id=str(request.user.user_id),
            )
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        audit_log.info(
            action="user.activate",
            message="User activated successfully",
            status="success",
            source="users.views.management_views.activate",
            target_user_id=str(request.user.user_id),
        )
        return Response(
            {
                "message": "User has been activated.",
                "user": ReadOnlyUserSerializer(user, fields=["user_id", "email"]).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="soft-delete")
    def soft_delete(self, request, pk=None):
        """
        Mark user as deleted while preserving all data (reversible, staff only).

        POST /users/management/{pk}/soft-delete/

        Returns:
            200: {"message": ..., "user": {user_id, email}}
            400: {"error": reason} if already soft-deleted.
        """
        user = self.get_object()

        user, error = UserManagementService.soft_delete_user(user)
        if error:
            audit_log.warning(
                action="user.soft_delete",
                message=f"Soft delete failed: {error}",
                status="failed",
                source="users.views.management_views.soft_delete",
                target_user_id=str(request.user.user_id),
            )
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        audit_log.info(
            action="user.soft_delete",
            message="User soft-deleted successfully",
            status="success",
            source="users.views.management_views.soft_delete",
            target_user_id=str(request.user.user_id),
        )
        return Response(
            {
                "message": "User has been soft-deleted.",
                "user": ReadOnlyUserSerializer(user, fields=["user_id", "email"]).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="me", permission_classes=[])
    def me(self, request):
        """
        Return the authenticated user's own profile.

        GET /users/management/me/

        Returns:
            200: Full user profile (ReadOnlyUserSerializer).
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    # --- SUPERUSER-ONLY ACTIONS ---

    @action(detail=True, methods=["post"], url_path="set-staff-status")
    def set_staff_status(self, request, pk=None):
        """
        Grant or revoke staff status (superuser only).

        POST /users/management/{pk}/set-staff-status/
        Body: {"is_staff": true}

        Returns:
            200: Updated user profile.
            400: {"detail": reason} on validation error.
        """
        user = self.get_object()
        user, error = UserManagementService.set_staff_status(
            user, request.data.get("is_staff")
        )
        if error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ReadOnlyUserSerializer(user).data)

    @action(detail=True, methods=["post"], url_path="set-superuser-status")
    def set_superuser_status(self, request, pk=None):
        """
        Grant or revoke superuser status (superuser only).

        POST /users/management/{pk}/set-superuser-status/
        Body: {"is_superuser": false}

        Returns:
            200: Updated user profile.
            400: {"detail": reason} on validation error.
            403: If requesting user is not a superuser.
        """
        if not request.user.is_superuser:
            return Response(
                {"detail": "Only superusers can modify superuser status."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = self.get_object()
        user, error = UserManagementService.set_superuser_status(
            user, request.data.get("is_superuser")
        )
        if error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ReadOnlyUserSerializer(user).data)

    @action(detail=True, methods=["post"], url_path="manage-groups")
    def manage_groups(self, request, pk=None):
        """
        Add or remove a user from permission groups (superuser only).

        POST /users/management/{pk}/manage-groups/
        Body: {
            "action": "add" | "remove",
            "group_ids": [1, 2, 3]
        }

        Returns:
            200: {"detail": ..., "current_groups": [...]}
            400: {"detail": reason} on invalid input.
            403: If requesting user is not a superuser.
        """
        if not request.user.is_superuser:
            return Response(
                {"detail": "Only superusers can modify user groups."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = self.get_object()
        action_type = request.data.get("action")
        group_ids = request.data.get("group_ids", [])

        if action_type not in ["add", "remove"]:
            return Response(
                {"detail": "Action must be 'add' or 'remove'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user, error = UserManagementService.manage_groups(user, action_type, group_ids)
            if error:
                return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)

            return Response(
                {
                    "detail": f"Successfully {action_type}ed groups.",
                    "current_groups": list(user.groups.values_list("name", flat=True)),
                }
            )

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="manage-permissions")
    def manage_permissions(self, request, pk=None):
        """
        Add or remove individual permissions from a user (superuser only).

        POST /users/management/{pk}/manage-permissions/
        Body: {
            "action": "add" | "remove",
            "permission_ids": [1, 2, 3]
        }

        Returns:
            200: {"detail": ..., "current_permissions": [...]}
            400: {"detail": reason} on invalid input.
            403: If requesting user is not a superuser.
        """
        if not request.user.is_superuser:
            return Response(
                {"detail": "Only superusers can modify user permissions."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = self.get_object()
        action_type = request.data.get("action")
        permission_ids = request.data.get("permission_ids", [])

        if action_type not in ["add", "remove"]:
            return Response(
                {"detail": "Action must be 'add' or 'remove'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user, error = UserManagementService.manage_permissions(user, action_type, permission_ids)
            if error:
                return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)

            return Response(
                {
                    "detail": f"Successfully {action_type}ed permissions.",
                    "current_permissions": list(
                        user.user_permissions.values_list("codename", flat=True)
                    ),
                }
            )

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
