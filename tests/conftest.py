import pytest
from django.core.cache import cache
from django.test import Client

from .factories import UserFactory


@pytest.fixture(autouse=True)
def _setup(db, settings):
    settings.BCRYPT_COST = 4  # fast hashing in tests, like Rails' MIN_COST
    cache.clear()  # rate limit counters


@pytest.fixture
def user():
    return UserFactory(email_address="motorista@exemplo.com", password="senha123")


@pytest.fixture
def signed_in(user):
    """A client that signed in through the login form."""
    client = Client()
    response = client.post("/session", {"email_address": user.email_address, "password": "senha123"})
    assert response.status_code == 302
    return client


def entry_params(**overrides):
    params = {
        "type_launche": "credito",
        "price": "150.00",
        "date_ocurrence": "2026-10-20",
        "cost_id": "6",
        "cash_account_id": "5",
        "historic": "Corridas Uber",
    }
    params.update(overrides)
    return {f"current_account[{key}]": value for key, value in params.items()}
