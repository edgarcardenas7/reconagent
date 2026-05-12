# ReconAgent

ReconAgent is a finance-operations reconciliation backend for invoice, payment, and
ledger workflows. It is intentionally scoped to the subniche of AI-native finance
automation: AP/AR reconciliation, treasury approvals, exception handling, and auditability.

The portfolio thesis is:

> I studied finance-ops automation companies, found the repeated backend/AI bottleneck, and
> built a focused reconciliation system that maps directly to their product and hiring needs.

## What It Does

1. Imports invoices, payments, ledger entries, and finance policies from CSV.
2. Normalizes vendors, references, dates, currencies, and integer money amounts.
3. Runs deterministic invoice/payment/ledger matching.
4. Detects finance exceptions: duplicate payments, amount mismatches, missing POs, changed bank accounts, overdue invoices, and unmatched ledger entries.
5. Retrieves relevant finance policy text.
6. Produces an explainable proposed action with a deterministic fallback and optional direct LLM integration.
7. Requires human approval for risky actions.
8. Writes hash-chained audit events.
9. Generates eval metrics from golden reconciliation cases.

## Why This Is Not A Generic AI Project

ReconAgent is built around a repeated finance-ops problem shared by companies such as Round
Treasury, Upflow, Moss, Payhawk, Pleo, Spendesk, Mollie, and adjacent lending/document-risk
companies such as Crediflow.

The AI is not the source of financial truth. Deterministic matching owns truth; AI explains
exceptions and proposes actions inside approval and audit boundaries.

## Quickstart

```bash
cd reconagent
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
uvicorn --app-dir src reconagent.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the API.

## Demo Flow

```bash
curl -F "file=@demo/sample-data/invoices.csv" http://127.0.0.1:8000/api/v1/imports/invoices
curl -F "file=@demo/sample-data/payments.csv" http://127.0.0.1:8000/api/v1/imports/payments
curl -F "file=@demo/sample-data/ledger_entries.csv" http://127.0.0.1:8000/api/v1/imports/ledger-entries
curl -F "file=@demo/sample-data/policies.csv" http://127.0.0.1:8000/api/v1/imports/policies
curl -X POST http://127.0.0.1:8000/api/v1/reconciliation-runs
```

## Architecture Learning Path

Read these in order:

1. `docs/company-research.md`
2. `docs/job-bulletpoint-mapping.md`
3. `docs/ARCHITECTURE.md`
4. `docs/FAILURE_MODES.md`
5. `docs/EVALS.md`
6. `docs/LEARNING_GUIDE.md`
7. `docs/INTERVIEW_STORY.md`

Each doc includes active recall and Feynman prompts so the architecture can be defended in
interviews instead of treated as AI-generated code.
