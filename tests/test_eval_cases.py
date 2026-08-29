from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = PROJECT_ROOT / "evals" / "cases.yaml"


def _load_cases() -> list[dict]:
    data = yaml.safe_load(CASES_PATH.read_text(encoding="utf-8"))
    return data["cases"]


def test_contains_at_least_10_cases() -> None:
    cases = _load_cases()

    assert len(cases) >= 10
    assert len({case["id"] for case in cases}) == len(cases)


def test_contains_all_required_questions() -> None:
    cases = _load_cases()
    questions = {case["question"].strip() for case in cases}

    required_questions = {
        "What was Kettlebridge ARR at the end of Q2 2027?",
        "What is Orlo's monthly user churn rate?",
    }

    assert required_questions <= questions


def test_at_least_20_percent_require_refusal() -> None:
    cases = _load_cases()
    refusal_count = sum(not case["answerable"] for case in cases)

    assert refusal_count / len(cases) >= 0.2


def test_every_case_has_grading_fields() -> None:
    cases = _load_cases()

    for case in cases:
        assert "expected_answer" in case
        assert "required_patterns" in case
        assert "expected_citations" in case
        assert "relevant_documents" in case
