from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from HungerFree.models import UserProfile, NGO

class Command(BaseCommand):
    help = 'Links NGO users with their NGO profiles'

    def handle(self, *args, **options):
        # Get all users with NGO role
        ngo_users = UserProfile.objects.filter(role='NGO').select_related('user')
        
        for profile in ngo_users:
            user = profile.user
            # Try to find matching NGO by email
            try:
                ngo = NGO.objects.get(email=user.email)
                if not ngo.user:
                    ngo.user = user
                    ngo.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully linked NGO user: {user.username}')
                    )
            except NGO.DoesNotExist:
                # Create new NGO profile if none exists
                NGO.objects.create(
                    user=user,
                    name=user.username,
                    contact_person=user.username,
                    email=user.email,
                    phone='',
                    address='',
                    city='',
                    is_verified=False
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Created and linked new NGO profile for: {user.username}')
                )