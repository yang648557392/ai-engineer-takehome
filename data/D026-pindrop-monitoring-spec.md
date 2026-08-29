---
doc_id: D026
title: "Pindrop Labs - Anomaly Digest Feature Spec"
date: 2027-05-06
source_type: spec
---

# Pindrop Labs - Anomaly Digest Feature Spec

## Goal

Every morning, produce a one page digest per customer site summarising overnight vibration anomalies and operator voice notes.

## Requirements

- Calls the agent gateway on the `summarise-long` route.
- Every anomaly in the digest must reference the sensor id and timestamp it came from.
- Operator voice notes are transcribed on device and stored as text; the transcripts are embedded into pd-prod for search.
- The digest must state explicitly when no anomalies were recorded.

## Out of scope

Automatic work orders or any write to the customer's maintenance system.
