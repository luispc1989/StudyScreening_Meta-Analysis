# Phase 0 - DOI Enrichment

## Purpose

Phase 0 was designed to reduce the number of records without a DOI before PDF retrieval begins. In practical terms, this stage acts as a metadata enrichment layer: it identifies records with missing DOI information, queries external bibliographic sources, evaluates candidate matches, and decides whether a DOI can be safely added automatically, should be flagged for human review, or must remain unresolved.

This phase exists for three main reasons:

1. Many downstream operations in the toolkit depend on DOI quality.
2. DOI-based retrieval is more reproducible than title-based manual search.
3. DOI enrichment early in the workflow reduces ambiguity in the following phases.

## Operational objective

The goal of Phase 0 is not simply to maximize DOI recovery. Its goal is to recover DOIs while preserving methodological safety. This means the stage is intentionally conservative: when the evidence is weak or ambiguous, the record is not auto-enriched.

In methodological terms, the phase aims to balance:

- coverage: recover as many missing DOIs as reasonably possible;
- precision: avoid inserting incorrect DOIs;
- traceability: keep each decision explainable and auditable.

## Input and scope selection

Phase 0 starts from the active workbook and scans the full set of records. Only records meeting the following conditions are considered eligible for DOI lookup:

- the record exists and has a valid `record_id`;
- the DOI field is empty or unusable;
- the title is sufficiently available for searching;
- DOI overwrite safeguards do not exclude the row.

The scope analysis produces the key counts shown in the terminal:

- total rows read;
- rows with existing DOI;
- rows missing DOI;
- rows eligible for lookup;
- rows skipped because they do not contain enough information.

This separation is important because the phase should only spend time on cases where enrichment is both necessary and methodologically defensible.

In the current implementation, this distinction became even more important because Phase 0 can now be rerun from a saved `phase_0` workbook. That created a practical reporting issue: after a rerun, the workbook already contains newly enriched DOI values, so the current number of `missing DOI` records no longer reflects the original baseline seen at the first execution.

To address this, the current app stores baseline Phase 0 scope metadata inside the workbook itself through a hidden metadata sheet. This lets the terminal distinguish between:

- original missing DOI / original eligible counts;
- current missing DOI / current eligible counts.

This was introduced specifically to preserve a correct interpretation of the enrichment stage over iterative reruns.

## Sources queried

The DOI enrichment engine uses a staged source cascade:

- primary sources:
  - Crossref
  - OpenAlex
- secondary sources:
  - DataCite
  - Europe PMC

The current configuration is intentionally ordered. Crossref and OpenAlex are queried first because they tend to provide strong coverage for conventional scholarly outputs. Secondary sources are then used to improve recall when the first layer is insufficient.

## Query strategy

For each eligible title, the system generates up to three query variants. The exact intention is to improve resilience to punctuation, subtitles, formatting noise, and minor title differences. The enrichment logic can stop early when a candidate is already strong enough, instead of always exhausting all possible variants and sources.

This design reduces unnecessary latency while preserving a conservative decision logic.

## Candidate generation and consolidation

Each external source returns candidate metadata, which is then normalized and collapsed by DOI. If multiple sources point to the same DOI, the candidate is consolidated and its `source_count` increases. This is important because corroboration from more than one source is treated as a stronger signal than a single-source match.

The candidate ranking is based on:

- confidence score;
- number of corroborating sources;
- title similarity;
- deterministic tie-breaking.

## Matching logic

Each candidate DOI is evaluated using three main signals:

- title similarity;
- year consistency;
- author consistency.

The current confidence function is:

```text
confidence_score =
    (title_similarity * 100 * 0.70) +
    (year_score * 0.15) +
    (author_score * 0.15)
```

This means:

- title similarity is the dominant signal;
- year and author agreement serve as supporting evidence rather than primary drivers.

This weighting reflects the fact that titles are usually the most stable identifier across bibliographic sources, while author formatting and year representation can vary.

## Decision classes

Phase 0 classifies each processed record into one of three main outcomes.

### `enriched`

The DOI is written automatically into the workbook.

This only happens when the best candidate satisfies a strong combination of safeguards:

- minimum title similarity: `0.93`
- minimum confidence score: `82.0`
- minimum top-2 gap: `8.0`
- minimum corroborating sources: `2`
- additional metadata support through either:
  - author score at least `25.0`, or
  - year score at least `70.0`

There is also an exceptional title-match safeguard:

