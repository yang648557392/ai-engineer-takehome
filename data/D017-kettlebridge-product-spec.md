---
doc_id: D017
title: "Kettlebridge - Shipment Summary Feature Spec"
date: 2027-03-28
source_type: spec
---

# Kettlebridge - Shipment Summary Feature Spec

## Goal

Given a shipment thread of emails, documents, and status events, produce a one paragraph summary and a list of open issues.

## Requirements

- The summary must cite the source event or document for every claim.
- The feature calls the agent gateway on the `summarise-long` route.
- Latency target is 6 seconds at the 95th percentile.
- If the model cannot find an open issue it must say so rather than inventing one.

## Out of scope

Automatic replies to the customer.
Any write action against the freight forwarder systems.
