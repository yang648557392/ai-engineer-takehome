from pathlib import Path

import chromadb

from vantel_qa.retriever import search_collection


def test_returns_chunks_in_similarity_order(tmp_path: Path) -> None:
    client = chromadb.PersistentClient(path=str(tmp_path / "chroma"))
    collection = client.get_or_create_collection(
        name="test-search",
        embedding_function=None,
        metadata={"hnsw:space": "cosine"},
    )

    collection.add(
        ids=["D001-000", "D002-000", "D003-000"],
        embeddings=[
            [1.0, 0.0],
            [0.8, 0.2],
            [0.0, 1.0],
        ],
        documents=[
            "First document",
            "Second document",
            "Third document",
        ],
        metadatas=[
            {
                "doc_id": "D001",
                "title": "First",
                "position": 0,
            },
            {
                "doc_id": "D002",
                "title": "Second",
                "position": 0,
            },
            {
                "doc_id": "D003",
                "title": "Third",
                "position": 0,
            },
        ],
    )

    def fake_embedder(texts: list[str]) -> list[list[float]]:
        assert len(texts) == 1
        return [[1.0, 0.0]]

    results = search_collection(
        collection=collection,
        question="Find the first document",
        embedder=fake_embedder,
        top_k=2,
    )

    assert [result.chunk_id for result in results] == [
        "D001-000",
        "D002-000",
    ]
    assert results[0].score > results[1].score
