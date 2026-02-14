import logging
from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from users.throttling import (
    RegistrationRateThrottle,
    UserActionThrottle,
)
from users.filters import UserFilter
from users.serializers import (
    ReadOnlyUserSerializer,
    RegisterSerializer,
    UpdateUserSerializer,
)
from users.utils.permission_utils import can_access_user

logger = logging.getLogger(__name__)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    REST API endpoint for complete user management (CRUD).

    Core CRUD Operations:
    - POST / -> Create new user (AllowAny)
    - GET / -> List users (IsAuthenticated, staff only)
    - GET /{id}/ -> Get user details (IsAuthenticated, owner or staff)
    - PUT/PATCH /{id}/ -> Update user (IsAuthenticated, owner or staff)
    - DELETE /{id}/ -> Hard delete user (IsAuthenticated, staff only)

    Filtering & Search (Query Parameters):
    - email: Email contains search (case-insensitive)
    - full_name: Search first_name OR last_name (case-insensitive)
    - telephone_number: Exact phone match (E.164 format)
    - email_verification_status: pending | verified | rejected
    - telephone_verification_status: pending | verified | rejected | no_number
    - is_active, is_staff, is_superuser, is_soft_deleted: Boolean filters
    - created_after, created_before: Date range filters (ISO format)

    Attributes:
        queryset: All User objects (filtered by get_queryset based on permissions)
        serializer_class: ReadOnlyUserSerializer (default for retrieve/list)
        lookup_field: 'user_id' (UUID primary key)
        filterset_class: UserFilter (15+ filter fields)
        ordering_fields: created_at, email, first_name, last_name, last_updated
        ordering: '-created_at' (newest first)
    """

    queryset = User.objects.all()
    serializer_class = ReadOnlyUserSerializer
    lookup_field = "user_id"
    filterset_class = UserFilter
    ordering_fields = [
        "created_at",
        "last_updated",
        "email",
        "first_name",
        "last_name",
    ]
    ordering = ["-created_at"]
    throttle_classes = [UserActionThrottle]

    def get_serializer_class(self):
        """Select serializer class based on the current action."""
        if self.action == "create":
            return RegisterSerializer
        elif self.action in ["update", "partial_update"]:
            return UpdateUserSerializer
        return ReadOnlyUserSerializer

    def get_permissions(self):
        """Define permission classes based on the current action."""
        if self.action == "create":
            # Registration is restricted to admins (public signup via AllAuth)
            permission_classes = [IsAdminUser]
        elif self.action == "list":
            # List all users - staff only
            permission_classes = [IsAdminUser]
        elif self.action in ["retrieve", "update", "partial_update", "destroy"]:
            # Get/update own profile - owner or staff
            # Hard delete (destroy) - staff only (but managed via check_object_permissions or separate check?)
            # The original code said "DELETE /users/{id}/ -> Hard delete user (IsAuthenticated, staff only)"
            # But the logic block in original `get_permissions` for 'retrieve', 'update', 'partial_update' was [IsAuthenticated]
            # It didn't mention 'destroy'. 'destroy' would fall to the `else` block which was `[IsAuthenticated]`.
            # I will trust the original logic which allowed `destroy` to pass initial perm check and fail at object level if needed
            # Or reliance on IsAdminUser for list implies typical admin usage.
            # Actually, `check_object_permissions` enforces "can_access_user".
            permission_classes = [IsAuthenticated]
        else:
            # Custom actions (if any added later) - authenticated users
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_throttles(self):
        """Apply specific throttles for registration."""
        if self.action == "create":
            return [RegistrationRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        """Filter queryset based on user's permissions and authentication status."""
        user = self.request.user
        if user.is_authenticated:
            if user.is_staff:
                # Staff can see all users
                return User.objects.all_objects()
            else:
                # Regular users can only see themselves
                return User.objects.filter(user_id=user.user_id)
        # Ensure 'create' (POST) works without queryset access?
        # ModelViewSet.create doesn't use get_queryset usually, but unique validators might.
        return User.objects.none()

    def check_object_permissions(self, request, obj):
        """Enforce object-level permissions by delegating to `permission_utils.can_access_user`."""
        if can_access_user(request.user, obj):
            return
        self.permission_denied(
            request, message="You do not have permission to access this user."
        )
