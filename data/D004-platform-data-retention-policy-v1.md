---
doc_id: D004
title: "Platform Data Retention Policy v1"
date: 2026-11-02
source_type: policy
---

# Platform Data Retention Policy v1

Applies to all data stored on shared platform infrastructure.
Issued November 2026 by the platform team.

## Retention windows

- Application logs: 30 days.
- Embeddings and vector index contents derived from customer data: 180 days.
- Raw customer documents in object storage: 12 months.

## Deletion requests

A customer deletion request must be executed within **5 working days** of receipt.
The venture owning the customer relationship files the request with the platform team.

## Access

Access to the shared vector database cluster is granted per venture by the platform lead.
