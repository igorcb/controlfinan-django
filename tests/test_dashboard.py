from datetime import date
from decimal import Decimal

from .factories import CurrentAccountFactory


def add(user, day, cost_id, kind, price):
    return CurrentAccountFactory(user=user, date_ocurrence=day, cost_id=cost_id, type_launche=kind, price=Decimal(price))


class TestDashboard:
    def build(self, user):
        add(user, date(2026, 9, 10), 6, 1, "500")  # rides
        add(user, date(2026, 9, 10), 0, -1, "120")  # fuel
        add(user, date(2026, 9, 11), 8, -1, "30")  # car wash
        add(user, date(2026, 9, 11), 7, -1, "50")  # phone
        add(user, date(2026, 9, 12), 3, -1, "25")  # lunch: not a ride expense
        add(user, date(2026, 10, 1), 6, 1, "999")  # next month

    def test_daily_balance_of_the_month(self, signed_in, user):
        self.build(user)
        body = signed_in.get("/dashboard?month=2026-09").content.decode()
        assert "Setembro de 2026" in body
        for text in ["12/09/2026", "-R$ 25,00", "11/09/2026", "-R$ 80,00", "10/09/2026", "R$ 380,00", "R$ 275,00"]:
            assert text in body
        assert body.index("12/09/2026") < body.index("10/09/2026")

    def test_monthly_balance_discounts_ride_expenses(self, signed_in, user):
        self.build(user)
        response = signed_in.get("/dashboard?month=2026-09")
        rows = response.context["monthly_rows"]
        assert rows == [
            ("Corridas", Decimal("500")),
            ("Combustível", Decimal("-120")),
            ("Lavagem", Decimal("-30")),
            ("Telefone", Decimal("-50")),
        ]
        assert response.context["rides_net"] == Decimal("300")

    def test_month_navigation(self, signed_in):
        body = signed_in.get("/dashboard?month=2026-01").content.decode()
        assert "?month=2025-12" in body and "?month=2026-02" in body

    def test_invalid_month_falls_back_to_the_current_one(self, signed_in):
        assert signed_in.get("/dashboard?month=lixo").status_code == 200

    def test_empty_month(self, signed_in):
        assert "Nenhum lançamento no período." in signed_in.get("/dashboard?month=2020-01").content.decode()


def test_health_check(client):
    assert client.get("/up").content == b"OK"
