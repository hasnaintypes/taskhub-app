from django.core.management.base import BaseCommand

from accounts.models import Role, User

DEMO_USERS = [
    ("admin", "admin@taskhub.local", Role.ADMIN),
    ("manager", "manager@taskhub.local", Role.MANAGER),
    ("employee1", "employee1@taskhub.local", Role.EMPLOYEE),
    ("employee2", "employee2@taskhub.local", Role.EMPLOYEE),
]
DEMO_PASSWORD = "DemoPass123!"


class Command(BaseCommand):
    help = "Seed one Admin, one Manager, and two Employee accounts for local testing/demo."

    def handle(self, *args, **options):
        for username, email, role in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=username, defaults={"email": email, "role": role}
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created {username} ({role})"))
            else:
                self.stdout.write(f"{username} already exists, skipping")
