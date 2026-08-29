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
