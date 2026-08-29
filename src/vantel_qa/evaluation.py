import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import yaml

from vantel_qa.answerer import answer_question, extract_citations
from vantel_qa.config import Settings

REFUSAL_TEXT = "the corpus does not provide enough information to answer this question"
CORRECTNESS_WEIGHT = 0.5
CITATION_WEIGHT = 0.3
RETRIEVAL_WEIGHT = 0.2
PASS_THRESHOLD = 0.8


@dataclass(frozen=True, slots=True)
class EvalCase:
    """One golden evaluation case."""

    case_id: str
    question: str
    answerable: bool
    expected_answer: str
    required_patterns: tuple[str, ...]
    expected_citations: tuple[str, ...]
    relevant_documents: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CaseResult:
    """Scores and output for one evaluation case."""

    case_id: str
    question: str
    answer: str
    answerable: bool
    correctness: float
    citation_precision: float
    citation_recall: float
    citation_f1: float
    retrieval_recall: float
    overall_score: float
    passed: bool
    cited_documents: tuple[str, ...]
    retrieved_documents: tuple[str, ...]
    error: str | None = None


@dataclass(frozen=True, slots=True)
class EvaluationSummary:
    """Aggregate scores for one evaluation run."""

    run_id: str
    case_count: int
    passed_count: int
    correctness: float
    citation_f1: float
    retrieval_recall: float
    aggregate_score: float
    refusal_pass_rate: float


def load_cases(path: Path) -> list[EvalCase]:
    """Load golden evaluation cases from YAML."""

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(raw, dict):
        raise TypeError("Evaluation YAML must contain a mapping")

    case_items = raw.get("cases")

    if not isinstance(case_items, list):
        raise TypeError("Evaluation YAML must contain a cases list")

    return [
        EvalCase(
            case_id=str(item["id"]),
            question=str(item["question"]).strip(),
            answerable=bool(item["answerable"]),
            expected_answer=str(item["expected_answer"]).strip(),
            required_patterns=tuple(item["required_patterns"]),
            expected_citations=tuple(item["expected_citations"]),
            relevant_documents=tuple(item["relevant_documents"]),
        )
        for item in case_items
    ]


