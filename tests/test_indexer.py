from pathlib import Path

import chromadb

from vantel_qa.chunker import chunk_documents
from vantel_qa.indexer import index_chunks
from vantel_qa.loader import load_documents

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def _fake_embedder(texts: list[str]) -> list[list[float]]:
    return [
        [
            float(len(text)),
            float(text.count("D")),
            1.0,
        ]
        for text in texts
    ]


def test_indexes_all_chunks_in_persistent_chroma(
    tmp_path: Path,
) -> None:
    documents = load_documents(DATA_DIR)
    chunks = chunk_documents(documents)
    database_path = tmp_path / "chroma"

    stats = index_chunks(
        chunks=chunks,
        persist_path=database_path,
        collection_name="test-documents",
        embedding_model="fake-embedding-model",
        embedder=_fake_embedder,
    )

    assert stats.document_count == 32
    assert stats.chunk_count == 38
    assert stats.stored_count == 38
    assert stats.vector_dimensions == 3

    client = chromadb.PersistentClient(path=str(database_path))
    collection = client.get_collection(
        name="test-documents",
        embedding_function=None,
    )

    stored = collection.get(
        ids=["D005-000"],
        include=["documents", "metadatas"],
    )

    assert stored["ids"] == ["D005-000"]
    assert "90 days" in stored["documents"][0]
    assert stored["metadatas"][0]["doc_id"] == "D005"


def test_reindexing_does_not_duplicate_chunks(
    tmp_path: Path,
) -> None:
    documents = load_documents(DATA_DIR)
    chunks = chunk_documents(documents)
    database_path = tmp_path / "chroma"

    index_chunks(
        chunks=chunks,
        persist_path=database_path,
        collection_name="test-documents",
        embedding_model="fake-embedding-model",
        embedder=_fake_embedder,
    )

    second_run = index_chunks(
        chunks=chunks,
        persist_path=database_path,
        collection_name="test-documents",
        embedding_model="fake-embedding-model",
        embedder=_fake_embedder,
        reset=False,
    )

    assert second_run.stored_count == 38
