# Learning Guide: Block-By-Block Mastery

Use this guide every time you study or extend ReconAgent. The goal is not to memorize code; the
goal is to explain why each boundary exists and what would break if it were designed differently.

## 1. Money Representation

**Files:** `src/reconagent/domain/money.py`, `src/reconagent/models.py`

**Architecture decision:** money is stored as integer minor units, e.g. `1000.00 EUR` becomes
`100000`.

**Rejected alternative:** `Float`. It is shorter to code, but unsafe for finance because binary
floating-point can create rounding drift.

**Code blocks to explain:**

- `parse_amount_to_cents`: converts incoming CSV strings into integer cents using `Decimal`.
- `cents_to_decimal`: converts internal cents back into human-readable decimals.
- `amount_cents` columns: every financial table persists money as an integer.

**Active recall:**

1. Why is `Decimal` used before converting to `int`?
2. What bug can happen if invoice amount and payment amount are stored as `Float`?
3. Which tables contain `amount_cents`?

**Feynman explanation:**

El sistema no guarda dinero como número decimal flotante. Primero convierte el texto del CSV con
`Decimal`, luego guarda centavos como entero. Así evita errores de redondeo en reconciliación.

**Interview sentence:**

"I store money as integer minor units because reconciliation cannot tolerate floating-point drift."

## 2. Data Model

**Files:** `src/reconagent/models.py`, `alembic/versions/0001_initial.py`

**Architecture decision:** use relational tables because finance data has clear entities and
relationships.

**Rejected alternative:** document database. It is flexible, but weaker for relational integrity
between invoices, payments, ledger entries, approvals, and audit events.

**Code blocks to explain:**

- `Vendor`: canonical vendor identity after normalization.
- `Invoice`, `Payment`, `LedgerEntry`: the three financial records being reconciled.
- `FinancePolicy`, `PolicyChunk`: source text for policy-backed explanations.
- `ReconciliationRun`: job lifecycle.
- `ReconciliationMatch`: deterministic match result.
- `ReconciliationException`: business risk produced by rules.
- `Approval`: human decision.
- `AuditEvent`: hash-chained evidence.

**Active recall:**

1. Why is vendor extracted into its own table?
2. What is the difference between a match and an exception?
3. Why are approvals separate from exceptions?

**Feynman explanation:**

Las tablas separan los datos financieros, los resultados del sistema y las decisiones humanas. Una
factura puede tener un match, ese match puede generar excepciones, y esas excepciones pueden crear
aprobaciones y auditoría.

**Interview sentence:**

"I separated matches, exceptions, approvals, and audit events so each step has a clear owner and can
be inspected independently."

## 3. CSV Ingestion And Normalization

**Files:** `src/reconagent/api/routes.py`, `src/reconagent/services/imports.py`,
`src/reconagent/domain/normalization.py`

**Architecture decision:** start with CSV ingestion before OCR/PDF.

**Rejected alternative:** OCR first. It looks impressive, but distracts from the core finance
workflow and adds noisy failure modes.

**Code blocks to explain:**

- API upload endpoint receives file bytes.
- `read_csv_bytes` converts bytes into rows.
- `normalize_*_row` validates date, currency, money, vendor, reference.
- `get_or_create_vendor` canonicalizes vendor identity.
- Import service commits records.

**Active recall:**

1. What happens before a row reaches SQLAlchemy?
2. Why is vendor normalization done during import?
3. Why does each row get a stable hash?

**Feynman explanation:**

La importación toma datos sucios de CSV y los convierte en registros consistentes. Antes de guardar,
normaliza nombres, fechas, monedas y montos para que el matching no dependa del formato original.

**Interview sentence:**

"I kept ingestion boring on purpose so the architecture demonstrates reconciliation rather than PDF
parsing."

## 4. Matching Engine

**Files:** `src/reconagent/services/matching.py`

**Architecture decision:** deterministic weighted scoring owns financial truth.

**Rejected alternative:** ask the LLM whether records match. That is harder to audit and unstable
for finance workflows.

**Code blocks to explain:**

- `find_best_match`: chooses the best payment and ledger entry for an invoice.
- `score_invoice_payment`: computes vendor, amount, date, and reference components.
- `amount_score`: exact and near-amount matching.
- `date_score`: realistic payment windows.
- `reference_score`: invoice/reference similarity.
- `find_ledger_entry`: checks accounting consistency.

**Active recall:**

1. What score threshold makes a record `matched`?
2. Why does ledger consistency add only a small number of points?
3. Which score component would catch `INV-001` inside a payment reference?

**Feynman explanation:**

El matching no adivina. Da puntos por señales concretas: mismo proveedor, mismo monto, fecha cercana,
referencia parecida y ledger consistente. Si el puntaje es suficiente, considera que hay match.

**Interview sentence:**

"The LLM does not decide matches; a deterministic scoring engine does, so the result is explainable."

## 5. Exception Rules

**Files:** `src/reconagent/services/exceptions.py`

**Architecture decision:** business-risk exceptions are explicit rules.

**Rejected alternative:** one generic `risk_score`. It hides why something is risky.

**Code blocks to explain:**

