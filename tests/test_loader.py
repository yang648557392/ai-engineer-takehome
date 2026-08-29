from pathlib import Path

from vantel_qa.loader import load_documents

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def test_loads_all_32_documents() -> None:
    documents = load_documents(DATA_DIR)

    assert len(documents) == 32
    assert {document.doc_id for document in documents} == {
        f"D{number:03d}" for number in range(1, 33)
    }


def test_reads_markdown_frontmatter() -> None:
    documents = load_documents(DATA_DIR)
    by_id = {document.doc_id: document for document in documents}

    policy = by_id["D005"]

    assert policy.title == "Platform Data Retention Policy v2"
    assert policy.date == "2027-05-20"
    assert policy.source_type == "policy"
    assert policy.content.startswith("# Platform Data Retention Policy v2")
    assert not policy.content.startswith("---")


def test_infers_metadata_for_csv_and_email() -> None:
    documents = load_documents(DATA_DIR)
    by_id = {document.doc_id: document for document in documents}

    assert by_id["D010"].source_type == "spreadsheet-export"
    assert by_id["D008"].source_type == "email-thread"


def test_loads_document_without_frontmatter() -> None:
    documents = load_documents(DATA_DIR)
    by_id = {document.doc_id: document for document in documents}

    procurement = by_id["D032"]

    assert procurement.title.startswith("Vantel Group")
    assert "5 million stored vectors" in procurement.content
