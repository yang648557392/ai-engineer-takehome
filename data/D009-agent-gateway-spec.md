---
doc_id: D009
title: "Internal Agent Gateway - Specification"
date: 2027-04-30
source_type: spec
---

# Internal Agent Gateway - Specification

The agent gateway is the single egress point for all venture calls to LLM providers.

## Responsibilities

- Route requests to a provider based on a per route configuration.
- Enforce per venture monthly spend caps.
- Log every request and response to the observability store with a trace id.
- Redact detected secrets and email addresses before the request leaves the network.

## Routing

Routes are named strings such as `summarise-long`, `classify-cheap`, `agent-tools`.
Each route maps to a primary model and one fallback model.
A venture never names a model directly in application code.

## Spend caps

Caps are set quarterly by group finance.
When a venture exceeds 90% of its cap the gateway emits a warning event.
At 100% the gateway returns HTTP 429 for non critical routes and continues to serve routes marked critical.
