# Recommendation: Conditional Pilot of the Shared Internal QA System

**To:** Group Operations Lead  
**From:** AI Engineering  
**Subject:** Portfolio rollout recommendation

I recommend a conditional yes, not an immediate four-venture rollout. Start with a limited Kettlebridge pilot and expand only after the evaluation, data-governance, capacity, and gateway controls below are complete. Do not onboard Orlo or additional production customer data until its DPO approval is resolved and Pindrop’s retention-policy breach is remediated.

## Cost and operating limits

The closest in-corpus cost benchmark is EUR 62 per 1,000 summaries on the selected primary model [D018]. Until pilot measurements provide a direct cost per answer, I would use that as a conservative planning assumption: 10,000 answers per month would cost approximately EUR 620.

That volume would consume about 21% of Kettlebridge’s EUR 3,000 monthly gateway cap, 52% of Orlo’s EUR 1,200 cap, 25% of Pindrop Labs’ EUR 2,500 cap, or 78% of Marrow & Co’s EUR 800 cap [D010]. These percentages assume the cap were otherwise unused, which it is not; the gateway cap covers all venture model traffic. At 100% of a cap, non-critical routes receive HTTP 429 [D009]. Kettlebridge’s shipment-summary feature uses `summarise-long`, but that route is not designated critical for Kettlebridge in the Q3 cap sheet [D010][D017]. A pilot therefore needs a separate usage budget, alerts, and an agreed response when the cap is reached.

The vector cluster has a five-million-vector limit and held 3.1 million vectors in March, of which Pindrop accounted for 2.4 million [D006]. Pindrop’s dry run identified 1.08 million expired vectors; applying that reduction to the March baseline would leave roughly 2.02 million [D024]. Adding Orlo’s estimated 900,000 launch vectors would produce roughly 2.92 million, but this is only a planning estimate because the corpus provides no current total [D007]. The next storage tier starts at 20 million vectors and roughly triples the monthly fee; the current absolute monthly fee is not provided [D032].

## Conditions before broader rollout

First, expand this submission’s 10-case evaluation set to the internal minimum of 30 domain-authored cases, retain at least 20% refusal questions, and add human spot checks for correctness and citation validity [D012]. A single aggregate score must not be the release gate; refusal regressions should block release even when the average improves [D012].

Second, execute Pindrop’s pruning job rather than leaving it in dry-run status, and settle the disputed classification of operator voice-note transcripts [D008][D024]. The current policy limits customer-derived embeddings to 90 days and requires customer deletion requests, including derived embeddings, to complete within two working days [D005].

Third, Orlo must submit its data protection impact assessment and receive DPO sign-off before its namespace request is reconsidered [D007][D023]. Capacity should be remeasured after pruning rather than inferred from the March snapshot.

Finally, close the shared-platform reliability actions. The gateway still lacks the planned per-route concurrency limit and fallback-rate dashboard, and the July cap-sheet validation action remains open [D011][D025][D029]. Namespace isolation is by API key rather than network boundary, so access controls and audit logs require explicit review before portfolio-wide use [D006].

## First venture

Kettlebridge should go first. It already has a production namespace [D006], its feature specification requires a citation for every claim and explicit abstention rather than invention [D017], and the provider evaluation already used 120 human-written shipment summaries [D018]. That gives the pilot the clearest use case, the strongest existing evaluation material, and a measurable cost baseline.

## Strongest argument against

The strongest argument against even a limited rollout is shared-infrastructure blast radius. One gateway fallback incident affected three ventures and caused roughly 40% of Kettlebridge summarisation requests to time out [D011], while the shared vector environment currently has unresolved retention violations and only API-key namespace isolation [D006][D024]. A new shared QA service could amplify these weaknesses faster than the platform team can correct them; the pilot should therefore remain read-only, volume-capped, and reversible until the listed controls are closed.
