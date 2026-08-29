from vantel_qa.answerer import build_context, extract_citations
from vantel_qa.models import RetrievedChunk


def test_builds_context_with_source_ids() -> None:
    chunks = [
        RetrievedChunk(
            chunk_id="D003-000",
            doc_id="D003",
            title="ARR Restatement",
            content="Restated ARR was EUR 1,280,000.",
            score=0.9,
            position=0,
            date="2027-08-19",
        )
    ]

    context = build_context(chunks)

    assert "SOURCE [D003]" in context
    assert "2027-08-19" in context
    assert "EUR 1,280,000" in context


def test_extracts_unique_citations() -> None:
    answer = (
        "The original value was EUR 1.42m [D002]. "
        "It was restated to EUR 1.28m [D003]. "
        "The later memo supersedes the original [D003]."
    )

    assert extract_citations(answer) == {"D002", "D003"}


def test_extracts_grouped_citations() -> None:
    answer = "The estimate uses multiple sources [D006; D008; D024]."

    assert extract_citations(answer) == {
        "D006",
        "D008",
        "D024",
    }
