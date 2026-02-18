from rest_framework import permissions

class UserActionPermission(permissions.BasePermission):
    """
    Permission class for user management with field-level restrictions.
    
    Rules:
    - Superusers can do anything
    - Non-superusers cannot modify superuser accounts
    - Users can view and update their own profile but NOT sensitive fields
    - Staff with 'view_user' can list/view all users
    - Staff with 'change_user' can update other users' profiles
    - Specific permissions required for activation/deactivation/soft-delete actions
    - Self-modification of sensitive fields is prohibited
    - ONLY superusers can modify: is_staff, is_superuser, groups, user_permissions
    """
    
    # Fields users can modify on their own profile
    SELF_EDITABLE_FIELDS = {'email', 'full_name', 'telephone_number'}
    
    # Fields that require special permissions (even for staff)
    SENSITIVE_FIELDS = {
        'is_active', 'is_superuser', 
        'is_staff', 'user_permissions', 'groups',
        'password_changed_at', 'session_version'
    }
    
    # Fields that ONLY superusers can modify
    SUPERUSER_ONLY_FIELDS = {
        'is_staff', 'is_soft_deleted', 'is_superuser', 'user_permissions', 'groups'
    }
    
    def has_permission(self, request, view):
        """
        Check view-level permissions (list, create actions).
        
        Returns:
            bool: True if user can access this view action
        """
        user = request.user
        
        # Must be authenticated
        if not user or not user.is_authenticated:
            return False
        
        # Superusers can do anything
        if user.is_superuser:
            return True
        
        # For list action, user must have view_user permission
        if view.action == 'list':
            return user.has_perm('users.view_user')
        
        # For retrieve (detail view), we'll check in has_object_permission
        # if they're viewing themselves
        if view.action == 'retrieve':
            return True  # Will be checked in has_object_permission
        
        # For create (registration), typically anyone can create
        # But you might want to restrict this
        if view.action == 'create':
            return True  # Or add your own logic
        
        # For update/partial_update/delete actions
        if view.action in ['update', 'partial_update', 'destroy']:
            return True  # Will be checked in has_object_permission
        
        # For custom actions (deactivate, activate, soft_delete)
        if view.action == 'deactivate':
            return user.has_perm('users.can_deactivate_user')
        
        if view.action == 'activate':
            return user.has_perm('users.can_activate_user')
        
        if view.action == 'soft_delete':
            return user.has_perm('users.can_soft_delete_user')
        
        # Default deny for unknown actions
        return False
    
    def has_object_permission(self, request, view, obj):
        """
        Check object-level permissions (retrieve, update, delete on specific user).
        
        Returns:
            bool: True if user can perform action on this specific user object
        """
        user = request.user
        
        # Superusers can do anything
        if user.is_superuser:
            return True
        
        # Non-superusers cannot touch superuser accounts at all
        if obj.is_superuser:
            return False
        
        is_self = (obj == user)
        
        # Safe methods (GET, HEAD, OPTIONS) - retrieve action
        if request.method in permissions.SAFE_METHODS:
            # Users can view themselves OR staff with view_user can view anyone
            return is_self or user.has_perm('users.view_user')
        
        data = request.data
        
        # --- CHECK FOR SUPERUSER-ONLY FIELDS ---
        # Non-superusers cannot modify these fields AT ALL (not even on themselves)
        attempted_superuser_fields = set(data.keys()) & self.SUPERUSER_ONLY_FIELDS
        if attempted_superuser_fields:
            return False  # Only superusers can touch these fields
        
        # --- SELF-MODIFICATION RULES ---
        if is_self:
            # Users CANNOT modify any sensitive fields on themselves
            if any(field in data for field in self.SENSITIVE_FIELDS):
                return False
            
            # Users CAN modify their own profile fields
            # Check that they're only modifying allowed fields
            attempted_fields = set(data.keys())
            if attempted_fields <= self.SELF_EDITABLE_FIELDS:
                return True
            
            # If trying to modify fields beyond self-editable ones, deny
            return False
        
        # --- MODIFYING OTHER USERS ---
        # Must have base change_user permission to modify anyone else
        if not user.has_perm('users.change_user'):
            return False
        
        # Check specific action permissions
        if 'is_active' in data:
            if data.get('is_active') is False:
                # Deactivating someone
                if not user.has_perm('users.can_deactivate_user'):
                    return False
            elif data.get('is_active') is True:
                # Activating someone
                if not user.has_perm('users.can_activate_user'):
                    return False
        
        if 'is_soft_deleted' in data:
            if not user.has_perm('users.can_soft_delete_user'):
                return False
        
        # All checks passed
        return True