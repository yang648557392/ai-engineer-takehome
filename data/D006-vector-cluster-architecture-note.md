---
doc_id: D006
title: "Shared Vector Cluster - Architecture Note"
date: 2027-03-11
source_type: architecture-note
---

# Shared Vector Cluster - Architecture Note

## Setup

One managed vector database cluster, three logical namespaces, one per approved venture.
Namespaces are isolated by API key, not by network.
Embedding model is pinned per namespace and recorded in the namespace registry.

## Approved namespaces as of March 2027

- `kb-prod` - Kettlebridge
- `pd-prod` - Pindrop Labs
- `mc-sandbox` - Marrow & Co, sandbox only, no customer data

Orlo has no namespace on the shared cluster.

## Known limits

The cluster plan caps total stored vectors at 5 million.
At the March 2027 measurement the cluster held 3.1 million vectors, of which Pindrop Labs accounted for 2.4 million.
