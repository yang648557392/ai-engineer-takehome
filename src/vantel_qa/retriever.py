"""Turn a question into a vector and reconstruct typed Chroma matches."""

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
    """Return the most similar chunks from an opened Chroma collection.

    Args:
        collection: Collection containing indexed document chunks.
        question: One non-empty natural-language question.
        embedder: Callable returning one vector for each input string.
        top_k: Maximum results, capped at the collection size.

    Returns:
        RetrievedChunk objects ordered from nearest to farthest.

    Raises:
        ValueError: If the question is blank or top_k is not positive.
        RuntimeError: If the collection or API response is inconsistent.
    """

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

    # Chroma supports batched queries, so every field is shaped as
    # [query][match]. We sent one question and select outer index 0 before
    # zipping the parallel match fields.
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
        # Cosine distance is smaller for better matches. Convert it to a
        # larger-is-better score for display.
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
    """Open the configured index and retrieve evidence for one question.

    This wrapper owns infrastructure setup. search_collection contains the
    testable retrieval logic and accepts an injected embedder.
    """

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
