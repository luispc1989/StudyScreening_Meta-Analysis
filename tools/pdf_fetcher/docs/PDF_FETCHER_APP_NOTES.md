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
7. use `S.C.O.U.T.` for residual manual triage when needed;
8. save the final workbook to `Final`.

This design means that:

- `Input` is the original source workbook;
- `Current` is the active working workbook;
- `Final` is the formal saved output;
- checkpoints and reports provide additional traceability.

The app therefore does not depend purely on volatile session memory. It uses workbook persistence as the core bridge between phases.

The current implementation should also be understood as one tool inside a broader evolving toolkit. The `PDF Fetcher` is no longer being designed as an isolated utility only. It is increasingly being treated as one phase-aware module that will later sit inside a wider project-oriented application for meta-analysis work.

## 5. Directory and persistence model

Within the active project, the main folders used by the app are:

- `PDF Fetcher/Excel/Input`
- `PDF Fetcher/Excel/Current`
- `PDF Fetcher/Excel/Final`
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

In the current implementation, the `Current` folder is phase-explicit rather than generic. The active workbook state is now stored through:

- `wos_workbook_current_phase_0.xlsx`
- `wos_workbook_current_phase_1.xlsx`
- `wos_workbook_current_phase_2.xlsx`

This means each stage now leaves a clearly named handoff workbook for the next stage, which makes the workflow easier to explain, safer to resume, and easier to audit.

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
- Wiley
- Elsevier

The app also supports two Phase 2 execution modes:

- automatic mode
  - runs all active resolvers sequentially;
- manual mode
  - allows the user to select one resolver only.

This is especially useful for debugging and targeted validation of new resolvers.

After the publisher-specific resolvers, the current logic treats `Sci-Hub` as a final automated fallback layer rather than as an immediate per-resolver escape hatch. This separation was adopted because it is easier to interpret, easier to report in a dissertation, and operationally less noisy than invoking `Sci-Hub` directly inside every resolver path.

The current intended automatic logic is:

1. run specialized resolvers;
2. run `Sci-Hub` pass 1 on still-unresolved eligible cases;
3. run `Sci-Hub` pass 2 only on retryable `Sci-Hub` failures;
4. send the remaining unresolved cases to `S.C.O.U.T.`.

## 8. Why the phases were separated

The three-phase model was chosen for methodological and practical reasons.

### 8.1 Separation of concerns

Each phase solves a different class of problem:

- metadata completion;
- generic retrieval;
- specialized retrieval.

This prevents complex publisher-specific logic from contaminating the baseline workflow.

## 7.4 S.C.O.U.T. as post-Phase-2 review layer

After `Phase 2`, the app can launch `S.C.O.U.T.` (Semi-assisted Case Opening and User Triage). This is not part of the automated retrieval pipeline itself, but a manual review layer built on top of the `Phase 2` workbook.

The current intended logic is:

1. `Phase 2` saves `wos_workbook_current_phase_2.xlsx`;
2. `S.C.O.U.T.` uses that workbook as its source;
3. `S.C.O.U.T.` creates a lightweight case report for unresolved or still-relevant cases;
4. the user performs manual triage, search, or author-contact actions there;
5. final workbook synchronization happens only after review completion.

This design keeps the automated pipeline and the manual decision layer conceptually separate.

As the SCOUT matured, it also gained more explicit operational safeguards. The interface now preserves review memory, exposes review-status cues, and allows reversal of wrongly saved PDFs through an `Erase PDF` action that returns the case to `Pending Review`. These details are not just UI polish; they are part of making manual triage reversible and auditable.

## 7.5 Forward link to PrismaLab

Although the current operational interfaces are still the terminal and the Streamlit-based `S.C.O.U.T.`, the longer-term direction of the project has shifted toward a broader top-level application called `PrismaLab`.

That future layer is expected to:

- organize the workflow by meta-analysis phase rather than by a flat list of tools;
- coordinate project opening, continuation, and export;
- centralize settings and future integrations;
- treat the `PDF Fetcher` as one tool among several.

The current repository already includes an early prototype for that direction in:

- `apps/prismalab`

This prototype is exploratory, but it is important because it documents the architectural transition from a tool-first prototype into a project-first application ecosystem.

That future direction now also includes an initial database foundation under:

- `tools/prismalab/core`
- `tools/prismalab/docs/DATABASE_ARCHITECTURE.md`

The role of this first database layer is not to replace the current workbook
workflow immediately. Its role is to define the minimum internal project memory
needed for:

