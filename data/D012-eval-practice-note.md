---
doc_id: D012
title: "How we evaluate LLM features at Vantel"
date: 2027-02-09
source_type: internal-wiki
---

# How we evaluate LLM features at Vantel

Every LLM feature that reaches production needs a golden set before launch.

## Minimum bar

- At least 30 question and answer pairs written by someone who knows the domain.
- At least 20% of the set must be questions the system should refuse or say it cannot answer.
- Scores are recorded per release and compared against the previous release.

## What we measure

- Answer correctness, graded by a model with a written rubric and spot checked by a human.
- Citation correctness, meaning every claim in the answer traces to a retrieved document.
- Retrieval recall at k, measured against the documents a human marked as relevant.

## What we do not do

We do not use a single aggregate score as a release gate.
A regression on refusal behaviour blocks a release even if the aggregate score improves.
