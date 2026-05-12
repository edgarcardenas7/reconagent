from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def parse_amount_to_cents(value: str | int | Decimal) -> int:
    try:
        amount = Decimal(str(value).replace(",", "").strip())
    except InvalidOperation as exc:
        raise ValueError(f"Invalid money amount: {value!r}") from exc

    cents = (amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(cents)


def cents_to_decimal(cents: int) -> Decimal:
    return (Decimal(cents) / Decimal("100")).quantize(Decimal("0.01"))
