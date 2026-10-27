"""Formatting filters matching Rails' pt-BR helpers (number_to_currency and l(date))."""

from decimal import ROUND_HALF_UP, Decimal

from django import template

register = template.Library()


@register.filter
def currency(value):
    """number_to_currency in pt-BR: "R$ 1.234,50"; negatives as "-R$ 1.234,50"."""
    amount = Decimal(value or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    sign = "-" if amount < 0 else ""
    units, cents = f"{abs(amount):.2f}".split(".")
    return f"{sign}R$ {int(units):,}".replace(",", ".") + f",{cents}"


@register.filter
def amount_class(value):
    return "text-red-700" if Decimal(value or 0) < 0 else "text-emerald-700"


@register.filter
def br_date(value):
    return value.strftime("%d/%m/%Y") if value else ""


@register.filter
def day_month(value):
    return value.strftime("%d/%m")


@register.filter
def iso(value):
    return value.isoformat() if value else ""


@register.filter
def decimal_text(value):
    """How Rails prints a BigDecimal in a form field: 150 -> "150.0"."""
    if value is None:
        return ""
    text = format(Decimal(value).normalize(), "f")
    return text if "." in text else f"{text}.0"
