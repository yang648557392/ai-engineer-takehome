"""Small OpenRouter adapter for chat and embedding API access."""

from openai import OpenAI

from vantel_qa.config import Settings


def create_openrouter_client(settings: Settings) -> OpenAI:
    """Create an OpenAI SDK client configured for OpenRouter.

    OpenRouter implements an OpenAI-compatible API, so the standard OpenAI
    client can be reused with a different base URL and API key.
    """

    return OpenAI(
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key.get_secret_value(),
        default_headers={
            "X-OpenRouter-Title": "Vantel QA Take-Home",
        },
    )


def embed_texts(
    client: OpenAI,
    texts: list[str],
    model: str,
    batch_size: int = 32,
) -> list[list[float]]:
    """Embed text in batches while preserving caller-visible order.

    Args:
        client: Configured OpenAI-compatible client.
        texts: Input strings. One embedding vector is returned per string.
        model: OpenRouter embedding model identifier.
        batch_size: Maximum number of texts sent in one API request.

    Returns:
        A two-dimensional list shaped as [number of texts][vector dimensions].
        With this project model, 38 chunk inputs produce a 38 by 1536 result.

    Raises:
        ValueError: If batch_size is not positive.
        RuntimeError: If the API returns a different number of vectors.
    """

    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    if not texts:
        return []

    vectors: list[list[float]] = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]

        response = client.embeddings.create(
            model=model,
            input=batch,
            encoding_format="float",
        )

        # API items include their original input index. Sort explicitly so
        # vector N remains aligned with text N before Chroma upsert.
        ordered_data = sorted(
            response.data,
            key=lambda item: item.index,
        )
        vectors.extend(item.embedding for item in ordered_data)

    if len(vectors) != len(texts):
        raise RuntimeError(
            "Embedding API returned a different number of vectors than input texts"
        )

    return vectors