def _f1(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0

    return 2 * precision * recall / (precision + recall)


def score_case(
    case: EvalCase,
    answer: str,
    retrieved_documents: list[str],
    error: str | None = None,
) -> CaseResult:
    """Score correctness, citations, and retrieval for one answer."""

    cited = extract_citations(answer)
    expected = set(case.expected_citations)
    relevant = set(case.relevant_documents)
    allowed = expected | relevant
    retrieved = set(retrieved_documents)

    if error:
        correctness = 0.0
    elif case.answerable:
        matches = [
            bool(re.search(pattern, answer, flags=re.IGNORECASE))
            for pattern in case.required_patterns
        ]
        correctness = sum(matches) / len(matches) if matches else 1.0
    else:
        correctness = float(REFUSAL_TEXT in answer.lower())

    if cited:
        citation_precision = len(cited & allowed) / len(cited)
    else:
        citation_precision = 1.0 if not expected else 0.0

    if expected:
        citation_recall = len(cited & expected) / len(expected)
    else:
        citation_recall = 1.0

    citation_f1 = _f1(citation_precision, citation_recall)

    retrieval_recall = len(retrieved & relevant) / len(relevant) if relevant else 1.0

    overall_score = (
        CORRECTNESS_WEIGHT * correctness
        + CITATION_WEIGHT * citation_f1
        + RETRIEVAL_WEIGHT * retrieval_recall
    )

    passed = (
        error is None
        and correctness >= PASS_THRESHOLD
        and citation_f1 >= PASS_THRESHOLD
        and retrieval_recall >= PASS_THRESHOLD
    )

    return CaseResult(
        case_id=case.case_id,
        question=case.question,
        answer=answer,
        answerable=case.answerable,
        correctness=correctness,
        citation_precision=citation_precision,
        citation_recall=citation_recall,
        citation_f1=citation_f1,
        retrieval_recall=retrieval_recall,
        overall_score=overall_score,
        passed=passed,
        cited_documents=tuple(sorted(cited)),
        retrieved_documents=tuple(sorted(retrieved)),
        error=error,
    )


SCHEMA = """
CREATE TABLE IF NOT EXISTS evaluation_runs (
    run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL,
    chat_model TEXT NOT NULL,
    embedding_model TEXT NOT NULL,
    case_count INTEGER NOT NULL,
    passed_count INTEGER,
    correctness REAL,
    citation_f1 REAL,
    retrieval_recall REAL,
    aggregate_score REAL,
    refusal_pass_rate REAL
);

CREATE TABLE IF NOT EXISTS evaluation_results (
    run_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    answerable INTEGER NOT NULL,
    correctness REAL NOT NULL,
    citation_precision REAL NOT NULL,
    citation_recall REAL NOT NULL,
    citation_f1 REAL NOT NULL,
    retrieval_recall REAL NOT NULL,
    overall_score REAL NOT NULL,
    passed INTEGER NOT NULL,
    cited_documents TEXT NOT NULL,
    retrieved_documents TEXT NOT NULL,
    error TEXT,
    PRIMARY KEY (run_id, case_id),
    FOREIGN KEY (run_id) REFERENCES evaluation_runs(run_id)
);
"""


def _open_database(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.executescript(SCHEMA)
    connection.commit()
    return connection


def _save_result(
    connection: sqlite3.Connection,
    run_id: str,
    result: CaseResult,
) -> None:
    connection.execute(
        """
        INSERT INTO evaluation_results (
            run_id,
            case_id,
            question,
            answer,
            answerable,
            correctness,
            citation_precision,
            citation_recall,
            citation_f1,
            retrieval_recall,
            overall_score,
            passed,
            cited_documents,
            retrieved_documents,
            error
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            result.case_id,
            result.question,
            result.answer,
            int(result.answerable),
            result.correctness,
            result.citation_precision,
            result.citation_recall,
            result.citation_f1,
            result.retrieval_recall,
            result.overall_score,
            int(result.passed),
            json.dumps(result.cited_documents),
            json.dumps(result.retrieved_documents),
            result.error,
        ),
    )
    connection.commit()


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def run_evaluation(settings: Settings) -> EvaluationSummary:
    """Run all golden cases and persist every result."""

    cases = load_cases(settings.evaluation_cases_path)
    run_id = uuid4().hex
    started_at = datetime.now(UTC).isoformat()
    connection = _open_database(settings.evaluation_db_path)

    connection.execute(
        """
        INSERT INTO evaluation_runs (
            run_id,
            started_at,
            status,
            chat_model,
            embedding_model,
            case_count
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            started_at,
            "running",
            settings.chat_model,
            settings.embedding_model,
            len(cases),
        ),
    )
    connection.commit()

    results: list[CaseResult] = []

    for position, case in enumerate(cases, start=1):
        print(
            f"[{position}/{len(cases)}] Evaluating {case.case_id}...",
            flush=True,
        )

        try:
            answer, retrieved_chunks = answer_question(
                settings,
                case.question,
            )
            retrieved_ids = [chunk.doc_id for chunk in retrieved_chunks]
            result = score_case(
                case,
                answer,
                retrieved_ids,
            )
        except Exception as error:  # noqa: BLE001
            result = score_case(
                case,
                answer="",
                retrieved_documents=[],
                error=f"{type(error).__name__}: {error}",
            )

        results.append(result)
        _save_result(connection, run_id, result)

        outcome = "PASS" if result.passed else "FAIL"
        print(
            f"    {outcome} | correctness={result.correctness:.2f} "
            f"citations={result.citation_f1:.2f} "
            f"retrieval={result.retrieval_recall:.2f}",
            flush=True,
        )

    correctness = _mean([result.correctness for result in results])
    citation_f1 = _mean([result.citation_f1 for result in results])
    retrieval_recall = _mean([result.retrieval_recall for result in results])
    aggregate_score = _mean([result.overall_score for result in results])
    passed_count = sum(result.passed for result in results)

    refusal_results = [result for result in results if not result.answerable]
    refusal_pass_rate = _mean(
        [float(result.correctness == 1.0) for result in refusal_results]
    )

    summary = EvaluationSummary(
        run_id=run_id,
        case_count=len(results),
        passed_count=passed_count,
        correctness=correctness,
        citation_f1=citation_f1,
        retrieval_recall=retrieval_recall,
        aggregate_score=aggregate_score,
        refusal_pass_rate=refusal_pass_rate,
    )

    connection.execute(
        """
        UPDATE evaluation_runs
        SET completed_at = ?,
            status = ?,
            passed_count = ?,
            correctness = ?,
            citation_f1 = ?,
            retrieval_recall = ?,
            aggregate_score = ?,
            refusal_pass_rate = ?
        WHERE run_id = ?
        """,
        (
            datetime.now(UTC).isoformat(),
            "completed",
            summary.passed_count,
            summary.correctness,
            summary.citation_f1,
            summary.retrieval_recall,
            summary.aggregate_score,
            summary.refusal_pass_rate,
            run_id,
        ),
    )
    connection.commit()
    connection.close()

    return summary
