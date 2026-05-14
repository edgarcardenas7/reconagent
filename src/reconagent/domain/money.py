from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def parse_amount_to_cents(value: str | int | Decimal) -> int:
    raw_value = str(value).replace(",", "").strip()
    if not raw_value:
        raise ValueError("Money amount cannot be empty")

    try:
        amount = Decimal(raw_value)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid money amount: {value!r}") from exc

    if amount < 0:
        raise ValueError("Money amount cannot be negative")

    cents = amount * Decimal("100")
    if cents != cents.to_integral_value():
        raise ValueError("Money amount must have at most two decimal places")

    return decimal_to_cents(amount)


def decimal_to_cents(amount: Decimal, rounding: str = ROUND_HALF_UP) -> int:
    if amount < 0:
        raise ValueError("Money amount cannot be negative")

    cents = (amount * Decimal("100")).quantize(Decimal("1"), rounding=rounding)
    return int(cents)


def cents_to_decimal(cents: int) -> Decimal:
    return (Decimal(cents) / Decimal("100")).quantize(Decimal("0.01"))


def format_cents(cents: int) -> str:
    return f"{cents_to_decimal(cents):.2f}"
