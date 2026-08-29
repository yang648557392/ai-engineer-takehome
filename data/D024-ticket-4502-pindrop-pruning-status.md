---
doc_id: D024
title: "Ticket PLAT-4502 - Pindrop pruning job, status update"
date: 2027-08-13
source_type: ticket
---

# Ticket PLAT-4502 - Pindrop pruning job, status update

**Assignee:** Pindrop Labs engineering
**Status:** in progress

## Update

The nightly pruning job is written and has run in dry run mode against pd-prod for three nights.
The dry run identifies 1.08 million vectors older than the policy window.
No deletions have been executed yet.
Pindrop engineering wants the platform lead's ruling on the telemetry classification before the first live run.

## Next step

Platform lead to confirm go ahead for the first live run.