- project reopening;
- multi-source bibliographic import;
- duplicate analysis;
- preservation of canonical article metadata and provenance.

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

## 10. Resolver construction strategy

The resolver layer was not conceived as a collection of unrelated publisher scripts. A deliberate construction strategy was followed so that new resolvers could be added incrementally without destabilizing the app.

### 10.1 Why resolvers were built incrementally

Publisher-specific automation was treated as an empirical engineering problem rather than a purely theoretical design task. In practice, publisher platforms differ in:

- navigation structure;
- cookie and consent behavior;
- DOI redirection behavior;
- PDF exposure mechanism;
- viewer design;
- access-control or institutional layers.

Because of this variability, resolvers were built incrementally and validated against real cases before being incorporated into the active Phase 2 workflow.

### 10.2 Practical construction workflow

The construction strategy for a new resolver follows a recurring sequence:

1. identify an unresolved publisher cluster through diagnostics or repeated failures;
2. create or adapt a prototype in the archive area;
3. validate the retrieval flow in isolation on real examples;
4. identify the concrete failure modes of that publisher;
5. translate the validated logic into the active resolver architecture;
6. register the resolver in detection and in the Phase 2 pipeline;
7. test the resolver in manual mode;
8. observe runtime failures and refine the resolver conservatively;
9. keep the output contract stable through `DownloadResult`.

This workflow matters because it allows resolver development to remain controlled and reproducible.

### 10.3 Design principles used during resolver construction

Several principles were followed while building resolvers.

#### Preserve the shared contract

Every resolver is expected to return a standardized `DownloadResult`. This means that even though the internal publisher logic can differ greatly, the surrounding pipeline remains stable.

#### Keep publisher logic local

Each resolver should contain publisher-specific navigation and download behavior, but should avoid:

- workbook logic;
- terminal logic;
- Streamlit logic;
- cross-phase orchestration logic.

This separation keeps the pipeline maintainable.

#### Start conservative and widen only when justified

Resolver attribution, domain matching, and fallback logic were introduced conservatively first, then widened only when real cases showed that the original assumptions were too narrow.

This was particularly important for Wiley, where valid cases appeared under multiple Wiley subdomains rather than a single canonical host.

#### Use real failure observation as part of development

Resolver development was not limited to implementing the intended happy path. Runtime observation of actual failures became a formal part of the construction process.

Typical observations included:

- wrong landing pages;
- viewer shells with no PDF loaded;
- missing HTML download links;
- session requests returning non-PDF content;
- cookie or consent interference;
- browser controls becoming relevant only after viewer rendering.

This observation-driven process directly informed resolver refinement.

### 10.4 Resolver development as staged refinement

In methodological terms, a resolver is not implemented once and then considered finished. Instead, resolver construction follows a staged refinement model:

1. baseline prototype;
2. active integration;
3. runtime observation;
4. failure categorization;
5. conservative fixes;
6. retesting.

This is one of the most important practical lessons of the app: specialized retrieval becomes robust not through one large implementation step, but through repeated adjustment against real publisher behavior.

### 10.5 Relationship between general logic and resolver-specific logic

The app intentionally distinguishes between:

- general workflow logic;
- resolver-specific logic.

General workflow logic includes:

- workbook persistence;
- phase orchestration;
- retry-task construction;
- shared statuses;
- terminal and UI reporting.

Resolver-specific logic includes:

- publisher-domain recognition;
- page interaction flow;
- viewer handling;
- PDF-link extraction;
- download fallbacks;
- resolver-specific cookie or session handling.

This distinction is important because it prevents Phase 2 from collapsing into a monolithic downloader with publisher behavior mixed into the core workflow.

### 10.6 Why common abstractions were delayed in some cases

Some behaviors, such as cookie-banner interference, appear across multiple publishers. However, the app did not immediately abstract those behaviors into a single generic utility.

That choice was intentional.

During active resolver development, it was often more useful to solve the issue publisher-by-publisher first, because:

- the exact interaction patterns still needed to be observed;
- different publishers exposed superficially similar but technically different problems;
- premature abstraction could hide important publisher-specific constraints.

The intended strategy is therefore:

1. refine behavior resolver-by-resolver first;
2. observe recurring patterns across publishers;
3. abstract only what proves to be genuinely common.

### 10.7 Dissertation relevance

For dissertation purposes, the resolver construction strategy demonstrates that the specialized retrieval layer was developed through a systematic and auditable methodology.

