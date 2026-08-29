import typer
from rich.console import Console

from vantel_qa.answerer import answer_question
from vantel_qa.config import get_settings
from vantel_qa.indexer import build_index
from vantel_qa.retriever import search_index

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


@app.command("search")
def search_command(question: str) -> None:
    """Show the chunks most relevant to a question."""

    settings = get_settings()
    results = search_index(settings, question)

    for rank, result in enumerate(results, start=1):
        console.rule(
            f"{rank}. [{result.doc_id}] {result.title} — score {result.score:.3f}"
        )
        console.print(result.content)


@app.command("ask")
def ask_command(question: str) -> None:
    """Answer a question using the indexed corpus."""

    settings = get_settings()
    answer, retrieved = answer_question(settings, question)

    console.rule("Answer")
    console.print(answer)

    retrieved_ids = sorted({chunk.doc_id for chunk in retrieved})
    console.print(
        f"\nRetrieved: {', '.join(retrieved_ids)}",
        style="dim",
    )
