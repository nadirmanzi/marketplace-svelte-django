# users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from config.logging import audit_log

from users.tokens import CustomRefreshToken

User = get_user_model()


@receiver(post_save, sender=User)
def assign_tokens_on_creation(sender, instance, created, **kwargs):
    """
    Assign JWT tokens to newly created users.
    
    This signal fires whenever a user is created:
    - API registration (POST /api/users/)
    - Django admin user creation
    - Management commands (createsuperuser, etc.)
    - Django shell (User.objects.create_user())
    
    Tokens are attached to the user instance as _auth_tokens attribute
    for views to access and return to the client.
    """
    if not created:
        return  # Only for new users
    
    try:
        # Generate refresh token (which includes access token)
        refresh = CustomRefreshToken.for_user(instance)
        
        # Attach tokens to user instance (not saved to DB)
        instance._auth_tokens = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        
        # Log token generation
        audit_log.info(
            action="auth.tokens_generated",
            message="JWT tokens generated for new user",
            status="success",
            source="users.signals.assign_tokens_on_creation",
        )
        
    except Exception as e:
        # Log error but don't block user creation
        audit_log.error(
            action="auth.token_generation_failed",
            message=f"Failed to generate tokens: {str(e)}",
            status="failed",
            source="users.signals.assign_tokens_on_creation",
        )