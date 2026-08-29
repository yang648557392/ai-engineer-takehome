from collections.abc import Callable

import chromadb
from chromadb.api.models.Collection import Collection

from vantel_qa.config import Settings
from vantel_qa.models import RetrievedChunk
from vantel_qa.openrouter import create_openrouter_client, embed_texts

QueryEmbedder = Callable[[list[str]], list[list[float]]]


def search_collection(
    collection: Collection,
    question: str,
    embedder: QueryEmbedder,
    top_k: int = 8,
) -> list[RetrievedChunk]:
    """Search one Chroma collection using a question embedding."""

    if not question.strip():
        raise ValueError("Question cannot be empty")

    if top_k <= 0:
        raise ValueError("top_k must be positive")

    stored_count = collection.count()

    if stored_count == 0:
        raise RuntimeError("The Chroma collection is empty")

    query_vectors = embedder([question])

    if len(query_vectors) != 1:
        raise RuntimeError("Expected exactly one query embedding")

    result = collection.query(
        query_embeddings=query_vectors,
        n_results=min(top_k, stored_count),
        include=["documents", "metadatas", "distances"],
    )

    ids = result["ids"][0]
    documents = result["documents"][0] if result["documents"] else []
    metadatas = result["metadatas"][0] if result["metadatas"] else []
    distances = result["distances"][0] if result["distances"] else []

    if not (len(ids) == len(documents) == len(metadatas) == len(distances)):
        raise RuntimeError("Chroma returned incomplete search results")

    retrieved: list[RetrievedChunk] = []

    for chunk_id, content, metadata, distance in zip(
        ids,
        documents,
        metadatas,
        distances,
        strict=True,
    ):
        retrieved.append(
            RetrievedChunk(
                chunk_id=chunk_id,
                doc_id=str(metadata["doc_id"]),
                title=str(metadata["title"]),
                content=content,
                score=1.0 - float(distance),
                position=int(metadata["position"]),
                date=(str(metadata["date"]) if "date" in metadata else None),
                section=(str(metadata["section"]) if "section" in metadata else None),
            )
        )

    return retrieved


def search_index(
    settings: Settings,
    question: str,
    top_k: int = 8,
) -> list[RetrievedChunk]:
    """Search the persistent project index."""

    chroma_client = chromadb.PersistentClient(path=str(settings.chroma_path))
    collection = chroma_client.get_collection(
        name=settings.chroma_collection,
        embedding_function=None,
    )

    openrouter_client = create_openrouter_client(settings)

    def embedder(texts: list[str]) -> list[list[float]]:
        return embed_texts(
            openrouter_client,
            texts,
            settings.embedding_model,
        )

    return search_collection(
        collection=collection,
        question=question,
        embedder=embedder,
        top_k=top_k,
    )
