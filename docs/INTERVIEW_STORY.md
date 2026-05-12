# Interview Story

## Two-Minute Version

I built ReconAgent after studying AI-native finance automation companies such as Round Treasury,
Upflow, Moss, Payhawk, Pleo, Spendesk, and Mollie. The repeated backend problem is reconciliation:
finance teams need to match invoices, payments, and ledger entries, detect risky exceptions, route
approvals, and keep audit evidence.

I intentionally made the system rules-first. The matching engine owns financial truth with
deterministic scoring. AI is used only to explain exceptions and propose actions, and high-risk
actions require human approval. The architecture uses FastAPI, SQLAlchemy, PostgreSQL, Redis/RQ,
policy retrieval, optional direct LLM calls, and hash-chained audit logs.

The important decision is that this is not a chatbot. It is a finance control system where AI is
bounded by deterministic matching, permissions, and auditability.

## Five-Minute Endpoint Deep Dive

Use `POST /api/v1/reconciliation-runs`.

1. The route creates a `ReconciliationRun` with status `queued`.
2. If RQ is enabled, it enqueues the run; otherwise local dev processes it inline.
3. The service loads invoices, payments, and ledger entries.
4. The matching engine scores candidate payments by vendor, amount, date, reference, and ledger consistency.
5. The exception detector raises finance-specific issues.
6. Policy retrieval finds relevant finance policy text.
7. The action recommender proposes a bounded action.
8. Risky exceptions create pending approvals.
9. Audit events are appended with previous hash and event hash.

## Ten-Minute System Design Walkthrough

Start from the finance business problem, then explain each boundary:

- API boundary: receives CSVs and commands.
- Normalization boundary: turns messy input into canonical records.
- Persistence boundary: relational finance data.
- Matching boundary: deterministic, explainable reconciliation.
- Exception boundary: business risk rules.
- Policy boundary: retrieval over internal finance controls.
- AI boundary: explanation and recommendation only.
- Approval boundary: human permission checks.
- Audit boundary: evidence chain.
- Eval boundary: observed quality metrics.

## Active Recall

1. Say the portfolio thesis in one sentence.
2. Explain why ReconAgent is not a generic RAG app.
3. Explain the run lifecycle without looking at code.
4. Explain one failure mode and its mitigation.
