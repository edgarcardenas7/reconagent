# Evals

ReconAgent does not claim fake portfolio metrics. Metrics must come from labeled test cases.

## Implemented Metrics

- `matching_precision`
- `exception_precision`
- `exception_recall`
- `false_positive_rate`
- `policy_citation_coverage`
- `approval_required_accuracy`

## Why These Metrics Matter

- Matching precision shows whether the system links the right invoice/payment records.
- Exception precision shows whether raised exceptions are actually problems.
- Exception recall shows whether known problems are caught.
- False positive rate shows how often finance teams are interrupted unnecessarily.
- Policy citation coverage shows whether recommendations are backed by policy text.
- Approval accuracy shows whether risky actions are routed to humans.

## Active Recall

1. Why is false positive rate important for finance teams?
2. Why is recall important for fraud-like exceptions?
3. Which metric proves the system is not inventing policy context?
