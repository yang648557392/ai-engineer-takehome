# Vantel QA

Vantel QA is a small retrieval-augmented generation (RAG) system. It answers
questions about 32 Vantel Group documents.

The system finds relevant text, sends it to a chat model, and adds source IDs
such as [D005]. It reports conflicts between documents. It refuses to answer
when the documents do not contain enough information.

## Quick Start

You need Python 3.12, uv, and an OpenRouter API key.

Copy the example environment file:

~~~bash
cp .env.example .env
~~~

Add the provided key to .env:

~~~dotenv
OPENROUTER_API_KEY=your-key
~~~

Install the project and build the index:

~~~bash
uv sync
PYTHONPATH=src uv run vantel-qa index
~~~

The finished index has 32 documents, 38 chunks, and 1,536 values in each
embedding vector.

## Commands

Search for relevant text without asking the chat model:

~~~bash
PYTHONPATH=src uv run vantel-qa search "What was Kettlebridge ARR at the end of Q2 2027?"
~~~

Generate an answer:

~~~bash
PYTHONPATH=src uv run vantel-qa ask "What was Kettlebridge ARR at the end of Q2 2027?"
~~~

Run all 10 evaluation cases:

~~~bash
PYTHONPATH=src uv run vantel-qa evaluate
~~~

Run tests and code checks:

~~~bash
uv run pytest -v
uv run ruff check .
~~~

## How It Works

1. loader.py reads Markdown, CSV, and email files.
2. chunker.py turns each document into one or more chunks.
3. openrouter.py creates an embedding vector for every chunk.
4. indexer.py stores the text, metadata, and vectors in ChromaDB.
5. retriever.py embeds a question and returns the eight closest chunks.
6. answerer.py gives those chunks to the chat model.
7. The answer must contain Dxxx citations.

Document IDs come from YAML frontmatter or filenames. The loader stops if the
two IDs disagree.

Small Markdown and CSV files stay together. Email threads are split by message.
Long text is split near paragraph boundaries at 2,400 characters, with a
250-character overlap. This keeps useful context while limiting chunk size.

The embedding model is openai/text-embedding-3-small. It is on the assignment's
zero-data-retention list. It is also low cost and good enough for this small
corpus.

The chat model is openai/gpt-5-mini. It gives a good balance of quality, speed,
and cost. The project calls OpenRouter through the OpenAI SDK. It does not use
LangChain. Direct SDK calls keep the retrieval and prompt logic easy to inspect.

Chroma uses cosine distance. The system returns the top eight chunks. This was
enough for the current evaluation, so I did not add keyword search or a
reranker.

The system prompt tells the model to use only retrieved sources. It must explain
conflicts and newer documents that replace older ones. After generation, the
code rejects citations to documents that were not retrieved.

See [docs/data-flow.md](docs/data-flow.md) for concrete data shapes.

## Persistence

Chroma data is stored in storage/chroma. It contains document chunks,
metadata, and embeddings.

Evaluation runs are stored in storage/evaluations.sqlite. One table stores each
run. A second table stores the result for every question. Generated storage
files are ignored by Git and can be rebuilt.

## Evaluation

evals/cases.yaml contains:

- the 7 required questions;
- 3 extra questions;
- 2 refusal questions.

Each case has a human-written expected answer, required answer patterns,
expected citations, and relevant documents.

The evaluator reports:

- correctness: how many required answer patterns were found;
- citation F1: whether the answer used the expected source IDs;
- retrieval recall: whether Chroma found the human-labelled documents;
- refusal pass rate: whether unsupported questions were refused.

The aggregate score uses 50% correctness, 30% citation F1, and 20% retrieval
recall. A case passes only if every main score is at least 0.8.

The recorded final run produced:

| Metric | Result |
| --- | ---: |
| Passed | 9/10 |
| Correctness | 0.975 |
| Citation F1 | 1.000 |
| Retrieval recall@8 | 1.000 |
| Refusal pass rate | 1.000 |
| Aggregate score | 0.988 |

Case q07 failed because the answer used a March vector count as if it were
current. The number was close, but the answer missed the time warning.

This grading method is cheap and repeatable, but it does not fully understand
language. A correct paraphrase can fail a regular expression. A wrong sentence
can also contain the expected words. Citation scoring checks source IDs, but it
does not prove that each source supports the exact claim.

## Scaling to 20,000 Documents

Full indexing would break first. The current system embeds every document again
and replaces the collection.

For 20,000 documents, I would add content hashes, incremental updates, deletion
tracking, token-based chunking, metadata filters, keyword search, a reranker,
and access control. I would also use a separately managed vector database.

## Production Monitoring

I would monitor:

- answer and citation quality;
- retrieval recall on a fixed test set;
- refusal errors;
- index age and vector count;
- API errors and empty results;
- response time and cost;
- changes after a model, prompt, or index update.

## Limitations and Next Steps

This project does not include a web UI, login, venture-level permissions,
streaming, hybrid search, reranking, incremental indexing, or claim-level
citation checking.

The next step would be stronger citation checking and a small internal pilot.

## Main Weakness

Vantel's own standard requires at least 30 cases written by domain experts.
This submission has only 10. It is enough for a take-home test, but not for a
production release.

## Recommendation Memo

The rollout recommendation is in
[recommendation_memo.md](recommendation_memo.md).
