"""Split normalized source documents into deterministic retrieval units."""

import re
from collections.abc import Iterable

from vantel_qa.models import DocumentChunk, SourceDocument

DEFAULT_MAX_CHARS = 2400
DEFAULT_OVERLAP = 250

EMAIL_SEPARATOR_PATTERN = re.compile(r"(?m)^\s*--\s*$")
EMAIL_SUBJECT_PATTERN = re.compile(r"(?mi)^Subject:\s*(.+)$")


def _split_oversized_text(
    text: str,
    max_chars: int,
    overlap: int,
) -> list[str]:
    """Split text into overlapping pieces near paragraph boundaries.

    Text no longer than max_chars is returned as one piece. Longer text is
    split at the last paragraph boundary in the latter half of each window when
    possible. overlap repeats context between adjacent pieces.

    Raises:
        ValueError: If the size or overlap configuration is invalid.
    """

    if max_chars <= 0:
        raise ValueError("max_chars must be positive")

    if overlap < 0 or overlap >= max_chars:
        raise ValueError("overlap must be between 0 and max_chars")

    text = text.strip()

    if len(text) <= max_chars:
        return [text]

    pieces: list[str] = []
    start = 0

    while start < len(text):
        proposed_end = min(start + max_chars, len(text))
        end = proposed_end

        if proposed_end < len(text):
            boundary = text.rfind(
                "\n\n",
                start + max_chars // 2,
                proposed_end,
            )
            if boundary != -1:
                end = boundary

        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)

        if end >= len(text):
            break

        next_start = end - overlap
        start = next_start if next_start > start else end

    return pieces


def _email_messages(text: str) -> list[tuple[str, str]]:
    """Return (subject, message_text) pairs from one email thread."""

    messages: list[str] = []

    for part in EMAIL_SEPARATOR_PATTERN.split(text):
        cleaned_part = part.strip()

        if cleaned_part:
            messages.append(cleaned_part)

    results: list[tuple[str, str]] = []

    for index, message in enumerate(messages, start=1):
        subject_match = EMAIL_SUBJECT_PATTERN.search(message)
        subject = (
            subject_match.group(1).strip()
            if subject_match
            else f"Email message {index}"
        )
        results.append((subject, message))

    return results


def chunk_document(
    document: SourceDocument,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap: int = DEFAULT_OVERLAP,
) -> list[DocumentChunk]:
    """Convert one source document into ordered, retrievable chunks.

    Email threads are first separated into messages. Other formats remain one
    logical unit before oversized text splitting. Chunk IDs use the document ID
    and zero-padded position, making repeated indexing deterministic.
    """

    # Each unit is (optional section label, text). For email the label is the
    # message subject; for Markdown and CSV there is one unlabeled unit.
    if document.path.suffix.lower() == ".eml":
        units: list[tuple[str | None, str]] = _email_messages(document.content)
    else:
        units = [(None, document.content)]

    chunks: list[DocumentChunk] = []
    position = 0

    for section, unit_text in units:
        pieces = _split_oversized_text(
            unit_text,
            max_chars=max_chars,
            overlap=overlap,
        )

        for piece_number, piece in enumerate(pieces, start=1):
            resolved_section = section

            if len(pieces) > 1:
                label = section or "Document"
                resolved_section = f"{label}, part {piece_number}"

            chunks.append(
                DocumentChunk(
                    chunk_id=f"{document.doc_id}-{position:03d}",
                    doc_id=document.doc_id,
                    title=document.title,
                    source_type=document.source_type,
                    content=piece,
                    path=document.path,
                    position=position,
                    date=document.date,
                    section=resolved_section,
                )
            )
            position += 1

    return chunks


def chunk_documents(
    documents: Iterable[SourceDocument],
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap: int = DEFAULT_OVERLAP,
) -> list[DocumentChunk]:
    """Chunk all documents and reject duplicate Chroma record IDs.

    documents accepts any iterable, while the result is materialized as a list
    because indexing sends aligned IDs, texts, metadata, and vectors to Chroma.
    """

    chunks: list[DocumentChunk] = []

    for document in documents:
        chunks.extend(
            chunk_document(
                document,
                max_chars=max_chars,
                overlap=overlap,
            )
        )

    chunk_ids = [chunk.chunk_id for chunk in chunks]

    if len(chunk_ids) != len(set(chunk_ids)):
        raise ValueError("Duplicate chunk IDs detected")

    return chunks
