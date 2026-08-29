# Constrive - AI Engineer Take-Home

**Deadline: 48 hours after you receive it  **

## Context

`data/` contains 32 short documents from a fictional venture holding called Vantel Group.
They are the kind of thing our own ventures produce: board decks, policies, an email thread, a spreadsheet export, incident reports, specs, finance memos.
Not every document carries clean metadata, and the ones that do are not consistent about it.
Some documents disagree with each other.
Some questions cannot be answered from the corpus at all.

## What to build

A small question answering system over `data/` with an evaluation harness around it.

### 1. Retrieval and answering

- Index the documents in `data/`.
- Given a question, retrieve relevant chunks and produce an answer.
- Every factual claim in the answer must cite the document it came from by its `Dxxx` id, for example `[D005]`. Some files declare the id in frontmatter, some only in the filename.
- If the corpus does not support an answer, the system must say so instead of guessing.
- If two documents disagree, the answer must surface the disagreement rather than silently picking one.

### 2. Evaluation

- `questions.md` contains 7 questions your system must handle.
- Write your own expected answers for those 7 and add **at least 3 more of your own**, for 10 or more total.
- Build a harness that runs the whole set and produces a score per question and an aggregate.
- Decide yourself how to grade non-deterministic output and justify that choice in the README.
- At minimum report something about answer correctness and something about citation correctness.
- Frameworks like Ragas or DeepEval are fine if you can explain what their metrics actually measure. Otherwise, feel free to build your own evaluation from scratch. 


### 3. Recommendation memo, one page

Vantel Group wants to roll your system out across all four ventures as a shared internal tool.
Write a one page memo to the group operations lead, who is not an engineer, recommending whether to do that and on what terms.
We are looking for the specific constraints, numbers, and blockers that are actually in `data/` and what they mean for a rollout.

Cover at least:

- Your recommendation, in the first three sentences. Yes, no, or yes with conditions.
- What it would cost to run, and how that sits against the constraints the documents describe.
- What blocks a full portfolio rollout today, and what has to happen first.
- What you would ship first if you could only serve one venture, and why that one.
- The strongest argument against your own recommendation.

Write it for someone who will forward it to a board.

### 4. Persistence

Store the embeddings in a vector store such as ChromaDB. If you prefer another option, feel free to use that and motivate it in the README. 
Store every evaluation run in a database in a SQLite. If you want to use another cloud database, that is also fine, as long as you mention it in the README and explain why.

### 5. README

Cover:

- How to run it from scratch, in one or two commands.
- Chunking, retrieval, and model choices, and why.
- How you grade non-deterministic answers, and what that grading misses.
- What breaks first if the corpus goes from 32 documents to 20,000.
- What you would monitor if this ran in production.
- Anything you deliberately left out, and what you would do next.
- One thing about your own submission that would not survive contact with the standards described in the corpus.

## Misc

- **We provide an OpenRouter API key** with a limit of 20 dollars. Use it for both the chat model and embeddings.
- **Embeddings, if you use them, must come from one of these models.** Our zero data retention agreement covers these and not others.
  `perplexity/pplx-embed-v1-0.6b`, `openai/text-embedding-3-small`, `qwen/qwen3-embedding-8b`, `google/gemini-embedding-001`.
  Pick one and say why.
- **Suggested frameworks:** LangChain, LangGraph or Mastra. If you want to use something else, that is also fine. Just motivate it in the README.
- **Evaluation frameworks** like Ragas or DeepEval are fine if you can explain what their metrics actually measure. Otherwise, feel free to build your own evaluation from scratch.
- You are free to use any AI coding assistant you want. 

## What we are actually looking for

We are not looking for perfect results but want to hear more about your reasoning, your logic and how you took certain decisions when implementing the assignment. 

## Submitting

Create a private GitHub repository and add `filipcons` as a collaborator before the deadline.
Email filip.muntean@constrive.com when you are done.

## Deliverables

One private GitHub repository containing:

1. The question answering system: indexing, retrieval, answering with `[Dxxx]` citations, and explicit handling of unanswerable questions and conflicting documents.
2. The evaluation set: the 7 required questions plus at least 3 of your own, each with your expected answer.
3. The evaluation harness, producing a score per question and an aggregate, covering both answer correctness and citation correctness.
4. A vector store holding the embeddings, and a database holding every evaluation run, queryable across runs.
5. The one page recommendation to the group operations lead.
6. `README.md`: how to run it, design choices, grading method, scaling limits, production monitoring, what you left out, and the one thing that would not survive the corpus's own standards.

