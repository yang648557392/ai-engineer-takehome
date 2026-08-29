import re
from pathlib import Path
from typing import Any

import yaml

from vantel_qa.models import SourceDocument

SUPPORTED_SUFFIXES = {".md", ".csv", ".eml"}
DOC_ID_PATTERN = re.compile(r"\b(D\d{3})\b")

DEFAULT_SOURCE_TYPES = {
    ".md": "markdown",
    ".csv": "spreadsheet-export",
    ".eml": "email-thread",
}


def _read_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Separate YAML frontmatter from a Markdown document."""

    lines = text.splitlines(keepends=True)

    if not lines or lines[0].strip() != "---":
        return {}, text

    closing_index = next(
        (
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        ),
        None,
    )

    if closing_index is None:
        raise ValueError("YAML frontmatter has no closing delimiter")

    header = "".join(lines[1:closing_index])
    body = "".join(lines[closing_index + 1 :]).lstrip()

    metadata = yaml.safe_load(header) or {}

    if not isinstance(metadata, dict):
        raise TypeError("YAML frontmatter must contain a mapping")

    return metadata, body


def _extract_filename_id(path: Path) -> str | None:
    match = DOC_ID_PATTERN.search(path.name)
    return match.group(1) if match else None


def _infer_title(path: Path, content: str) -> str:
    """Infer a readable title when frontmatter does not provide one."""

    if path.suffix.lower() == ".md":
        heading = re.search(r"^#\s+(.+)$", content, flags=re.MULTILINE)
        if heading:
            return heading.group(1).strip()

        first_line = next(
            (line.strip() for line in content.splitlines() if line.strip()),
            None,
        )
        if first_line:
            return first_line

    return path.stem.replace("-", " ")


def load_document(path: Path) -> SourceDocument:
    """Load one supported corpus file."""

    suffix = path.suffix.lower()

    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(f"Unsupported file type: {path}")

    raw_text = path.read_text(encoding="utf-8")

    if suffix == ".md":
        metadata, content = _read_frontmatter(raw_text)
    else:
        metadata, content = {}, raw_text

    filename_id = _extract_filename_id(path)
    metadata_id = metadata.get("doc_id")
    metadata_id = str(metadata_id) if metadata_id is not None else None

    if filename_id and metadata_id and filename_id != metadata_id:
        raise ValueError(
            f"Document ID mismatch in {path}: "
            f"filename={filename_id}, frontmatter={metadata_id}"
        )

    doc_id = metadata_id or filename_id

    if doc_id is None:
        raise ValueError(f"Could not determine document ID for {path}")

    if not re.fullmatch(r"D\d{3}", doc_id):
        raise ValueError(f"Invalid document ID {doc_id!r} in {path}")

    title_value = metadata.get("title")
    title = (
        str(title_value)
        if title_value is not None
        else _infer_title(path, content)
    )

    source_type_value = metadata.get("source_type")
    source_type = (
        str(source_type_value)
        if source_type_value is not None
        else DEFAULT_SOURCE_TYPES[suffix]
    )

    date_value = metadata.get("date")
    date = str(date_value) if date_value is not None else None

    return SourceDocument(
        doc_id=doc_id,
        title=title,
        source_type=source_type,
        content=content.strip(),
        path=path,
        date=date,
    )


def load_documents(data_dir: Path) -> list[SourceDocument]:
    """Load every supported document in deterministic order."""

    if not data_dir.is_dir():
        raise FileNotFoundError(f"Data directory does not exist: {data_dir}")

    paths = sorted(
        path
        for path in data_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    )

    documents = [load_document(path) for path in paths]

    seen_ids: set[str] = set()
    duplicate_ids: set[str] = set()

    for document in documents:
        if document.doc_id in seen_ids:
            duplicate_ids.add(document.doc_id)
        seen_ids.add(document.doc_id)

    if duplicate_ids:
        duplicates = ", ".join(sorted(duplicate_ids))
        raise ValueError(f"Duplicate document IDs: {duplicates}")

    return documents