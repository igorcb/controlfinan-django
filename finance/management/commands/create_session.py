"""Prints a signed "session_id" cookie value signed in as the given e-mail (local testing and benchmarks)."""

from django.core import signing
from django.core.management.base import BaseCommand, CommandError

from finance.auth import COOKIE, COOKIE_SALT
from finance.models import Session, User


class Command(BaseCommand):
    help = "Creates a session for the user and prints the session_id cookie value."

    def add_arguments(self, parser):
        parser.add_argument("email")

    def handle(self, *args, **options):
        user = User.objects.filter(email_address=User.normalize_email(options["email"])).first()
        if user is None:
            raise CommandError("user not found")
        session = Session.objects.create(user=user, user_agent="create_session", ip_address="127.0.0.1")
        self.stdout.write(signing.get_cookie_signer(salt=COOKIE + COOKIE_SALT).sign(str(session.pk)))
