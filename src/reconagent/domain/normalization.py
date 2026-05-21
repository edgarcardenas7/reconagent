from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import date
from io import StringIO

from reconagent.domain.money import parse_amount_to_cents


def normalize_name(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_reference(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.strip().lower())


def normalize_currency(value: str) -> str:
    currency = value.strip().upper()
    if len(currency) != 3 or not currency.isalpha():
        raise ValueError(f"Currency must be ISO-4217 style code, got {value!r}")
    return currency


def parse_iso_date(value: str) -> date:
    return date.fromisoformat(value.strip())


def stable_row_hash(row: dict[str, str]) -> str:
    payload = json.dumps(row, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_csv_bytes(content: bytes) -> list[dict[str, str]]:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(StringIO(text))
    return [{k: (v or "").strip() for k, v in row.items()} for row in reader]


def normalize_invoice_row(row: dict[str, str]) -> dict:
    return {
        "vendor_name": row["vendor_name"].strip(),
        "normalized_vendor_name": normalize_name(row["vendor_name"]),
        "invoice_number": row["invoice_number"].strip(),
        "amount_cents": parse_amount_to_cents(row["amount"]),
        "currency": normalize_currency(row["currency"]),
        "invoice_date": parse_iso_date(row["invoice_date"]),
        "due_date": parse_iso_date(row["due_date"]),
        "po_number": row.get("po_number", "").strip() or None,
        "bank_account": row.get("bank_account", "").strip() or None,
        "source_hash": stable_row_hash(row),
        "raw_payload": json.dumps(row, sort_keys=True),
    }


def normalize_payment_row(row: dict[str, str]) -> dict:
    return {
        "vendor_name": row["vendor_name"].strip(),
        "normalized_vendor_name": normalize_name(row["vendor_name"]),
        "amount_cents": parse_amount_to_cents(row["amount"]),
        "currency": normalize_currency(row["currency"]),
        "payment_date": parse_iso_date(row["payment_date"]),
        "bank_account": row["bank_account"].strip(),
        "reference": row["reference"].strip(),
        "source_hash": stable_row_hash(row),
        "raw_payload": json.dumps(row, sort_keys=True),
    }


def normalize_ledger_row(row: dict[str, str]) -> dict:
    return {
        "vendor_name": row["vendor_name"].strip(),
        "normalized_vendor_name": normalize_name(row["vendor_name"]),
        "amount_cents": parse_amount_to_cents(row["amount"]),
        "currency": normalize_currency(row["currency"]),
        "entry_date": parse_iso_date(row["entry_date"]),
        "account_code": row["account_code"].strip(),
        "description": row["description"].strip(),
        "reference": row["reference"].strip(),
        "source_hash": stable_row_hash(row),
        "raw_payload": json.dumps(row, sort_keys=True),
    }
