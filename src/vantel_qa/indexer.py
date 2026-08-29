from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import chromadb

from vantel_qa.chunker import chunk_documents
from vantel_qa.config import Settings
from vantel_qa.loader import load_documents
from vantel_qa.models import DocumentChunk
from vantel_qa.openrouter import create_openrouter_client, embed_texts

EmbeddingCallable = Callable[[list[str]], list[list[float]]]


@dataclass(frozen=True, slots=True)
class IndexStats:
    """Summary of one indexing operation."""

    document_count: int
    chunk_count: int
    stored_count: int
    vector_dimensions: int


def index_chunks(
    chunks: list[DocumentChunk],
    persist_path: Path,
    collection_name: str,
    embedding_model: str,
    embedder: EmbeddingCallable,
    *,
    reset: bool = True,
) -> IndexStats:
    """Embed chunks and persist them in ChromaDB."""

    if not chunks:
        raise ValueError("Cannot build an index without chunks")

    embedding_inputs = [chunk.embedding_text for chunk in chunks]
    vectors = embedder(embedding_inputs)

    if len(vectors) != len(chunks):
        raise RuntimeError(
            "The number of embeddings does not match the number of chunks"
        )

    dimensions = {len(vector) for vector in vectors}

    if len(dimensions) != 1 or dimensions == {0}:
        raise RuntimeError("Embedding vectors have inconsistent dimensions")

    vector_dimensions = dimensions.pop()

    persist_path.mkdir(parents=True, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=str(persist_path))

    existing_names = {
        collection.name for collection in chroma_client.list_collections()
    }

    if reset and collection_name in existing_names:
        chroma_client.delete_collection(collection_name)

    collection = chroma_client.get_or_create_collection(
        name=collection_name,
        embedding_function=None,
        metadata={
            "hnsw:space": "cosine",
            "embedding_model": embedding_model,
            "indexed_at": datetime.now(UTC).isoformat(),
        },
    )

    collection.upsert(
        ids=[chunk.chunk_id for chunk in chunks],
        embeddings=vectors,
        documents=[chunk.content for chunk in chunks],
        metadatas=[chunk.metadata for chunk in chunks],
    )

    return IndexStats(
        document_count=len({chunk.doc_id for chunk in chunks}),
        chunk_count=len(chunks),
        stored_count=collection.count(),
        vector_dimensions=vector_dimensions,
    )


def build_index(
    settings: Settings,
    *,
    reset: bool = True,
) -> IndexStats:
    """Load the corpus, create embeddings, and build the index."""

    documents = load_documents(settings.data_path)
    chunks = chunk_documents(documents)
    openrouter_client = create_openrouter_client(settings)

    def embedder(texts: list[str]) -> list[list[float]]:
        return embed_texts(
            openrouter_client,
            texts,
            settings.embedding_model,
        )

    return index_chunks(
        chunks=chunks,
        persist_path=settings.chroma_path,
        collection_name=settings.chroma_collection,
        embedding_model=settings.embedding_model,
        embedder=embedder,
        reset=reset,
    )