It shows that:

- unresolved cases were used as evidence for extension priorities;
- prototypes were validated before integration;
- integration preserved architectural consistency;
- debugging relied on observed runtime behavior rather than guesswork;
- improvements were introduced conservatively to avoid breaking the broader workflow.

This makes the resolver layer defensible not only as software engineering work, but also as a methodologically structured part of the research-support system.

## 11. Workbook fields used by the app

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

## 12. Terminal interface

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

Recent terminal changes also improved workflow continuity:

- startup now distinguishes between:
  - starting a new run from the Input workbook;
  - continuing from saved phase workbooks;
- the `continue previous run` option is only shown when saved phase workbooks actually exist;
- phase transitions now display explicit loading/saving messages rather than appearing idle;
- quitting during execution now uses lighter checkpoint logic and more responsive interruption behavior.

## 13. Reporting and diagnostics

The app can generate diagnostic Excel reports to support:

- error analysis;
- publisher distribution analysis;
- resolver prioritization;
- unresolved-case inspection.

This reporting layer is particularly important because the unresolved set is not merely a set of failures; it is also a guide for future system extension. For example, unresolved clusters by publisher can indicate which resolver should be implemented next.

## 14. Safety and rerun behavior

One of the core practical goals of the app was rerun safety.

This was achieved through:

- duplicate PDF detection;
- persistent workbook state;
- checkpoints;
- explicit statuses instead of silent overwrites;
- separation between working and final workbooks.

This means the workflow can be rerun iteratively without redownloading everything from scratch and without losing the audit trail of what happened.

One important refinement is that rerun safety is now phase-aware. Instead of relying on a single generic `Current` workbook, the app can resume from explicit phase outputs. This helps preserve a clearer operational history:

- `Phase 0` resumes from `phase_0`;
- `Phase 1` resumes from `phase_1`;
- `Phase 2` resumes from `phase_2`;
- `S.C.O.U.T.` starts from `phase_2` and then maintains its own review memory.

For Phase 0 specifically, the app now also stores baseline DOI-scope metadata in the workbook itself so that later reruns can distinguish:

- original missing DOI counts;
- current missing DOI counts after enrichment.

This is particularly useful for dissertation reporting because it preserves the distinction between the original problem size and the remaining unresolved subset.

## 15. Methodological strengths

From a dissertation perspective, the strongest features of the app are:

- staged design with clear phase boundaries;
- deterministic decision logic in the DOI enrichment stage;
- explicit classification of retrieval outcomes;
- publisher-specific extensibility;
- workbook-based persistence and traceability;
- diagnostic reporting for unresolved cases;
- compatibility with iterative, researcher-controlled use.

These strengths make the tool suitable not just for automation, but for methodologically defensible research support.

## 16. Current limitations

The app also has clear limitations, which are important to acknowledge in academic writing:

- some DOI enrichments remain unresolved because candidate evidence is too weak;
- some publishers require heavy or fragile automation;
- anti-bot and access-control mechanisms can limit retrieval;
- not every unresolved case is attributable to an implemented resolver;
- browser-based resolvers can be slower and less predictable than the generic phase.

These limitations are not accidental. In several places, the system was intentionally designed to remain conservative rather than over-automate risky cases.

Another current limitation is architectural: the persistent workflow still uses Excel workbooks as the primary state bridge between phases. This has worked well for the current local tool, but it also creates friction in session recovery, project portability, and long-term incremental reuse.

For that reason, a future direction already identified is:

- Excel as import/export layer;
- a local project database as the internal source of truth;
- a portable project file that can later be reopened, extended, and re-exported.

## 17. Evolution logic

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

## 18. Suggested dissertation framing

A good concise way to describe the app in the dissertation would be:

> The PDF Fetcher app is a staged retrieval system that combines DOI enrichment, generic full-text acquisition, and publisher-specific PDF resolution in a workbook-driven workflow. Its design prioritizes reproducibility, auditability, rerun safety, and progressive extensibility, making it suitable for systematic-review support in a dissertation context.

## 19. Suggested chapter structure for writing

If these notes are to be turned into dissertation text, a good structure would be:

1. motivation for automated metadata enrichment and PDF retrieval;
2. overall architecture of the app;
3. phase-by-phase methodology;
4. workbook persistence and state management;
5. publisher-specific resolver strategy;
6. reporting and unresolved-case analysis;
7. limitations and future extensions.

This would let the technical implementation support the methodological narrative cleanly.
