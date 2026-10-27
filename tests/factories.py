from decimal import Decimal

import factory
from django.utils import timezone

from finance.models import CurrentAccount, User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email_address = factory.Sequence(lambda n: f"motorista{n}@exemplo.com")

    @factory.post_generation
    def password(self, create, value, **kwargs):
        self.set_password(value or "senha123")
        if create:
            self.save()


class CurrentAccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CurrentAccount

    user = factory.SubFactory(UserFactory)
    cash_account_id = 0
    cost_id = 6
    type_launche = 1
    price = Decimal("100.00")
    date_ocurrence = factory.LazyFunction(timezone.localdate)
