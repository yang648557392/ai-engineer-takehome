from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SourceDocument:
    """A source file loaded from the assignment corpus."""

    doc_id: str
    title: str
    source_type: str
    content: str
    path: Path
    date: str | None = None


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    """A retrievable unit derived from a source document."""

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
        """Text sent to the embedding model."""

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
        """Scalar metadata suitable for storage in ChromaDB."""

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
    """One chunk returned by retrieval."""

    chunk_id: str
    doc_id: str
    title: str
    content: str
    score: float
    position: int
    date: str | None = None
    section: str | None = None