- `detect_for_invoice`: main exception orchestration.
- `missing_po`: procurement control.
- `amount_mismatch`: invoice and payment differ.
- `changed_bank_account`: fraud-sensitive vendor control.
- `overdue_invoice`: AR/AP aging risk.
- `detect_duplicate_payments`: duplicate-sized payments inside seven days.
- `detect_unmatched_ledger_entries`: accounting consistency.

**Active recall:**

1. Which exceptions are high risk?
2. Why is changed bank account high risk?
3. Why does duplicate payment detection compare same vendor, same amount, and nearby dates?

**Feynman explanation:**

Después del matching, el sistema revisa problemas financieros conocidos. No dice solo "riesgo alto";
explica qué regla falló: falta PO, cambió la cuenta, hay duplicado o el monto no cuadra.

**Interview sentence:**

"I modeled exceptions as named finance controls, not as an opaque AI risk score."

## 6. Policy Retrieval And AI Boundary

**Files:** `src/reconagent/services/embeddings.py`, `src/reconagent/services/policies.py`,
`src/reconagent/services/actions.py`

**Architecture decision:** retrieval is direct and inspectable; LLM is optional.

**Rejected alternatives:** LangChain first, or hard dependency on an external LLM. Both make the
system harder to explain and test early.

**Code blocks to explain:**

- `local_text_embedding`: deterministic local vector for testable retrieval.
- `cosine_similarity`: ranks policy chunks.
- `PolicyRetriever.retrieve`: finds relevant policy context.
- `ActionRecommender.recommend`: uses deterministic fallback unless an API key exists.
- `llm_recommendation`: direct SDK boundary with strict action set.

**Active recall:**

1. What happens if no OpenAI API key is configured?
2. Why is local deterministic embedding useful for tests?
3. What actions are allowed?

**Feynman explanation:**

El sistema busca la política más relacionada con la excepción y usa ese texto para explicar la
acción. Si no hay LLM o falla, usa reglas determinísticas para que el backend siga funcionando.

**Interview sentence:**

"The AI layer is a replaceable advisor; the backend still works with deterministic fallback."

## 7. Reconciliation Run And Worker Boundary

**Files:** `src/reconagent/services/reconciliation.py`, `src/reconagent/workers/jobs.py`

**Architecture decision:** reconciliation is a run/job with lifecycle status.

**Rejected alternative:** process everything directly inside a request with FastAPI
`BackgroundTasks`. That does not give durable status or reliable retry boundaries.

**Code blocks to explain:**

- `create_run`: writes queued run and audit event.
- `process_run`: status transition, load records, match, detect exceptions, complete/fail.
- `persist_exception`: policy retrieval, action recommendation, approval creation, audit event.
- `enqueue_reconciliation_run`: RQ path in production, inline path in local tests/dev.

**Active recall:**

1. What are the run statuses?
2. What happens if processing raises an exception?
3. Why is the inline path useful locally?

**Feynman explanation:**

Una reconciliación puede tardar o fallar, así que se modela como job. El sistema sabe si está queued,
processing, completed o failed, y deja auditoría de cada transición.

**Interview sentence:**

"I modeled reconciliation as a job because finance workflows need status, retries, and failure
evidence."

## 8. Approvals And Audit

**Files:** `src/reconagent/services/auth.py`, `src/reconagent/services/approvals.py`,
`src/reconagent/services/audit.py`

**Architecture decision:** high-risk financial decisions require human permission and immutable-ish
audit evidence.

**Rejected alternative:** let the AI auto-approve all recommendations.

**Code blocks to explain:**

- `DEMO_USERS`: simple v1 auth model.
- `can_decide`: role-based approval permission.
- `ApprovalService.decide`: validates pending state, permission, decision, audit.
- `compute_event_hash`: chains each event to the previous hash.

**Active recall:**

1. Why can an analyst not approve high-risk actions?
2. What fields are used to compute an audit hash?
3. What would reveal tampering with a previous audit event?

**Feynman explanation:**

La IA puede recomendar, pero las decisiones de riesgo requieren humano. Cada decisión se registra
con un hash que depende del evento anterior; si alguien cambia el historial, la cadena deja de
cuadrar.

**Interview sentence:**

"The system prevents silent AI execution by separating recommendation, permissioned approval, and
audit evidence."

## 9. Evals

**Files:** `src/reconagent/services/evals.py`, `tests/test_evals.py`

**Architecture decision:** metrics must come from labeled cases, not claims in the README.

**Rejected alternative:** invent portfolio metrics like "98.5% precision."

**Code blocks to explain:**

- `EvalCase`: one labeled scenario.
- `compute_eval_report`: calculates matching precision, exception precision/recall, false positive
  rate, citation coverage, approval accuracy, and support counts.

**Active recall:**

1. Why is exception recall important?
2. Why does false positive rate matter to finance teams?
3. Why should every percentage metric include a denominator such as `case_count`?
4. What metric tells us policy context was actually attached?

**Feynman explanation:**

Los evals comparan lo que el sistema hizo contra casos esperados. Así puedes decir "esta métrica
salió de estos casos y con este denominador", no "me inventé un número para el portafolio."

**Interview sentence:**

"I report eval percentages with support counts, because a metric without a denominator is not defensible."
