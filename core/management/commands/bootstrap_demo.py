from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Create a demo user (username=demo, password=demo12345) if not exists"

    def handle(self, *args, **options):
        username = "demo"
        password = "demo12345"
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS("Demo user already exists."))
            return
        user = User.objects.create_user(username=username, password=password)
        user.is_staff = True
        user.first_name = "Demo"
        user.last_name = "User"
        user.email = "demo@example.com"
        user.save()
        self.stdout.write(self.style.SUCCESS("Demo user created: demo / demo12345"))
