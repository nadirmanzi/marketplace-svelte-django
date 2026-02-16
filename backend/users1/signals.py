"""
AllAuth Signal Handlers for User Account Events.

This module connects AllAuth signals to update user model fields and perform
audit logging for important account lifecycle events.

Signal Handlers:
----------------
- email_confirmed: Updates user.email_verification_status when email is verified
- user_signed_up: Logs new user registrations for audit trail
- password_changed: Logs password changes (session invalidation handled by User.set_password)
- email_changed: Updates verification status when email address changes

Integration:
------------
Signals are automatically connected when the users app is loaded (via apps.py).
"""
import logging
from allauth.account.signals import (
    email_confirmed,
    user_signed_up,
    password_changed,
    email_changed,
    user_logged_in,
)
from django.dispatch import receiver
from config.logging import audit_log
from users1.services.account_lockout_service import AccountLockoutService

logger = logging.getLogger(__name__)


@receiver(email_confirmed)
def handle_email_confirmed(sender, request, email_address, **kwargs):
    """
    Update user's email verification status when email is confirmed.
    
    When a user clicks the email verification link, AllAuth sends this signal.
    We update the user's email_verification_status field to 'verified' to
    keep our custom User model in sync with AllAuth's email verification state.
    
    Args:
        sender: The sender class (EmailAddress model)
        request: Django request object
        email_address: EmailAddress instance that was confirmed
        **kwargs: Additional signal arguments
    """
    user = email_address.user
    if hasattr(user, 'email_verification_status'):
        # Update verification status to verified
        old_status = user.email_verification_status
        user.email_verification_status = 'verified'
        user.save(update_fields=['email_verification_status'])
        
        logger.info(
            "Email confirmed for user_id=%s, email=%s, status: %s -> verified",
            user.user_id,
            email_address.email,
            old_status
        )
        
        audit_log.info(
            action="account.email_verified",
            message="Email address verified successfully",
            status="success",
            source="users.signals.handle_email_confirmed",
            extra={
                "user_id": str(user.user_id),
                "email": email_address.email,
                "previous_status": old_status,
            }
        )


@receiver(user_signed_up)
def handle_user_signed_up(sender, request, user, **kwargs):
    """
    Log new user registration for audit trail.
    
    This signal is sent when a new user completes the signup process.
    We log this event for security auditing and analytics purposes.
    
    Note: The user may not have verified their email yet (depending on
    ACCOUNT_EMAIL_VERIFICATION setting). Email verification is handled
    separately by handle_email_confirmed.
    
    Args:
        sender: The sender class (User model)
        request: Django request object
        user: User instance that was created
        **kwargs: Additional signal arguments (may include 'form_data')
    """
    logger.info(
        "New user signed up: user_id=%s, email=%s",
        user.user_id,
        user.email
    )
    
    audit_log.info(
        action="account.user_signed_up",
        message="New user registered",
        status="success",
        source="users.signals.handle_user_signed_up",
        extra={
            "user_id": str(user.user_id),
            "email": user.email,
            "signup_method": kwargs.get("signup_method", "email"),
        }
    )


@receiver(password_changed)
def handle_password_changed(sender, request, user, **kwargs):
    """
    Log password change events for security auditing.
    
    This signal is sent when a user changes their password through AllAuth.
    Note: Session invalidation (via session_version increment) is already
    handled by User.set_password(), so this handler focuses on audit logging.
    
    Args:
        sender: The sender class (User model)
        request: Django request object
        user: User instance whose password was changed
        **kwargs: Additional signal arguments
    """
    logger.info(
        "Password changed for user_id=%s, email=%s",
        user.user_id,
        user.email
    )
    
    audit_log.info(
        action="account.password_changed",
        message="User password changed",
        status="success",
        source="users.signals.handle_password_changed",
        extra={
            "user_id": str(user.user_id),
            "email": user.email,
            "session_version": getattr(user, "session_version", 0),
        }
    )


@receiver(email_changed)
def handle_email_changed(sender, request, user, from_email_address, to_email_address, **kwargs):
    """
    Update email verification status when email address changes.
    
    When a user changes their email address, the new email needs to be verified.
    We reset the email_verification_status to 'pending' to reflect that the
    new email address requires verification.
    
    Args:
        sender: The sender class (User model)
        request: Django request object
        user: User instance whose email was changed
        from_email_address: EmailAddress instance (old email)
        to_email_address: EmailAddress instance (new email)
        **kwargs: Additional signal arguments
    """
    if hasattr(user, 'email_verification_status'):
        # Reset verification status since new email needs verification
        old_status = user.email_verification_status
        user.email_verification_status = 'pending'
        user.save(update_fields=['email_verification_status'])
        
        logger.info(
            "Email changed for user_id=%s: %s -> %s, status reset to pending",
            user.user_id,
            from_email_address.email,
            to_email_address.email
        )
        
        audit_log.info(
            action="account.email_changed",
            message="User email address changed",
            status="success",
            source="users.signals.handle_email_changed",
            extra={
                "user_id": str(user.user_id),
                "old_email": from_email_address.email,
                "new_email": to_email_address.email,
                "previous_status": old_status,
            }
        )


@receiver(user_logged_in)
def handle_user_logged_in(sender, request, user, **kwargs):
    """
    Reset failed login attempts on successful login.
    
    This signal is sent when a user successfully logs in through AllAuth.
    We reset the failed login attempts counter and clear any lockout status
    to ensure the account is ready for future login attempts.
    
    Args:
        sender: The sender class (User model)
        request: Django request object
        user: User instance that logged in
        **kwargs: Additional signal arguments
    """
    # Reset failed attempts for email
    AccountLockoutService.reset_account_attempts(user.email)
    
    # Reset failed attempts for IP (if applicable)
    ip_address = AccountLockoutService.get_client_ip(request)
    AccountLockoutService.reset_ip_attempts(ip_address)
    
    logger.debug(
        "Reset failed login attempts for user_id=%s, email=%s, ip=%s",
        user.user_id,
        user.email,
        ip_address
    )

