"""
Custom permissions for catalog resources.

IsOwnerOrStaff:
    Allows access if the user is the owner of the resource,
    or has is_staff=True (admin/staff), or is a superuser.
"""

from rest_framework.permissions import BasePermission


class IsOwnerOrStaff(BasePermission):
    """
    Object-level permission: owner, staff, or superuser can mutate.

    For list/create actions, requires authentication.
    For object-level actions, checks if request.user is the resource owner
    (via the `user` FK) or has staff/superuser privileges.
    """

    def has_permission(self, request, view):
        """Require authentication for all management actions."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Allow if user is owner, staff, or superuser."""
        return (
            request.user.is_superuser
            or request.user.is_staff
            or self._is_owner(request.user, obj)
        )

    @staticmethod
    def _is_owner(user, obj):
        """Check ownership by traversing to the user FK."""
        # Direct owner (Product)
        if hasattr(obj, "user_id"):
            return obj.user_id == user.pk
        # Variant → Product → User
        if hasattr(obj, "product"):
            return obj.product.user_id == user.pk
        return False
