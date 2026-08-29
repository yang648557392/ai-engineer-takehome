from pathlib import Path

from vantel_qa.chunker import chunk_documents
from vantel_qa.loader import load_documents

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def _load_chunks():
    documents = load_documents(DATA_DIR)
    return chunk_documents(documents)


def test_creates_deterministic_unique_chunks() -> None:
    chunks = _load_chunks()
    chunk_ids = [chunk.chunk_id for chunk in chunks]

    assert len(chunks) == 38
    assert len(chunk_ids) == len(set(chunk_ids))
    assert chunk_ids[0] == "D001-000"


def test_splits_email_threads_by_message() -> None:
    chunks = _load_chunks()
    email_chunks = [chunk for chunk in chunks if chunk.doc_id == "D008"]

    assert len(email_chunks) == 4
    assert all(chunk.content.startswith("From:") for chunk in email_chunks)
    assert any("1.1 million vectors" in chunk.content for chunk in email_chunks)
    assert any("classification separately" in chunk.content for chunk in email_chunks)


def test_keeps_small_csv_and_markdown_documents_together() -> None:
    chunks = _load_chunks()

    spend_cap_chunks = [chunk for chunk in chunks if chunk.doc_id == "D010"]
    policy_chunks = [chunk for chunk in chunks if chunk.doc_id == "D005"]

    assert len(spend_cap_chunks) == 1
    assert len(policy_chunks) == 1
    assert "Kettlebridge" in spend_cap_chunks[0].content
    assert "Marrow & Co" in spend_cap_chunks[0].content
    assert "90 days" in policy_chunks[0].content


def test_embedding_text_contains_source_context() -> None:
    chunks = _load_chunks()
    policy_chunk = next(chunk for chunk in chunks if chunk.doc_id == "D005")

    assert "Document ID: D005" in policy_chunk.embedding_text
    assert "Platform Data Retention Policy v2" in policy_chunk.embedding_text
    assert policy_chunk.metadata["doc_id"] == "D005"
    assert policy_chunk.metadata["date"] == "2027-05-20"
