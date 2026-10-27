import json
from datetime import date
from decimal import Decimal

from django.test import Client

from finance.models import CurrentAccount

from .conftest import entry_params
from .factories import CurrentAccountFactory, UserFactory


class TestIndex:
    def test_lists_the_user_entries_with_the_total_balance(self, signed_in, user):
        CurrentAccountFactory(user=user, price=Decimal("150"), historic="Corridas Uber")
        CurrentAccountFactory(user=user, price=Decimal("40"), type_launche=-1, cost_id=0)
        CurrentAccountFactory(historic="De outro motorista")
        body = signed_in.get("/").content.decode()
        assert "Saldo total" in body
        assert "R$ 110,00" in body
        assert "Corridas Uber" in body
        assert "De outro motorista" not in body

    def test_filters_by_day(self, signed_in, user):
        CurrentAccountFactory(user=user, date_ocurrence=date(2026, 10, 1), price=Decimal("10"))
        CurrentAccountFactory(user=user, date_ocurrence=date(2026, 10, 2), price=Decimal("20"))
        body = signed_in.get("/current_accounts?date=2026-10-02").content.decode()
        assert "Saldo do dia 02/10/2026" in body
        assert "R$ 20,00" in body
        assert "Limpar" in body

    def test_ignores_an_invalid_date(self, signed_in):
        assert "Saldo total" in signed_in.get("/current_accounts?date=xx").content.decode()

    def test_paginates_30_per_page(self, signed_in, user):
        CurrentAccountFactory.create_batch(31, user=user)
        first = signed_in.get("/").content.decode()
        second = signed_in.get("/current_accounts?page=2").content.decode()
        assert first.count('id="current_account_') == 30
        assert "Mais antigos →" in first
        assert second.count('id="current_account_') == 1
        assert "← Mais recentes" in second

    def test_empty_list(self, signed_in):
        assert "Nenhum lançamento encontrado." in signed_in.get("/").content.decode()

    def test_legacy_search_redirects_to_the_filter(self, signed_in):
        response = signed_in.get("/search_account?date_calendar_now=2026-10-02")
        assert response.status_code == 301
        assert response["Location"] == "/current_accounts?date=2026-10-02"


class TestCrud:
    def test_creates_an_entry(self, signed_in, user):
        response = signed_in.post("/current_accounts", entry_params())
        assert response["Location"] == "/current_accounts"
        entry = user.current_accounts.get()
        assert (entry.price, entry.type_launche, entry.cost_id, entry.cash_account_id) == (Decimal("150.00"), 1, 6, 5)
        assert "Lançamento cadastrado." in signed_in.get("/").content.decode()

    def test_new_defaults_to_debit_today(self, signed_in):
        body = signed_in.get("/current_accounts/new").content.decode()
        assert 'value="debito" checked' in body

    def test_shows_validation_errors(self, signed_in, user):
        response = signed_in.post("/current_accounts", entry_params(price="", cost_id="", cash_account_id=""))
        body = response.content.decode()
        assert response.status_code == 422
        for message in [
            "Conta não está incluído na lista",
            "Categoria não está incluído na lista",
            "Valor não pode ficar em branco",
            "Valor não é um número",
        ]:
            assert message in body
        assert not user.current_accounts.exists()

    def test_shows_an_entry(self, signed_in, user):
        entry = CurrentAccountFactory(user=user, type_launche=-1, cost_id=0, price=Decimal("80"))
        body = signed_in.get(f"/current_accounts/{entry.pk}").content.decode()
        assert "Débito" in body and "Combustível" in body and "-R$ 80,00" in body

    def test_updates_an_entry(self, signed_in, user):
        entry = CurrentAccountFactory(user=user)
        response = signed_in.post(f"/current_accounts/{entry.pk}", entry_params(price="200"))
        assert response["Location"] == f"/current_accounts/{entry.pk}"
        entry.refresh_from_db()
        assert entry.price == Decimal("200")

    def test_deletes_an_entry(self, signed_in, user):
        entry = CurrentAccountFactory(user=user)
        response = signed_in.post(f"/current_accounts/{entry.pk}/destroy")
        assert response["Location"] == "/current_accounts"
        assert not CurrentAccount.objects.filter(pk=entry.pk).exists()

    def test_cannot_touch_entries_of_other_users(self, signed_in):
        other = CurrentAccountFactory(user=UserFactory())
        assert signed_in.get(f"/current_accounts/{other.pk}").status_code == 404
        assert signed_in.get(f"/current_accounts/{other.pk}/edit").status_code == 404
        assert signed_in.post(f"/current_accounts/{other.pk}", entry_params()).status_code == 404
        assert signed_in.post(f"/current_accounts/{other.pk}/destroy").status_code == 404
        assert CurrentAccount.objects.filter(pk=other.pk).exists()

    def test_requires_login(self, user):
        assert Client().post("/current_accounts", entry_params()).status_code == 302


class TestJson:
    def test_index_returns_the_same_fields_as_jbuilder(self, signed_in, user):
        entry = CurrentAccountFactory(user=user, price=Decimal("150"), historic=None)
        data = json.loads(signed_in.get("/current_accounts.json").content)
        assert data == [
            {
                "id": entry.pk,
                "cash_account_id": 0,
                "cost_id": 6,
                "date_ocurrence": entry.date_ocurrence.isoformat(),
                "price": "150.0",
                "historic": None,
                "user_id": user.pk,
                "type_launche": 1,
                "url": f"http://testserver/current_accounts/{entry.pk}.json",
            }
        ]

    def test_show(self, signed_in, user):
        entry = CurrentAccountFactory(user=user, price=Decimal("12.5"))
        data = json.loads(signed_in.get(f"/current_accounts/{entry.pk}.json").content)
        assert data["price"] == "12.5"

    def test_json_is_compact(self, signed_in, user):
        CurrentAccountFactory(user=user)
        assert b", " not in signed_in.get("/current_accounts.json").content
