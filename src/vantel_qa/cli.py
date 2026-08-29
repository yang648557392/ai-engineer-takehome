import typer
from rich.console import Console

from vantel_qa.config import get_settings
from vantel_qa.indexer import build_index

app = typer.Typer(
    help="Question answering system for the Vantel corpus.",
)
console = Console()


@app.callback()
def root() -> None:
    """Vantel QA command-line application."""


@app.command("index")
def index_command() -> None:
    """Build a fresh persistent ChromaDB index."""

    settings = get_settings()
    stats = build_index(settings, reset=True)

    console.print("[green]Index built successfully.[/green]")
    console.print(f"Documents: {stats.document_count}")
    console.print(f"Chunks: {stats.chunk_count}")
    console.print(f"Stored vectors: {stats.stored_count}")
    console.print(f"Vector dimensions: {stats.vector_dimensions}")
    console.print(f"Location: {settings.chroma_path.resolve()}")
