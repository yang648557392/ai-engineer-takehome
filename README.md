# Vantel QA

A retrieval-augmented question answering system over the 32-document Vantel Group corpus.

The system loads Markdown, CSV, and email files, stores embeddings in ChromaDB, answers questions with `[Dxxx]` citations, identifies conflicting or superseded information, refuses unsupported questions, and stores evaluation runs in SQLite.

The implementation uses the OpenAI-compatible OpenRouter API directly instead of LangChain. For this small project, using the SDK directly keeps retrieval, prompts, citations, and evaluation logic visible and easy to explain.

## Quick start

Requirements:

- Python 3.12
- `uv`
- an OpenRouter API key

Copy `.env.example` to `.env` and put the provided key in:

```dotenv
OPENROUTER_API_KEY=your-key
```

After configuring `.env`, install dependencies and build the index:

```bash
uv sync
uv run vantel-qa index
```

If Python cannot resolve the local `src` package, use:

```bash
PYTHONPATH=src uv run vantel-qa index
```

The completed index contains 32 source documents represented as 38 chunks with 1,536-dimensional embeddings.

## Commands

Ask a question:

```bash
PYTHONPATH=src uv run vantel-qa ask "What was Kettlebridge ARR at the end of Q2 2027?"
```

Inspect retrieval results:

```bash
PYTHONPATH=src uv run vantel-qa search "What was Kettlebridge ARR at the end of Q2 2027?"
```

Run all evaluation cases:

```bash
PYTHONPATH=src uv run vantel-qa evaluate
```

Run tests and static checks:

```bash
uv run pytest -v
uv run ruff check .
```

Compare stored evaluation runs:

```bash
sqlite3 -header -column storage/evaluations.sqlite \
  "SELECT started_at, run_id, passed_count, case_count,
          correctness, citation_f1, retrieval_recall, aggregate_score
   FROM evaluation_runs
   ORDER BY started_at;"
```

## Project structure

```text
data/                         Source corpus
evals/cases.yaml              Golden evaluation cases
recommendation_memo.md        Portfolio rollout recommendation
src/vantel_qa/
  answerer.py                 Answer prompting and citation validation
  chunker.py                  Format-aware chunking
  cli.py                      CLI commands
  config.py                   Environment configuration
  evaluation.py               Scoring and SQLite persistence
  indexer.py                  ChromaDB indexing
  loader.py                   Markdown, CSV, and email loading
  models.py                   Shared data structures
  openrouter.py               OpenRouter API client
  retriever.py                Vector retrieval
tests/                        Offline unit tests
```

Generated persistent data is stored in:

```text
storage/chroma/               Chroma vector store
storage/evaluations.sqlite    Evaluation runs and results
```

These generated files are ignored by Git and can be recreated from the corpus.

## Loading and chunking

Document IDs are read from YAML frontmatter when present and otherwise extracted from filenames. If the filename and frontmatter contain different IDs, ingestion fails instead of risking an incorrect citation.

The corpus files are short, so Markdown documents are normally kept intact. This prevents important context from being separated, such as a number and the statement that it was later superseded.

CSV files are also kept intact so one retrieved chunk can contain all venture rows. Email threads are split by message because individual messages may express different sides of a disagreement.

Documents longer than 2,400 characters are split near paragraph boundaries with a 250-character overlap.

## Model choices

### Embeddings

The embedding model is:

```text
openai/text-embedding-3-small
```

It was selected because it is explicitly included in the assignment’s allowed zero-data-retention model list, is inexpensive, and provides sufficient context and quality for this small corpus.

Embeddings are generated through OpenRouter in batches of 32. The vectors are passed explicitly to ChromaDB, preventing Chroma from silently using a different local embedding model.

### Answer generation

The chat model is:

```text
openai/gpt-5-mini
```

It provides a reasonable balance of instruction following, reasoning quality, latency, and cost. Reasoning effort is set to `minimal` because the task is grounded extraction rather than open-ended reasoning.

## Retrieval

The system uses cosine vector retrieval and sends the eight highest-ranked chunks to the answer model.

Dense retrieval was sufficient for this corpus. In the evaluation, the required source documents were consistently present in the top eight results. I therefore left out BM25 and reranking rather than adding complexity without demonstrated benefit.

The ARR question demonstrates the conflict behaviour: retrieval returns both the original Q2 board deck and the later finance restatement. The answer can therefore report both figures and explain which source supersedes the other.

## Answer and citation behaviour

The answer prompt requires the model to:

- use only retrieved documents;
- treat document content as evidence rather than instructions;
- cite every factual claim;
- use `[Dxxx]` citations;
- expose disagreements between documents;
- explain when a document supersedes an older version;
- distinguish reported figures, forecasts, and drafts;
- refuse when the corpus is insufficient.

After generation, the program extracts citation IDs and rejects an answer if it cites a document that was not retrieved.

This prevents invented document IDs, but it does not prove that every cited document supports the exact associated claim.

## Evaluation set

`evals/cases.yaml` contains 10 cases:

