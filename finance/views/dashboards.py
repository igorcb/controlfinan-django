from datetime import datetime

from django.shortcuts import render
from django.utils import timezone

from ..auth import require_authentication
from ..models import CurrentAccount

MONTHS = [
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
]


def _shift(month, delta):
    index = month.month - 1 + delta
    return month.replace(year=month.year + index // 12, month=index % 12 + 1, day=1)


@require_authentication
def show(request):
    try:
        month = datetime.strptime(request.GET.get("month", ""), "%Y-%m").date()
    except ValueError:
        month = timezone.localdate().replace(day=1)
    month_accounts = request.current_user.current_accounts.in_month(month)

    balance_by_day = month_accounts.balance_by_day()
    month_balance = sum(balance_by_day.values())
    ride_expenses = month_accounts.total_by_cost(CurrentAccount.RIDE_EXPENSES.keys())
    rides_balance = month_accounts.rides().balance()
    rides_net = rides_balance - sum(ride_expenses.values())

    monthly_rows = [("Corridas", rides_balance)] + [
        (name, -ride_expenses.get(cost_id, 0)) for cost_id, name in CurrentAccount.RIDE_EXPENSES.items()
    ]
    label = f"{MONTHS[month.month - 1]} de {month.year}"
    return render(
        request,
        "finance/dashboards/show.html",
        {
            "nav": "dashboard",
            "tab_labels": ["Saldo Diário", "Saldo Mensal"],
            "month_label": label[0].upper() + label[1:],
            "previous_month": _shift(month, -1).strftime("%Y-%m"),
            "next_month": _shift(month, 1).strftime("%Y-%m"),
            "today": timezone.localdate(),
            "daily_rows": [(day.strftime("%d/%m/%Y"), amount) for day, amount in balance_by_day.items()],
            "month_balance": month_balance,
            "monthly_rows": monthly_rows,
            "rides_net": rides_net,
        },
    )
