from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Seed default category, regex, and UPI account mappings."

    def handle(self, *args, **options):
        try:
            # mapping.py lives at the project root and exposes seed_default_mappings.
            from mapping import seed_default_mappings
        except ImportError as exc:  # pragma: no cover - hard failure path
            raise CommandError("Could not import seed_default_mappings from mapping.py") from exc

        seed_default_mappings()
        self.stdout.write(self.style.SUCCESS("Default mappings seeded."))
