from decimal import Decimal, InvalidOperation

from .errors import ValidationError

CENTS = Decimal("0.01")
MAX_AMOUNT = Decimal("1000000.00")
ZERO = Decimal("0.00")


def parse_amount(raw):
    try:
        amount = Decimal(str(raw)).quantize(CENTS)
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(f"amount '{raw}' is not a valid number")
    if amount <= ZERO:
        raise ValidationError("amount must be greater than zero")
    if amount > MAX_AMOUNT:
        raise ValidationError(f"amount must not exceed {MAX_AMOUNT}")
    return amount


def format_amount(amount):
    return f"{amount.quantize(CENTS):.2f}"
