# PDF Fetcher App - Dissertation Notes

## 1. Overview

The PDF Fetcher app is a local Python-based tool designed to support a dissertation workflow for systematic review and meta-analysis. Its purpose is to increase full-text availability from bibliographic records stored in an Excel workbook, while preserving reproducibility, traceability, and operational control.

The app was not designed as a generic web-scraping product. It was designed as a research-support application embedded in a broader study-screening pipeline. For that reason, the implementation emphasizes:

- deterministic processing where possible;
- staged escalation from simple to complex retrieval;
- explicit status tracking;
- compatibility with iterative reruns;
- workbook-based persistence across phases.

In practical terms, the app reads bibliographic records from an Excel workbook, enriches missing DOI information, attempts PDF retrieval in a generic way, escalates unresolved cases to publisher-specific resolvers, and stores the resulting state in the workbook and project folders.

## 2. Main objective

The main objective of the PDF Fetcher app is to improve the proportion of records with accessible full-text PDFs in a structured and auditable way.

This objective is operationalized through three stages:

1. enrich DOI metadata where possible;
2. retrieve PDFs using a generic DOI-based approach;
3. apply publisher-specific resolvers to unresolved or attributable cases.

The app therefore acts both as a retrieval engine and as a workflow management layer.

## 3. Design rationale

The app was developed around a few key methodological assumptions:

- DOI quality strongly influences retrieval success;
- not all retrieval cases should be treated with the same level of complexity;
- generic methods should be tried before publisher-specific automation;
- every automated action should leave an interpretable audit trail;
- rerunning the workflow should be safe and should not duplicate work unnecessarily.

This led to a staged architecture in which each phase has a distinct role and produces state that is consumed by the next phase.

## 4. Workflow model

The intended workflow is:

1. start from the workbook in `Input`;
2. run Phase 0 to enrich DOI metadata;
3. save the updated workbook to `Current`;
4. run Phase 1 using the updated `Current`;
5. save the updated workbook again to `Current`;
6. run Phase 2 using the latest `Current`;
7. save the final workbook to `Final`.

This design means that:

- `Input` is the original source workbook;
- `Current` is the active working workbook;
- `Final` is the formal saved output;
- checkpoints and reports provide additional traceability.

The app therefore does not depend purely on volatile session memory. It uses workbook persistence as the core bridge between phases.

## 5. Directory and persistence model

Within the active project, the main folders used by the app are:

- `Excel/Input`
- `Excel/Current`
- `Excel/Final`
- `PDF Fetcher/PDFs`
- `PDF Fetcher/Reports`
- `PDF Fetcher/Checkpoints`

This separation serves different purposes:

- `Input` preserves the original imported state;
- `Current` stores the latest working state;
- `Final` stores finalized outputs;
- `PDFs` stores downloaded full-text files;
- `Reports` stores diagnostics and analysis files;
- `Checkpoints` provide safety and recoverability during execution.

## 6. Core data model

The app uses a relatively small set of core structures:

- `Record`
  - represents a workbook row;
- `DownloadResult`
  - represents the outcome of one retrieval attempt;
- `RetryTask`
  - represents a Phase 2 specialized retrieval task;
- `SessionState`
  - stores the loaded workbook, records, paths, and phase summaries.

This separation helps keep the app modular:

- the workbook is the persistent store;
- the models are the runtime abstraction;
- the UI only reflects what the pipeline emits.

## 7. Phase structure

The app is organized into three main phases.

### 7.1 Phase 0 - DOI Enrichment

Phase 0 identifies records with missing DOI information and tries to enrich them using external bibliographic sources such as:

- Crossref
- OpenAlex
- DataCite
- Europe PMC

The phase evaluates candidate DOIs using title similarity, year consistency, and author consistency. It classifies records into:

- `enriched`
- `needs_review`
- `unresolved`

The goal is not simply to maximize DOI recovery, but to do so safely enough for downstream automation.

### 7.2 Phase 1 - PDF Basic Download

Phase 1 is the generic PDF retrieval phase. It attempts direct DOI-based download using:

- DOI links already present in the workbook;
- normalized DOI URLs;
- direct PDF responses;
- HTML metadata such as `citation_pdf_url`;
- simple generic PDF link extraction.

It also checks whether the PDF already exists locally. This makes reruns safe and efficient.

Typical Phase 1 outcomes include:

- `downloaded`
- `duplicate_pdf`
- `invalid_doi`
- `not_found`
- `broken_link`
- `paywalled`
- `metadata_only`
- `manual_check`

### 7.3 Phase 2 - PDF Specialized Download

Phase 2 is the publisher-specific layer. It is used when the generic Phase 1 logic is insufficient or when the record is attributable to a known resolver.

The current implementation groups records by resolver and processes them resolver-by-resolver. This improves:

- predictability;
- monitoring;
- debugging;
- future extensibility.

Phase 2 currently supports:

- MDPI
- Frontiers
- Springer
- Elsevier

The app also supports two Phase 2 execution modes:

- automatic mode
  - runs all active resolvers sequentially;
- manual mode
  - allows the user to select one resolver only.

This is especially useful for debugging and targeted validation of new resolvers.

## 8. Why the phases were separated

The three-phase model was chosen for methodological and practical reasons.

