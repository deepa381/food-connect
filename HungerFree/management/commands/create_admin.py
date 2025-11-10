from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Create an admin user if none exists"

    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(username="deepa").exists():
            User.objects.create_superuser("deepa", "manyamdeepa607@gmail.com", "Deepa@123")
            self.stdout.write(self.style.SUCCESS("✅ Admin user created!"))
        else:
            self.stdout.write(self.style.WARNING("⚠️ Admin user already exists."))
