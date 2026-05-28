# Failure Modes

## LLM Timeout Or Bad Output

- **Risk:** The LLM does not respond or returns invalid JSON.
- **Mitigation:** `ActionRecommender` catches failures and uses deterministic fallback actions.
- **Design point:** External AI services are treated as unreliable dependencies.

## Duplicate Payment Approved By Mistake

- **Risk:** A duplicate payment is incorrectly released.
- **Mitigation:** duplicate payment exceptions require approval and are written to audit logs.
- **Remaining gap:** v1 does not execute real payments; payment execution is intentionally out of scope.

## False Positive Exception

- **Risk:** Normal payment is held for review.
- **Mitigation:** users can reject approvals; evals track false positive rate.

## Changed Bank Account

- **Risk:** fraud via vendor bank account change.
- **Mitigation:** changed bank accounts escalate to controller and cannot be silently approved by AI.

## Worker Failure

- **Risk:** reconciliation job fails mid-run.
- **Mitigation:** run status becomes `failed`, error is stored, audit event is appended.

## Missing Policy Data

- **Risk:** no finance policy has been imported.
- **Mitigation:** policy retrieval returns an explicit fallback citation and deterministic rules still run.
