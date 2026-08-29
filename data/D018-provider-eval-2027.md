---
doc_id: D018
title: "Platform - Provider Evaluation Summary 2027"
date: 2027-04-02
source_type: internal-wiki
---

# Platform - Provider Evaluation Summary 2027

The platform team ran a bake off across three providers for the `summarise-long` route.

## Method

We used 120 shipment threads from Kettlebridge with human written reference summaries.
Each provider was scored on correctness, citation validity, and cost per thousand summaries.

## Result

The chosen primary model won on citation validity by a wide margin and lost on raw cost.
The fallback model is roughly 40% cheaper and slightly worse on correctness.
Cost per thousand summaries on the primary model was EUR 62.

We deliberately did not pick on cost alone because bad citations create support load that costs more than the inference.
