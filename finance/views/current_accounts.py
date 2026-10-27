from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from ..auth import require_authentication
from ..models import CurrentAccount

PER_PAGE = 30
# Compact JSON, like jbuilder.
COMPACT = {"separators": (",", ":"), "ensure_ascii": False}
FIELDS = ("cash_account_id", "cost_id", "type_launche", "date_ocurrence", "price", "historic")


def _parse_date(value):
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


def _owned(request, pk):
    entry = request.current_user.current_accounts.filter(pk=pk).first()
    if entry is None:
        raise Http404
    return entry


def _as_json(request, entry):
    return {
        "id": entry.pk,
        "cash_account_id": entry.cash_account_id,
        "cost_id": entry.cost_id,
        "date_ocurrence": entry.date_ocurrence.isoformat(),
        "price": _decimal_text(entry.price),
        "historic": entry.historic,
        "user_id": entry.user_id,
        "type_launche": entry.type_launche,
        "url": request.build_absolute_uri(reverse("current_account_json", args=[entry.pk])),
    }


def _decimal_text(value):
    """Same text Rails uses for BigDecimal in JSON: 150 -> "150.0", 12.5 -> "12.5"."""
    text = format(value.normalize(), "f")
    return text if "." in text else f"{text}.0"


@require_authentication
@require_http_methods(["GET", "POST"])
def index(request, fmt=None):
    if request.method == "POST":
        return _create(request)
    day = _parse_date(request.GET.get("date"))
    scope = request.current_user.current_accounts.all()
    if day:
        scope = scope.on_date(day)
    try:
        page = max(int(request.GET.get("page", 1)), 1)
    except ValueError:
        page = 1
    rows = list(scope.ordered()[(page - 1) * PER_PAGE : page * PER_PAGE + 1])
    entries = rows[:PER_PAGE]
    if fmt == "json":
        return JsonResponse([_as_json(request, entry) for entry in entries], safe=False, json_dumps_params=COMPACT)
    return render(
        request,
        "finance/current_accounts/index.html",
        {
            "nav": "index",
            "date": day,
            "balance": scope.balance(),
            "page": page,
            "next_page": len(rows) > PER_PAGE,
            "current_accounts": entries,
        },
    )


@require_authentication
@require_http_methods(["GET", "POST"])
def show(request, pk, fmt=None):
    entry = _owned(request, pk)
    if request.method == "POST":
        return _update(request, entry)
    if fmt == "json":
        return JsonResponse(_as_json(request, entry), json_dumps_params=COMPACT)
    return render(request, "finance/current_accounts/show.html", {"current_account": entry})


def _form(request, entry, template, errors=(), status=200):
    return render(
        request,
        template,
        {
            "current_account": entry,
            "errors": errors,
            "costs": CurrentAccount.COSTS.items(),
            "cash_accounts": CurrentAccount.CASH_ACCOUNTS.items(),
        },
        status=status,
    )


@require_authentication
def new(request):
    entry = CurrentAccount(user=request.current_user, date_ocurrence=timezone.localdate(), type_launche=-1)
    return _form(request, entry, "finance/current_accounts/new.html")


@require_authentication
def edit(request, pk):
    return _form(request, _owned(request, pk), "finance/current_accounts/edit.html")


def _assign(entry, data):
    def integer(name):
        try:
            return int(data.get(f"current_account[{name}]", ""))
        except ValueError:
            return None

    entry.cash_account_id = integer("cash_account_id")
    entry.cost_id = integer("cost_id")
    entry.type_launche = CurrentAccount.TYPES.get(data.get("current_account[type_launche]"))
    entry.date_ocurrence = _parse_date(data.get("current_account[date_ocurrence]"))
    entry.price_text = data.get("current_account[price]", "").strip()
    try:
        entry.price = Decimal(entry.price_text).quantize(Decimal("0.01")) if entry.price_text else None
    except InvalidOperation:
        entry.price = None
    entry.historic = data.get("current_account[historic]") or None
    return entry.validate()


def _create(request):
    entry = CurrentAccount(user=request.current_user)
    errors = _assign(entry, request.POST)
    if errors:
        return _form(request, entry, "finance/current_accounts/new.html", errors, status=422)
    entry.save()
    messages.success(request, "Lançamento cadastrado.")
    return redirect("current_accounts")


def _update(request, entry):
    errors = _assign(entry, request.POST)
    if errors:
        return _form(request, entry, "finance/current_accounts/edit.html", errors, status=422)
    entry.save()
    messages.success(request, "Lançamento atualizado.")
    return redirect("current_account", pk=entry.pk)


@require_authentication
@require_POST
def destroy(request, pk):
    _owned(request, pk).delete()
    messages.success(request, "Lançamento removido.")
    return redirect("current_accounts")


def search_account(request):
    """Legacy daily balance search, now a filter on the listing."""
    return redirect(f"/current_accounts?date={request.GET.get('date_calendar_now', '')}", permanent=True)
