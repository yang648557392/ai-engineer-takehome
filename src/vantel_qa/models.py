"""Typed data contracts passed between the Vantel QA pipeline stages."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SourceDocument:
    """One complete source file after ingestion.

    Attributes:
        doc_id: Stable citation identifier such as 'D003'.
        title: Human-readable title read from metadata or inferred from the file.
        source_type: Normalized format label such as 'markdown' or
            'email-thread'.
        content: File body after Markdown frontmatter has been removed.
        path: Location of the source file on disk.
        date: Optional source date converted to text for consistent metadata.

    This object is produced by loader.py and consumed by chunker.py.
    """

    doc_id: str
    title: str
    source_type: str
    content: str
    path: Path
    date: str | None = None


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    """One retrievable piece derived from a SourceDocument.

    doc_id is shared by every chunk from the same source, while chunk_id
    identifies one exact piece. For example, chunks from D003 receive IDs such
    as D003-000 and D003-001.

    Attributes:
        chunk_id: Stable Chroma record ID.
        doc_id: Source-level citation ID shown to users.
        title: Source document title.
        source_type: Normalized source format.
        content: Text stored as the Chroma document and sent to the chat model.
        path: Original source path.
        position: Zero-based chunk number inside the source document.
        date: Optional source date.
        section: Optional heading or email subject associated with this chunk.
    """

    chunk_id: str
    doc_id: str
    title: str
    source_type: str
    content: str
    path: Path
    position: int
    date: str | None = None
    section: str | None = None

    @property
    def embedding_text(self) -> str:
        """Return the text sent to the embedding model.

        Document identity and section context are prepended to the body so that
        similar chunks from different ventures remain distinguishable.
        """

        lines = [
            f"Document ID: {self.doc_id}",
            f"Title: {self.title}",
        ]

        if self.date:
            lines.append(f"Date: {self.date}")

        if self.section:
            lines.append(f"Section: {self.section}")

        lines.append(self.content)
        return "\n".join(lines)

    @property
    def metadata(self) -> dict[str, str | int]:
        """Return scalar metadata stored beside this chunk in ChromaDB.

        Chroma metadata values must be scalar values, so Path is converted to
        str and optional fields are omitted rather than stored as None. The
        chunk ID is separate because collection.upsert receives it via ids.
        """

        result: dict[str, str | int] = {
            "doc_id": self.doc_id,
            "title": self.title,
            "source_type": self.source_type,
            "path": str(self.path),
            "position": self.position,
        }

        if self.date:
            result["date"] = self.date

        if self.section:
            result["section"] = self.section

        return result


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    """A document chunk reconstructed from one Chroma search match.

    It contains the fields needed by answer generation plus score, where a
    larger value means the chunk is more similar to the question.
    """

    chunk_id: str
    doc_id: str
    title: str
    content: str
    score: float
    position: int
    date: str | None = None
    section: str | None = None