### 8.1 Separation of concerns

Each phase solves a different class of problem:

- metadata completion;
- generic retrieval;
- specialized retrieval.

This prevents complex publisher-specific logic from contaminating the baseline workflow.

### 8.2 Explainability

When a record fails, the phase structure helps explain where and why:

- the DOI may be missing or ambiguous;
- the generic retrieval may be insufficient;
- the publisher may require a custom resolver.

### 8.3 Efficiency

Many records are resolved early:

- some by DOI enrichment;
- many by generic download;
- many reruns by duplicate detection.

This means browser-heavy specialized resolvers are only used where they add value.

## 9. Resolver architecture

Resolvers are the publisher-specific automation modules used in Phase 2.

Each resolver is designed to:

- know its own publisher workflow;
- avoid workbook logic;
- avoid UI logic;
- return a structured `DownloadResult`.

The active app currently contains resolvers for:

- `mdpi`
- `frontiers`
- `springer`
- `elsevier`

The design intention is that all future resolvers will follow the same pattern:

- publisher detection;
- resolver bucketization;
- duplicate-safe execution;
- structured status return;
- integration into the shared Phase 2 menu and stats system.

## 10. Workbook fields used by the app

The workbook acts as the operational memory between phases. Key fields used by the app include:

- `DOI`
- `DOI Link`
- `pdf_downloaded`
- `pdf_download_status`
- `pdf_file_name`
- `pdf_source_url`
- `pdf_local_path`
- `pdf_http_status`
- `pdf_checked_at`

These fields are intentionally operational. They store the minimum persistent state needed for the next phase and for auditability.

## 11. Terminal interface

The terminal interface was designed to provide operational clarity without overwhelming the user.

The current terminal behavior reflects several design choices:

- phase-specific dashboards;
- live progress reporting;
- persistent final summary menus;
- reduced flicker where possible;
- resolver-specific Phase 2 summaries;
- a dedicated submenu for full resolver stats.

Phase 2, in particular, now supports:

- resolver progress;
- resolver downloads;
- resolver duplicates;
- resolver failures;
- all-resolver statistics in a dedicated submenu;
- manual selection of a single resolver.

This is important for the dissertation context because it demonstrates that the tool was not only implemented, but also made operable and inspectable for iterative research work.

## 12. Reporting and diagnostics

The app can generate diagnostic Excel reports to support:

- error analysis;
- publisher distribution analysis;
- resolver prioritization;
- unresolved-case inspection.

This reporting layer is particularly important because the unresolved set is not merely a set of failures; it is also a guide for future system extension. For example, unresolved clusters by publisher can indicate which resolver should be implemented next.

## 13. Safety and rerun behavior

One of the core practical goals of the app was rerun safety.

This was achieved through:

- duplicate PDF detection;
- persistent workbook state;
- checkpoints;
- explicit statuses instead of silent overwrites;
- separation between working and final workbooks.

This means the workflow can be rerun iteratively without redownloading everything from scratch and without losing the audit trail of what happened.

## 14. Methodological strengths

From a dissertation perspective, the strongest features of the app are:

- staged design with clear phase boundaries;
- deterministic decision logic in the DOI enrichment stage;
- explicit classification of retrieval outcomes;
- publisher-specific extensibility;
- workbook-based persistence and traceability;
- diagnostic reporting for unresolved cases;
- compatibility with iterative, researcher-controlled use.

These strengths make the tool suitable not just for automation, but for methodologically defensible research support.

## 15. Current limitations

The app also has clear limitations, which are important to acknowledge in academic writing:

- some DOI enrichments remain unresolved because candidate evidence is too weak;
- some publishers require heavy or fragile automation;
- anti-bot and access-control mechanisms can limit retrieval;
- not every unresolved case is attributable to an implemented resolver;
- browser-based resolvers can be slower and less predictable than the generic phase.

These limitations are not accidental. In several places, the system was intentionally designed to remain conservative rather than over-automate risky cases.

## 16. Evolution logic

The app was developed to support gradual expansion. The intended evolution pattern is:

1. keep the core workflow stable;
2. identify unresolved publishers through diagnostics;
3. prototype new resolvers in the archive;
4. validate them in isolation;
5. integrate them into Phase 2 without breaking the overall architecture.

This pattern has already been used in practice for resolvers such as:

- Frontiers
- Springer
- Elsevier

This gradual integration strategy is one of the strongest architectural features of the tool.

## 17. Suggested dissertation framing

A good concise way to describe the app in the dissertation would be:

> The PDF Fetcher app is a staged retrieval system that combines DOI enrichment, generic full-text acquisition, and publisher-specific PDF resolution in a workbook-driven workflow. Its design prioritizes reproducibility, auditability, rerun safety, and progressive extensibility, making it suitable for systematic-review support in a dissertation context.

## 18. Suggested chapter structure for writing

If these notes are to be turned into dissertation text, a good structure would be:

1. motivation for automated metadata enrichment and PDF retrieval;
2. overall architecture of the app;
3. phase-by-phase methodology;
4. workbook persistence and state management;
5. publisher-specific resolver strategy;
6. reporting and unresolved-case analysis;
7. limitations and future extensions.

This would let the technical implementation support the methodological narrative cleanly.
