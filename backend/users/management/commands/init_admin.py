import os
import sys
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from config.logging import audit_log

class Command(BaseCommand):
    help = 'Creates a superuser from environment variables if it does not exist'

    def handle(self, *args, **options):
        User = get_user_model()
        
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        full_name = os.environ.get('DJANGO_SUPERUSER_FULL_NAME', 'Admin')
        phone = os.environ.get('DJANGO_SUPERUSER_TELEPHONE', '+250786802977')

        if not email or not password:
            self.stdout.write(self.style.ERROR(
                'Missing DJANGO_SUPERUSER_EMAIL or DJANGO_SUPERUSER_PASSWORD environment variables'
            ))
            sys.exit(1)

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.SUCCESS(f'Superuser {email} already exists.'))
            return

        try:
            user = User.objects.create_superuser(
                email=email,
                password=password,
                full_name=full_name,
                telephone_number=phone
            )
            audit_log.info(
                action="admin.init_superuser",
                message=f"Superuser initialized via management command: {email}",
                status="success",
                source="users.management.commands.init_admin",
                target_user_id=str(user.user_id)
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created superuser {email}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to create superuser: {str(e)}'))
            sys.exit(1)
