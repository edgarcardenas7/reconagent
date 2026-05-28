from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvalCase:
    expected_match: bool
    actual_match: bool
    expected_exception: bool
    actual_exception: bool
    expected_policy_citation: bool
    actual_policy_citation: bool
    expected_approval_required: bool
    actual_approval_required: bool


def compute_eval_report(cases: list[EvalCase]) -> dict[str, float]:
    if not cases:
        return {
            "case_count": 0,
            "predicted_match_count": 0,
            "predicted_exception_count": 0,
            "expected_exception_count": 0,
            "matching_precision": 0.0,
            "exception_precision": 0.0,
            "exception_recall": 0.0,
            "false_positive_rate": 0.0,
            "policy_citation_coverage": 0.0,
            "approval_required_accuracy": 0.0,
        }

    true_matches = sum(c.expected_match and c.actual_match for c in cases)
    predicted_matches = sum(c.actual_match for c in cases)
    true_exceptions = sum(c.expected_exception and c.actual_exception for c in cases)
    predicted_exceptions = sum(c.actual_exception for c in cases)
    expected_exceptions = sum(c.expected_exception for c in cases)
    false_positives = sum((not c.expected_exception) and c.actual_exception for c in cases)
    non_exception_cases = sum(not c.expected_exception for c in cases)
    cited = sum(c.actual_policy_citation for c in cases if c.expected_policy_citation)
    expected_citations = sum(c.expected_policy_citation for c in cases)
    approval_correct = sum(
        c.expected_approval_required == c.actual_approval_required for c in cases
    )

    return {
        "case_count": len(cases),
        "predicted_match_count": predicted_matches,
        "predicted_exception_count": predicted_exceptions,
        "expected_exception_count": expected_exceptions,
        "matching_precision": safe_div(true_matches, predicted_matches),
        "exception_precision": safe_div(true_exceptions, predicted_exceptions),
        "exception_recall": safe_div(true_exceptions, expected_exceptions),
        "false_positive_rate": safe_div(false_positives, non_exception_cases),
        "policy_citation_coverage": safe_div(cited, expected_citations),
        "approval_required_accuracy": safe_div(approval_correct, len(cases)),
    }


def safe_div(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0
