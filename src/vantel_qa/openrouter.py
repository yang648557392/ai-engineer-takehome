from openai import OpenAI

from vantel_qa.config import Settings


def create_openrouter_client(settings: Settings) -> OpenAI:
    """Create an OpenAI-compatible client pointed at OpenRouter."""

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
    """Generate embeddings while preserving input order."""

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
