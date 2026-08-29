import typer
from rich.console import Console

from vantel_qa.answerer import answer_question
from vantel_qa.config import get_settings
from vantel_qa.evaluation import run_evaluation
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


@app.command("evaluate")
def evaluate_command() -> None:
    """Run the golden evaluation set and save results."""

    settings = get_settings()
    summary = run_evaluation(settings)

    console.rule("Evaluation summary")
    console.print(f"Run ID: {summary.run_id}")
    console.print(f"Passed: {summary.passed_count}/{summary.case_count}")
    console.print(f"Correctness: {summary.correctness:.3f}")
    console.print(f"Citation F1: {summary.citation_f1:.3f}")
    console.print(f"Retrieval recall: {summary.retrieval_recall:.3f}")
    console.print(f"Refusal pass rate: {summary.refusal_pass_rate:.3f}")
    console.print(f"Aggregate score: {summary.aggregate_score:.3f}")
    console.print(f"Database: {settings.evaluation_db_path.resolve()}")
