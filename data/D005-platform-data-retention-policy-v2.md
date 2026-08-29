---
doc_id: D005
title: "Platform Data Retention Policy v2"
date: 2027-05-20
source_type: policy
---

# Platform Data Retention Policy v2

Applies to all data stored on shared platform infrastructure.
This version supersedes v1 of November 2026.

## Retention windows

- Application logs: 30 days.
- Embeddings and vector index contents derived from customer data: 90 days.
- Raw customer documents in object storage: 12 months.

## Deletion requests

A customer deletion request must be executed within **2 working days** of receipt.
The venture owning the customer relationship files the request with the platform team.
Deletion must cascade to derived embeddings in the same window.

## Access

Access to the shared vector database cluster is granted per venture by the platform lead.
Ventures handling special category personal data require an additional sign-off from the group DPO.
