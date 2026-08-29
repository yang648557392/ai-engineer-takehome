---
doc_id: D019
title: "Platform Data Retention Policy v0 (DRAFT, never adopted)"
date: 2026-08-14
source_type: policy
status: draft
---

# Platform Data Retention Policy v0 (DRAFT)

**Status: draft for comment. Never adopted. Superseded by v1 of November 2026.**

## Proposed retention windows

- Application logs: 90 days.
- Embeddings and vector index contents derived from customer data: 365 days.
- Raw customer documents in object storage: 24 months.

## Proposed deletion handling

A customer deletion request should be executed within 10 working days of receipt.

## Comments received

Group legal considered 365 days for derived embeddings too long and asked for a shorter window before adoption.
The platform team agreed and the numbers were revised in v1.