- title similarity at least `0.97`

This allows strong title evidence to compensate, to a limited extent, for weaker corroboration.

### `needs_review`

The system found a plausible DOI candidate, but the evidence was not strong enough for safe automatic insertion.

Current lower plausibility thresholds:

- minimum title similarity: `0.88`
- minimum confidence score: `70.0`

Typical reasons for `needs_review` include:

- the top two candidates are too close;
- author/year support is weak;
- only one source returned the DOI;
- the match is plausible but fails at least one safeguard for automatic insertion.

### `unresolved`

The record remains without DOI.

This happens when:

- no candidate was found;
- or the best candidate remains below the plausibility thresholds.

In decision terms, unresolved cases are not necessarily hopeless; they are simply not safe enough for automatic enrichment under the current rules.

## Early stopping and conservative design

The phase includes an early-stop mechanism. If a candidate becomes very strong early in the search process, the system stops querying additional variants and sources.

Current early-stop thresholds:

- title similarity at least `0.97`
- confidence score at least `88.0`
- at least `2` corroborating sources

This improves efficiency without relaxing quality control.

## Why the phase is conservative

The central design decision in Phase 0 was to prioritize correctness over aggressive enrichment. In a dissertation context, this is important for at least four reasons:

1. an incorrect DOI can contaminate all downstream retrieval stages;
2. false positives are harder to detect later than false negatives;
3. a conservative enrichment strategy is easier to justify methodologically;
4. ambiguous cases can be explicitly isolated for review instead of silently accepted.

For this reason, `needs_review` is not a failure state. It is a deliberate buffer between automation and human validation.

## Outputs written to the workbook

When a DOI is enriched automatically, the workbook is updated with:

- DOI;
- DOI link.

The workbook therefore becomes the bridge between Phase 0 and the following retrieval phases.

The current implementation also stores internal Phase 0 baseline metadata in the workbook. This metadata is not meant as a bibliographic output field; it exists to preserve the original scope of the enrichment problem for later reporting and continuation.

## Reporting logic

Phase 0 can generate a dedicated report workbook with separate sheets for:

- all processed records;
- enriched records;
- needs-review records;
- unresolved records;
- statistics.

This reporting design supports auditability and allows the enrichment stage to be described transparently in the dissertation.

The terminal now supports a more nuanced interpretation of rerun status:

- if original baseline metadata is available, the user sees both original and current DOI-scope values;
- if an older `phase_0` workbook predates this metadata, the terminal explicitly reports that the original baseline is unavailable instead of silently treating the current state as the original one.

## What was done in the current implementation

The implemented Phase 0 includes:

- deterministic scope analysis before search begins;
- multi-source DOI querying;
- title-based query variants;
- candidate consolidation across sources;
- weighted confidence scoring;
- conservative decision thresholds;
- separate statuses for `enriched`, `needs_review`, and `unresolved`;
- terminal progress monitoring;
- optional reporting for audit and review.

Recent implementation refinements also include:

- explicit `new run` versus `continue previous run` terminal startup logic;
- phase-specific current workbook naming (`wos_workbook_current_phase_0.xlsx`);
- preservation of original Phase 0 baseline counts for later reruns;
- improved responsiveness when interrupting the phase from the terminal.

## Why it was done this way

The current implementation was built to serve a research workflow rather than a generic metadata-enrichment service. That led to several practical choices:

- deterministic rules instead of opaque model decisions;
- explicit thresholds instead of hidden heuristics;
- source corroboration as a trust signal;
- an intermediate `needs_review` class to protect against over-automation;
- report generation to support reproducibility and dissertation writing.

## Limitations

The current phase still has limitations:

- it depends on the quality of external bibliographic APIs;
- some records remain unresolved because titles are too noisy or incomplete;
- author metadata can be inconsistent across sources;
- the current matching logic is strong but still rule-based, which means borderline cases may require human interpretation.

An important practical limitation remains: if a `phase_0` workbook was created before baseline metadata began to be stored, the app cannot reconstruct the original missing-DOI counts retroactively with full reliability. In those cases, the original baseline should be treated as unavailable unless the phase is rerun from the original Input workbook.

## Dissertation framing suggestion

For the dissertation, Phase 0 can be described as:

> a conservative bibliographic enrichment stage designed to improve DOI completeness before automated PDF retrieval, while preserving transparency, auditability, and methodological control.

That phrasing captures both the technical and research rationale behind the phase.
