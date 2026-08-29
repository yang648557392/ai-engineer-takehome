---
doc_id: D007
title: "Ticket PLAT-4411 - Orlo requests vector namespace"
date: 2027-07-22
source_type: ticket
---

# Ticket PLAT-4411 - Orlo requests vector namespace

**Reporter:** Orlo engineering
**Assignee:** platform lead

## Request

Orlo asks for a namespace on the shared vector cluster to power in-app plant identification search.
Estimated 900,000 vectors at launch.

## Resolution

Rejected for now.
Orlo processes photographs that can contain identifiable people in the background, which group legal treats as special category adjacent.
Per the current retention policy, that requires DPO sign-off, which Orlo has not obtained.
Capacity is also a concern given the Pindrop Labs footprint.
Revisit after DPO sign-off and after the Pindrop pruning job lands.
