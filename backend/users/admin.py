from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import User, FailedLoginAttempt
from .forms import UserCreationForm, UserChangeForm
from .services.account_lockout_service import AccountLockoutService


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    ordering = ["-created_at"]
    list_display = [
        "full_name",
        "email",
        "telephone_number",
        "email_verification_status",
        "user_role",
        "is_active",
        "lockout_status",
        # "failed_login_attempts",
    ]
    list_filter = []
    actions = ["unlock_accounts"]
    search_fields = ["email", "first_name", "last_name", "telephone_number"]
    readonly_fields = [
        "user_id",
        "password_changed_at",
        "session_version",
        "created_at",
        "last_updated",
        "password_expired",
        "lockout_status",
        "failed_login_attempts",
        "is_locked",
        "locked_until",
        "locked_at",
        "user_role",
    ]

    def get_queryset(self, request):
        """Return queryset of all users including soft-deleted ones."""
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
                            "first_name",
                            "last_name",
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
                    "Verification Status",
                    {
                        "fields": (
                            "email_verification_status",
                            "telephone_verification_status",
                        )
                    },
                ),
                (
                    "Permissions",
                    {
                        "fields": (
                            "is_active",
                            "is_staff",
                            "is_superuser",
                            "groups",
                            "user_permissions",
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
                            "first_name",
                            "last_name",
                            "telephone_number",
                        )
                    },
                ),
                (
                    "Password",
                    {
                        "fields": (
                            "password_changed_at",
                            "password_expires_in_days",
                            "password_expired",
                            "password",
                        ),
                        "description": 'Raw passwords are not stored. Use <a href="password/">this form</a> to change the password.',
                    },
                ),
                (
                    "Verification Status",
                    {
                        "fields": (
                            "email_verification_status",
                            "telephone_verification_status",
                        )
                    },
                ),
                (
                    "Permissions",
                    {
                        "fields": (
                            "is_active",
                            "is_staff",
                            "is_superuser",
                            "groups",
                            "user_permissions",
                        )
                    },
                ),
                (
                    "Account Status",
                    {"fields": ("is_soft_deleted",)},
                ),
                (
                    "Account Lockout",
                    {
                        "fields": (
                            "failed_login_attempts",
                            "lockout_status",
                            "locked_until",
                            "locked_at",
                        ),
                        "description": "Account lockout information for failed login attempts.",
                    },
                ),
                (
                    "Audit & Session",
                    {
                        "fields": (
                            "session_version",
                            "created_at",
                            "last_updated",
                        ),
                        # "classes": ("collapse",),
                    },
                ),
            )

    def user_role(self, obj):
        if obj.is_superuser:
            return "Superuser"
        elif obj.is_staff and not obj.is_superuser:
            return "Staff"
        elif not obj.is_staff and not obj.is_superuser:
            return "User"
        return "Unknown"

    user_role.short_description = "User Role"

    def lockout_status(self, obj):
        """Display lockout status with color coding."""
        if obj.is_locked:
            return format_html(
                '<span style="color: red;">Locked until {}</span>',
                obj.locked_until.strftime("%Y-%m-%d %H:%M:%S")
                if obj.locked_until
                else "N/A",
            )
        elif obj.failed_login_attempts > 0:
            return format_html(
                '<span style="color: orange;">{} failed attempts</span>',
                obj.failed_login_attempts,
            )
        return mark_safe('<span style="color: green;">Not locked</span>')

    lockout_status.short_description = "Lockout Status"

    def is_locked(self, obj):
        """Filter helper for locked accounts."""
        return obj.is_locked

    is_locked.boolean = True
    is_locked.short_description = "Is Locked"

    def unlock_accounts(self, request, queryset):
        """Admin action to unlock selected accounts."""
        unlocked_count = 0
        for user in queryset:
            if user.is_locked:
                if AccountLockoutService.unlock_account(user.email):
                    unlocked_count += 1

        if unlocked_count > 0:
            self.message_user(
                request,
                f"Successfully unlocked {unlocked_count} account(s).",
                level="success",
            )
        else:
            self.message_user(
                request, "No locked accounts were selected or found.", level="warning"
            )

    unlock_accounts.short_description = "Unlock selected accounts"


@admin.register(FailedLoginAttempt)
class FailedLoginAttemptAdmin(admin.ModelAdmin):
    """Admin interface for IP-based failed login attempts."""

    list_display = [
        "ip_address",
        "failed_attempts",
        "lockout_status",
        "last_attempt_at",
        "created_at",
    ]
    list_filter = []
    search_fields = ["ip_address"]
    readonly_fields = [
        "ip_address",
        "failed_attempts",
        "locked_until",
        "last_attempt_at",
        "created_at",
    ]
    actions = ["unlock_ips", "cleanup_expired"]

    def lockout_status(self, obj):
        """Display lockout status with color coding."""
        if obj.is_locked:
            return format_html(
                '<span style="color: red;">Locked until {}</span>',
                obj.locked_until.strftime("%Y-%m-%d %H:%M:%S")
                if obj.locked_until
                else "N/A",
            )
        elif obj.failed_attempts > 0:
            return format_html(
                '<span style="color: orange;">{} failed attempts</span>',
                obj.failed_attempts,
            )
        return mark_safe('<span style="color: green;">Not locked</span>')

    lockout_status.short_description = "Lockout Status"

    def unlock_ips(self, request, queryset):
        """Admin action to unlock selected IP addresses."""
        unlocked_count = 0
        for attempt in queryset:
            if attempt.is_locked:
                if AccountLockoutService.unlock_ip(attempt.ip_address):
                    unlocked_count += 1

        if unlocked_count > 0:
            self.message_user(
                request,
                f"Successfully unlocked {unlocked_count} IP address(es).",
                level="success",
            )
        else:
            self.message_user(
                request,
                "No locked IP addresses were selected or found.",
                level="warning",
            )

    unlock_ips.short_description = "Unlock selected IP addresses"

    def cleanup_expired(self, request, queryset):
        """Admin action to cleanup expired lockout records."""
        deleted_count = AccountLockoutService.cleanup_expired_locks()
        self.message_user(
            request,
            f"Cleaned up {deleted_count} expired lockout record(s).",
            level="success",
        )

    cleanup_expired.short_description = "Cleanup expired lockout records"