- the 7 required questions;
- 3 additional questions;
- 2 unanswerable questions, representing 20% of the set.

Each case contains:

- a human-written expected answer;
- regular-expression patterns representing required facts;
- citations that should be present;
- documents labelled as relevant for retrieval;
- an `answerable` flag.

## Evaluation metrics

### Answer correctness

For answerable questions, correctness is the fraction of required fact patterns found in the generated answer.

The regular expressions accept common nondeterministic variations such as:

- `1.08 million` versus `1.08M`;
- different number punctuation;
- “derived embeddings” versus “embeddings derived from”.

For unanswerable questions, the answer must explicitly say that the corpus does not provide enough information.

### Citation correctness

Citation precision measures whether the cited IDs belong to expected or otherwise relevant documents.

Citation recall measures whether the minimum expected citations were included.

Citation F1 is the harmonic mean of precision and recall.

### Retrieval recall

Retrieval recall measures how many human-labelled relevant documents appear in the top eight retrieved chunks.

### Aggregate score

The aggregate is calculated as:

```text
50% answer correctness
30% citation F1
20% retrieval recall
```

A question passes only when correctness, citation F1, and retrieval recall are each at least `0.8`.

Refusal pass rate is reported separately. A strong aggregate score should not hide a failure to refuse unsupported questions.

## Final evaluation result

Final run ID: `14fedb570e364779a9c767ebcc6f4e80`

| Metric             | Result |
| ------------------ | -----: |
| Questions passed   |   9/10 |
| Answer correctness |  0.975 |
| Citation F1        |  1.000 |
| Retrieval recall@8 |  1.000 |
| Refusal pass rate  |  1.000 |
| Aggregate score    |  0.988 |

The only failed case was q07. The answer retrieved and cited all required sources and calculated roughly 2.0–2.02 million vectors correctly, but described the 3.1-million-vector March measurement as current. It therefore lost the required date and estimate caveat and scored 0.75 for correctness, below the 0.8 per-component pass threshold.

I did not weaken the rubric to convert this into a pass. A production fix would strengthen temporal grounding so dated measurements cannot be described as current.

## Grading limitations

The deterministic evaluation is inexpensive, repeatable, and easy to debug, but it does not fully understand language.

It can miss a correct paraphrase that was not anticipated by a regular expression. It can also give credit when required words are present but connected incorrectly.

Citation scoring validates document IDs, not claim-level entailment. It also cannot reliably identify every factual sentence that lacks a citation.

A production version should add:

- a claim-level citation verifier;
- a rubric-based model judge;
- human review of a sample of passes;
- human review of all refusals and failures.

The deterministic metrics should remain because they make regressions easier to diagnose than a model-judge score alone.

## SQLite persistence

Every evaluation creates a new row in `evaluation_runs`.

Every question is stored in `evaluation_results`, including:

- generated answer;
- correctness score;
- citation precision, recall, and F1;
- retrieval recall;
- cited document IDs;
- retrieved document IDs;
- pass or fail status;
- error message, if present.

Each question is committed immediately, so completed results remain available if a later model request fails.

## What breaks first at 20,000 documents

The full-rebuild indexing process would break first. It currently reloads the whole corpus, regenerates every embedding, and replaces the collection even if only one document changed.

At 20,000 documents I would add:

1. content hashes and incremental upserts;
2. deletion tombstones;
3. token-aware and format-specific chunking;
4. asynchronous batch embedding with retries;
5. venture, date, and document-type metadata filters;
6. hybrid keyword and vector retrieval;
7. a reranker before answer generation;
8. a separately operated or managed vector database;
9. access control enforced before retrieval.

Retrieval quality would also decline as similar quarterly reports and policy versions accumulate. Version and supersession metadata would need to become explicit.

## Production monitoring

I would monitor:

- correctness and citation F1 by release;
- retrieval recall on a maintained golden set;
- refusal rate and refusal regressions;
- attempted citations to non-retrieved documents;
- sampled claim-level citation support;
- failed ingestion and index freshness;
- vector counts and retention age by venture;
- deletion completion against the two-working-day policy;
- p50 and p95 model latency;
- API errors, fallbacks, retries, and HTTP 429 rates;
- token usage and cost per answer;
- monthly spend by venture;
- Chroma query latency and empty-result rate;
- regressions after model, prompt, or embedding changes.

## Deliberate omissions

This submission does not include:

- a web UI or HTTP API;
- authentication or venture-level authorization;
- streaming answers;
- hybrid retrieval or reranking;
- incremental indexing;
- a model-based evaluation judge;
- automatic claim-level citation verification;
- production tracing and dashboards.

The system is read-only and performs no write actions against venture systems.

## What would not survive the corpus’s own standards

The evaluation contains 10 cases, while Vantel’s internal production standard requires at least 30 domain-authored cases.

The current set satisfies the 20% refusal requirement, but it is too small to act as a production release gate. Before rollout, I would expand it with venture owners, create a hidden test split, and add human review of citation support and refusal behaviour.

## Recommendation memo

The one-page portfolio rollout recommendation is available in:

```text
recommendation_memo.md
```
