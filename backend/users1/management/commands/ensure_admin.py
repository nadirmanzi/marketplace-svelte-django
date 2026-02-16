from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Ensures the specified superuser exists'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Superuser credentials
        EMAIL = "nadir@gmail.com"
        PASSWORD = "manzi200"
        FIRST_NAME = "nadir"
        LAST_NAME = "manzi"
        TELEPHONE = "+250786802977"

        if not User.objects.filter(email=EMAIL).exists():
            self.stdout.write(f"Creating superuser {EMAIL}...")
            User.objects.create_superuser(
                email=EMAIL,
                password=PASSWORD,
                first_name=FIRST_NAME,
                last_name=LAST_NAME,
                telephone_number=TELEPHONE
            )
            self.stdout.write(self.style.SUCCESS(f"Superuser {EMAIL} created successfully."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Superuser {EMAIL} already exists."))
