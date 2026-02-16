from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from django.contrib.auth.models import Group, Permission

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


class UserManagementViewSet(viewsets.ModelViewSet):
    """
    User management viewset.

    Handles:
    - User registration (POST /api/users/ - public)
    - User profile (GET /api/users/me/ - authenticated)
    - User CRUD (admin actions)
    """

    permission_classes = [UserActionPermission()]

    def get_queryset(self):
        """
        Filter queryset based on user permissions.

        - Superusers see all users
        - Staff with view_user see all users
        - Regular users only see themselves
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
        Registration is public, everything else requires authentication.
        """
        if self.action == "create":
            return [AllowAny()]
        return [IsAuthenticated(), UserActionPermission()]

    def get_throttles(self):
        """Apply throttling to registration."""
        if self.action == "create":
            return [RegistrationRateThrottle()]
        return [UserActionThrottle()]

    def create(self, request, *args, **kwargs):
        """
        User registration endpoint.

        POST /api/users/
        Body: {
            "email": "user@example.com",
            "full_name": "John Doe",
            "telephone_number": "+1234567890",
            "password": "secure_password"
        }

        Returns: User object + tokens (tokens added by signal)
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create user (signal will fire and assign tokens)
        user = serializer.save()

        # Return user data + tokens from signal
        response_data = ReadOnlyUserSerializer(user).data

        # Tokens are attached to user object by signal
        if hasattr(user, "_auth_tokens"):
            response_data["tokens"] = user._auth_tokens

        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        """Deactivate a user (requires can_deactivate_user permission)."""
        user = self.get_object()
        serializer = AdminUserActionSerializer(
            user, data={"is_active": False}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        """Activate a user (requires can_activate_user permission)."""
        user = self.get_object()
        serializer = AdminUserActionSerializer(
            user, data={"is_active": True}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="soft-delete")
    def soft_delete(self, request, pk=None):
        """Soft delete a user (requires can_soft_delete_user permission)."""
        user = self.get_object()
        serializer = AdminUserActionSerializer(
            user, data={"is_soft_deleted": True}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """Get current user's profile (no special permissions needed)."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    # --- SUPERUSER-ONLY ACTIONS ---

    @action(detail=True, methods=["post"], url_path="set-staff-status")
    def set_staff_status(self, request, pk=None):
        """
        Set staff status (SUPERUSER ONLY).

        Body: {"is_staff": true/false}
        """
        if not request.user.is_superuser:
            return Response(
                {"detail": "Only superusers can modify staff status."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = self.get_object()
        serializer = AdminUserActionSerializer(
            user, data={"is_staff": request.data.get("is_staff")}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ReadOnlyUserSerializer(user).data)

    @action(detail=True, methods=["post"], url_path="set-superuser-status")
    def set_superuser_status(self, request, pk=None):
        """
        Set superuser status (SUPERUSER ONLY).

        Body: {"is_superuser": true/false}
        """
        if not request.user.is_superuser:
            return Response(
                {"detail": "Only superusers can modify superuser status."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = self.get_object()
        serializer = AdminUserActionSerializer(
            user, data={"is_superuser": request.data.get("is_superuser")}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ReadOnlyUserSerializer(user).data)

    @action(detail=True, methods=["post"], url_path="manage-groups")
    def manage_groups(self, request, pk=None):
        """
        Add/remove user from groups (SUPERUSER ONLY).

        Body: {
            "action": "add" or "remove",
            "group_ids": [1, 2, 3]
        }
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
            groups = Group.objects.filter(id__in=group_ids)

            if action_type == "add":
                user.groups.add(*groups)
            else:  # remove
                user.groups.remove(*groups)

            return Response(
                {
                    "detail": f"Successfully {action_type}ed {len(groups)} group(s).",
                    "current_groups": list(user.groups.values_list("name", flat=True)),
                }
            )

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="manage-permissions")
    def manage_permissions(self, request, pk=None):
        """
        Add/remove user permissions (SUPERUSER ONLY).

        Body: {
            "action": "add" or "remove",
            "permission_ids": [1, 2, 3]
        }
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
            permissions = Permission.objects.filter(id__in=permission_ids)

            if action_type == "add":
                user.user_permissions.add(*permissions)
            else:  # remove
                user.user_permissions.remove(*permissions)

            return Response(
                {
                    "detail": f"Successfully {action_type}ed {len(permissions)} permission(s).",
                    "current_permissions": list(
                        user.user_permissions.values_list("codename", flat=True)
                    ),
                }
            )

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
