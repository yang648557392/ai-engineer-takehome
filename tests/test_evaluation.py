from vantel_qa.evaluation import EvalCase, score_case


def test_scores_supported_answer() -> None:
    case = EvalCase(
        case_id="test-1",
        question="What is the value?",
        answerable=True,
        expected_answer="The value is 100.",
        required_patterns=("100", "supersed"),
        expected_citations=("D001", "D002"),
        relevant_documents=("D001", "D002", "D003"),
    )

    result = score_case(
        case,
        answer=("The old value was 90 [D001]. It was superseded by 100 [D002]."),
        retrieved_documents=["D001", "D002", "D003"],
    )

    assert result.correctness == 1.0
    assert result.citation_f1 == 1.0
    assert result.retrieval_recall == 1.0
    assert result.passed


def test_scores_correct_refusal() -> None:
    case = EvalCase(
        case_id="test-2",
        question="What is missing?",
        answerable=False,
        expected_answer="The corpus does not provide it.",
        required_patterns=(),
        expected_citations=(),
        relevant_documents=("D010",),
    )

    result = score_case(
        case,
        answer=(
            "The corpus does not provide enough information to answer this question."
        ),
        retrieved_documents=["D010"],
    )

    assert result.correctness == 1.0
    assert result.citation_f1 == 1.0
    assert result.passed
