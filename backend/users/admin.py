from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from users.models import User
from users.forms import UserCreationForm, UserChangeForm


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
        "is_active",
    ]
    list_filter = []
    search_fields = ["email", "full_name", "telephone_number", "user_id"]
    readonly_fields = [
        "user_id",
        "password_changed_at",
        "session_version",
        "created_at",
        "updated_at",
        "password_expired",
    ]

    def get_queryset(self, request):
        """Return queryset of all users including soft-deleted ones. None superusers can't query a superuser profile"""
        if not request.user.is_superuser:
            return User.objects.filter(is_superuser=False)
        return User.objects.all_objects()

    def get_fieldsets(self, request, obj=None):
        """Define fieldsets for create and change views."""
        if not obj:
            # Creation form fieldsets
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
            # Change form fieldsets
            return (
                (
                    "Account Information",
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
                    "Password",
                    {
                        "fields": (
                            "password",
                            "password_changed_at",
                            "password_expired",
                            "password_expires_in_days",
                        ),
                        "description": 'Raw passwords are not stored. Use <a href="password/">this form</a> to change the password.',
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
                (
                    "Account Status",
                    {"fields": ("is_soft_deleted", "soft_deleted_at")},
                ),
                (
                    "Audit & Session",
                    {
                        "fields": (
                            "session_version",
                            "created_at",
                            "updated_at",
                        ),
                        # "classes": ("collapse",),
                    },
                ),
            )

    def user_role(self, obj):
        if obj.is_superuser:
            return mark_safe('<span style="color: #ff6600">Superuser</span>')
        elif obj.is_staff and not obj.is_superuser:
            return mark_safe('<span style="color: #0066ff">Staff</span>')
        elif not obj.is_staff and not obj.is_superuser:
            return mark_safe('<span style="color: white">User</span>')
        return "User"

    user_role.short_description = "User Role"