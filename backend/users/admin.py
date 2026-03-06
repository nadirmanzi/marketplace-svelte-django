from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils import timezone
from datetime import timedelta
from users.models import User
from users.forms import UserCreationForm, UserChangeForm
from config.logging import audit_log


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    ordering = ["-created_at"]
    
    list_display = [
        "full_name",
        "email",
        "telephone_number",
        "user_role",
        "status_badge",
        "is_soft_deleted_badge",
        "created_at",
    ]
    
    list_filter = [
        # "is_active",
        # "is_staff",
        # "is_superuser",
        # "is_soft_deleted",
        # "created_at",
    ]
    
    search_fields = ["email", "full_name", "telephone_number", "user_id"]
    
    readonly_fields = [
        "user_id",
        "password_changed_at",
        "session_version",
        "created_at",
        "updated_at",
        "password_expired",
    ]

    actions = ["force_password_expiry", "soft_delete_users", "reactivate_users"]

    def get_queryset(self, request):
        """Return queryset of all users including soft-deleted ones."""
        if not request.user.is_superuser:
            return User.objects.filter(is_superuser=False)
        return User.objects.all_objects()

    def get_fieldsets(self, request, obj=None):
        """Define fieldsets for create and change views."""
        if not obj:
            return (
                (
                    "Account Information",
                    {
                        "fields": (
                            "email",
                            "full_name",
                            "telephone_number",
                        )
                    },
                ),
                (
                    "Password",
                    {
                        "fields": ("password1", "password2"),
                        "description": "Enter a strong password and confirm it.",
                    },
                ),
                (
                    "Permissions",
                    {
                        "fields": (
                            "is_active",
                            "is_staff",
                            "is_superuser",
                            "user_permissions",
                            "groups",
                        )
                    },
                ),
            )
        else:
            return (
                (
                    "Basic Information",
                    {
                        "fields": (
                            "user_id",
                            "email",
                            "full_name",
                            "telephone_number",
                        )
                    },
                ),
                (
                    "Security & Password",
                    {
                        "classes": ("collapse",),
                        "fields": (
                            "password",
                            "password_changed_at",
                            "password_expired",
                            "password_expires_in_days",
                            "session_version",
                        ),
                        "description": 'Raw passwords are not stored. Use <a href="password/">this form</a> to change the password.',
                    },
                ),
                (
                    "Permissions & Access",
                    {
                        "fields": (
                            "is_active",
                            "is_staff",
                            "is_superuser",
                            "user_permissions",
                            "groups",
                        )
                    },
                ),
                (
                    "Lifecycle Status",
                    {
                        "fields": ("is_soft_deleted", "soft_deleted_at"),
                    },
                ),
                (
                    "Audit Metadata",
                    {
                        "classes": ("collapse",),
                        "fields": (
                            "created_at",
                            "updated_at",
                        ),
                    },
                ),
            )

    # --- Custom Column Methods ---

    def user_role(self, obj):
        if obj.is_superuser:
            return mark_safe('<b style="color: #d35400;">Superuser</b>')
        elif obj.is_staff:
            return mark_safe('<b style="color: #2980b9;">Staff</b>')
        return mark_safe('<span style="color: #7f8c8d;">User</span>')

    def status_badge(self, obj):
        if obj.is_active:
            return mark_safe('<span style="background-color: #27ae60; color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: bold;">ACTIVE</span>')
        return mark_safe('<span style="background-color: #c0392b; color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: bold;">INACTIVE</span>')

    def is_soft_deleted_badge(self, obj):
        if obj.is_soft_deleted:
            return mark_safe('<span style="color: #e67e22; font-weight: bold;">🗑 Deleted</span>')
        return mark_safe('<span style="color: #bdc3c7;">-</span>')

    status_badge.short_description = "Status"
    is_soft_deleted_badge.short_description = "Soft Deleted"
    user_role.short_description = "Role"

    # --- Custom Actions ---

    @admin.action(description="Force selected users to change password")
    def force_password_expiry(self, request, queryset):
        # Set password_changed_at to long ago
        count = queryset.update(password_changed_at=timezone.now() - timedelta(days=365))
        
        for user in queryset:
            audit_log.warning(
                action="admin.force_password_expiry",
                message="Password expiry forced by admin",
                status="success",
                source="users.admin.UserAdmin",
                target_user_id=str(user.user_id),
            )
        
        self.message_user(request, f"Successfully forced password change for {count} users.")

    @admin.action(description="Soft-delete selected users")
    def soft_delete_users(self, request, queryset):
        # We should use the service or at least ensure is_soft_deleted is True 
        # so models.save() handles the rest.
        count = 0
        for user in queryset:
            if not user.is_soft_deleted:
                user.is_soft_deleted = True
                user.save()
                count += 1
                audit_log.info(
                    action="admin.soft_delete",
                    message="User soft-deleted via admin action",
                    status="success",
                    source="users.admin.UserAdmin",
                    target_user_id=str(user.user_id),
                )
        self.message_user(request, f"Successfully soft-deleted {count} users.")

    @admin.action(description="Reactivate selected users")
    def reactivate_users(self, request, queryset):
        count = 0
        for user in queryset:
            if user.is_soft_deleted:
                user.is_soft_deleted = False
                user.is_active = True
                user.save()
                count += 1
                audit_log.info(
                    action="admin.reactivate",
                    message="User reactivated via admin action",
                    status="success",
                    source="users.admin.UserAdmin",
                    target_user_id=str(user.user_id),
                )
        self.message_user(request, f"Successfully reactivated {count} users.")