# Job Bullet Point Mapping

## "Build AI-powered product features end-to-end"

ReconAgent implements the full path from CSV ingestion to reconciliation run, exceptions, policy
context, proposed action, approval, and audit event.

## "Design backend services and scalable architecture"

The backend is split into API routes, domain normalization, deterministic matching, policy
retrieval, approval services, audit services, workers, and evals. RQ is used for background work
because reconciliation is a job with status, retries, and failure modes.

## "Work with financial data"

The data model includes vendors, invoices, payments, ledger entries, finance policies, matches,
exceptions, approvals, and audit events. Money is stored as integer cents to avoid floating-point
rounding errors.

## "Integrate LLM APIs and retrieval pipelines"

Policy retrieval is implemented as a direct, inspectable retrieval service. The LLM integration is
optional and direct; when no API key exists, deterministic fallback recommendations are used.

## "Build agents beyond simple wrappers"

The agentic part is constrained: the system recommends actions, but financial truth remains in
matching rules and approvals. High-risk actions require a controller or CFO actor.

## "Care about reliability and observability"

ReconAgent uses reconciliation run statuses, deterministic fallbacks, failure-mode docs, evals, and
hash-chained audit events.

## Interview Sentence

"I intentionally made the AI advisory rather than authoritative: deterministic matching owns
financial truth, while the AI explains exceptions and proposes actions inside approval and audit
boundaries."
