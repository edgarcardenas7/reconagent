# ReconAgent

ReconAgent is a finance-operations reconciliation backend for invoice, payment, and
ledger workflows. It is intentionally scoped to the subniche of AI-native finance
automation: AP/AR reconciliation, treasury approvals, exception handling, and auditability.

The portfolio thesis is:

> Finance-ops automation companies share a repeated backend/AI bottleneck: reconciling messy
> financial records, detecting risky exceptions, routing approvals, and preserving audit evidence.

## What It Does

1. Imports invoices, payments, ledger entries, and finance policies from CSV.
2. Normalizes vendors, references, dates, currencies, and integer money amounts.
3. Runs deterministic invoice/payment/ledger matching.
4. Detects finance exceptions: duplicate payments, amount mismatches, missing POs, changed bank accounts, overdue invoices, and unmatched ledger entries.
5. Retrieves relevant finance policy text.
6. Produces an explainable proposed action with a deterministic fallback and optional direct LLM integration.
7. Requires human approval for risky actions.
8. Writes hash-chained audit events.
9. Generates eval metrics from labeled reconciliation test cases.

## Why This Is Not A Generic AI Project

ReconAgent is built around a repeated finance-ops problem shared by companies such as Round
Treasury, Upflow, Moss, Payhawk, Pleo, Spendesk, Mollie, and adjacent lending/document-risk
companies such as Crediflow.

The AI is not the source of financial truth. Deterministic matching owns truth; AI explains
exceptions and proposes actions inside approval and audit boundaries.

## Quickstart

```bash
git clone https://github.com/edgarcardenas7/reconagent.git
cd reconagent
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest
uvicorn --app-dir src reconagent.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the API.

## Demo Flow

Run these in another terminal while the API server is running:

```bash
curl -F "file=@demo/sample-data/invoices.csv" http://127.0.0.1:8000/api/v1/imports/invoices
curl -F "file=@demo/sample-data/payments.csv" http://127.0.0.1:8000/api/v1/imports/payments
curl -F "file=@demo/sample-data/ledger_entries.csv" http://127.0.0.1:8000/api/v1/imports/ledger-entries
curl -F "file=@demo/sample-data/policies.csv" http://127.0.0.1:8000/api/v1/imports/policies
curl -X POST http://127.0.0.1:8000/api/v1/reconciliation-runs
curl http://127.0.0.1:8000/api/v1/exceptions
curl http://127.0.0.1:8000/api/v1/metrics/summary
```

## Technical Docs

- `docs/PRODUCT_THESIS.md`: portfolio thesis, target company mapping, and system positioning.
- `docs/company-research.md`: finance-ops company research behind the project scope.
- `docs/job-bulletpoint-mapping.md`: mapping from common backend/AI role expectations to this repo.
- `docs/ARCHITECTURE.md`: architecture decisions and service responsibilities.
- `docs/FAILURE_MODES.md`: operational risks, mitigations, and explicit v1 gaps.
- `docs/EVALS.md`: implemented metrics and why denominators are reported next to percentages.
