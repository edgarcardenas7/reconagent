# Evals

ReconAgent does not claim fake portfolio metrics. Metrics must come from labeled test cases.

## Implemented Metrics

- `case_count`
- `predicted_match_count`
- `predicted_exception_count`
- `expected_exception_count`
- `matching_precision`
- `exception_precision`
- `exception_recall`
- `false_positive_rate`
- `policy_citation_coverage`
- `approval_required_accuracy`

## Why These Metrics Matter

- Support counts show the denominator behind each metric. A perfect percentage on one case is not
  strong evidence.
- Matching precision shows whether the system links the right invoice/payment records.
- Exception precision shows whether raised exceptions are actually problems.
- Exception recall shows whether known problems are caught.
- False positive rate shows how often finance teams are interrupted unnecessarily.
- Policy citation coverage shows whether recommendations are backed by policy text.
- Approval accuracy shows whether risky actions are routed to humans.

## Current Limitations

- The current repository includes the metric calculation and test cases.
- It does not claim production benchmark quality or a large external golden dataset.
- A larger eval runner should add adversarial finance cases, company-specific scenarios, and
  regression snapshots before any production claim.
