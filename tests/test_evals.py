from reconagent.services.evals import EvalCase, compute_eval_report


def test_eval_report_uses_observed_cases_not_fake_metrics():
    report = compute_eval_report(
        [
            EvalCase(True, True, True, True, True, True, True, True),
            EvalCase(True, True, False, False, False, False, False, False),
            EvalCase(False, False, True, False, True, False, True, False),
        ]
    )

    assert report["matching_precision"] == 1.0
    assert report["exception_precision"] == 1.0
    assert report["exception_recall"] == 0.5
    assert report["false_positive_rate"] == 0.0
    assert report["policy_citation_coverage"] == 0.5
    assert report["approval_required_accuracy"] == 0.6667
    assert report["case_count"] == 3
    assert report["predicted_match_count"] == 2
    assert report["predicted_exception_count"] == 1
    assert report["expected_exception_count"] == 2
