# Phase 2 - PDF Specialized Download

## Purpose

Phase 2 is the specialized retrieval layer of the PDF Fetcher app. Its purpose is to handle records that either:

- were not fully resolved by the generic download logic;
- or are attributable to publisher-specific resolvers that can operate more effectively than the generic Phase 1 strategy.

In practical terms, Phase 2 exists because many publisher platforms do not expose PDFs in a simple DOI-to-PDF workflow. Instead, they require site-specific handling, browser automation, HTML interaction, or resolver logic tailored to their publication platform.

## Position in the workflow

Phase 2 is designed to run after the workbook has already passed through:

1. Phase 0 - DOI Enrichment
2. Phase 1 - PDF Basic Download

This means that Phase 2 should not be understood as a general first-pass downloader. It is an escalation stage.

Its role is to work on the cases that remain relevant for specialized handling after the previous phases have already done their work.

## Main objective

The main objective of Phase 2 is to improve PDF recovery beyond the limits of the generic strategy, while preserving:

- structured execution;
- repeatability;
- resolver-level monitoring;
- safe reruns;
- explicit classification of outcomes.

Unlike Phase 1, which is intentionally publisher-agnostic, Phase 2 assumes that some publishers require dedicated logic and that these publishers should be processed resolver-by-resolver.

## Why Phase 2 was necessary

The need for Phase 2 emerged from practical observation:

- some publishers expose PDFs through custom buttons rather than direct links;
- some publishers require browser-rendered pages before PDF access is possible;
- some publishers use viewer pages, temporary asset URLs, or nontrivial navigation flows;
- some sites behave differently in headless and visible browser modes.

A generic HTTP strategy alone is therefore insufficient for robust coverage.

Phase 2 was designed as the controlled answer to that limitation.

## Resolver-based architecture

Phase 2 is built around the concept of resolvers.

A resolver is a publisher-specific retrieval module responsible for:

- identifying whether a record belongs to its publisher;
- executing the site-specific PDF retrieval logic;
- returning a standardized `DownloadResult`.

The current implementation includes:

- `mdpi`
- `frontiers`
- `springer`
- `wiley`
- `elsevier`

The architecture was explicitly designed so that additional resolvers can be added later without changing the overall workflow model.

## How records enter Phase 2

Phase 2 works from the workbook state left by earlier phases, especially Phase 1. The current workflow uses the `Current` workbook as the active working state.

The app reconstructs the relevant operational information from that state and uses it to identify which records are attributable to specialized resolvers.

This means that Phase 2 is not an isolated script. It is a continuation of the staged workbook-driven workflow.

## Bucketization logic

One of the central design decisions of Phase 2 was to group records by resolver instead of processing the entire unresolved set in an undifferentiated way.

The workflow is therefore:

1. inspect the eligible records;
2. identify which resolver applies to each case;
3. create resolver buckets;
4. process those buckets one resolver at a time.

This approach was chosen because it is:

- easier to debug;
- easier to monitor;
- easier to validate empirically;
- easier to extend with future resolvers.

It also matches the methodological need to understand which publishers are already covered and which remain unresolved.

## Automatic and manual modes

Phase 2 currently supports two execution modes.

### Automatic mode

In automatic mode, the app runs all active resolvers sequentially, one resolver at a time.

This is the best mode for:

- full workflow execution;
- broader recovery attempts;
- end-to-end batch runs.

### Manual mode

In manual mode, the user selects one resolver only.

This mode is especially useful for:

- testing a single resolver;
- debugging publisher-specific logic;
- validating a newly integrated resolver;
- avoiding long runs when only one resolver is of interest.

After running a single resolver in manual mode, the user can:

- repeat that resolver;
- go back to the resolver list;
- return to earlier menus;
- save the workbook or run diagnostics.

This manual control was intentionally added to support iterative resolver development.

## Current execution order

The active resolver order in automatic mode is:

1. `mdpi`
2. `frontiers`
3. `springer`
4. `wiley`
5. `elsevier`

The specific order is not conceptually fixed forever, but the resolver-by-resolver structure is central to the current design.

## Duplicate handling

One of the most important practical features of Phase 2 is duplicate-safe execution.

When a resolver is run on a record whose PDF already exists locally, the system returns:

- `duplicate_pdf`

This behavior matters because reruns are common in this workflow. Specialized resolvers must therefore be safe to execute repeatedly without redownloading everything.

In methodological terms, this makes Phase 2:

- idempotent in normal use;
- efficient for iterative debugging;
- auditable in terms of what was newly recovered versus what was already present.

## Outcome types in Phase 2

The most important Phase 2 outcomes are:

- `downloaded_<resolver>`
- `duplicate_pdf`
- `not_<resolver>`
- `pdf_link_not_found_<resolver>`
- `download_failed_<resolver>`
- `resolver_exception_<resolver>`

These statuses serve different purposes:

- successful retrieval;
- local duplicate detection;
- wrong resolver attribution;
- missing or inaccessible PDF link;
- failed retrieval attempt;
- resolver-level exception or timeout.

This explicit status model is essential because Phase 2 is more complex than Phase 1 and therefore requires better diagnostic visibility.

## Resolver monitoring

The terminal interface for Phase 2 was designed to provide resolver-level observability.

During execution, the app shows:

- current resolver;
- progress within the current resolver;
- downloads within the current resolver;
- duplicates within the current resolver;
- failures within the current resolver.

At the end of the phase, the user can open a separate resolver-stats submenu showing all resolvers one by one, with:

- progress;
- downloads;
- duplicates;
- failures.

This structure was introduced to balance two competing needs:

- clear visibility;
- avoidance of terminal clutter.

## Why the terminal was redesigned

As the number of resolvers grew, it became clear that a single-line summary would not scale well. Resolver statistics would either be truncated or become visually overwhelming.

The terminal was therefore redesigned so that:

- the main summary stays compact;
- a dedicated submenu contains full resolver statistics;
- the user can inspect details only when needed.

This decision is particularly relevant for dissertation work because it reflects a transition from a prototype-oriented interface to a more mature operational interface.

## Refresh strategy

Phase 2 uses controlled refresh logic rather than redrawing the terminal on every low-level event. This was done to reduce visual flicker, especially in Git Bash and non-ANSI terminal modes.

At the same time, the phase now forces immediate refresh when the active resolver changes. This allows the interface to remain visually stable while still reflecting meaningful state transitions.

## Publisher detection and attribution

Phase 2 depends on resolver attribution logic that uses DOI patterns, DOI links, and source URLs left by earlier phases.

This publisher detection is intentionally cautious. Broad all-resolver sweeps are avoided when there is no credible publisher signal, because that would:

- inflate execution time;
- reduce interpretability;
- generate noisy retry behavior.

Instead, the system aims to assign records only when there is enough evidence that a specific resolver is appropriate.

## Elsevier as a case of resolver integration

The integration of the Elsevier resolver illustrates the intended development pattern of Phase 2:

1. prototype the resolver logic in the archive area;
2. validate its retrieval flow in isolation;
3. adapt the logic to the app while preserving the resolver structure;
4. integrate detection, pipeline registration, and terminal monitoring;
5. evaluate downloads, duplicates, and failures at runtime.

This pattern is likely to be reused for future resolvers.

## Data persistence

Like the previous phases, Phase 2 writes its operational outcomes back to the workbook, including:

- status;
- source URL;
- local file path;
- timestamp;
- HTTP status when available.

This keeps the workflow persistent and ensures that reruns have the information they need.

## Why Phase 2 is not “just another downloader”

Phase 2 is better understood as a resolver orchestration layer rather than a simple download phase.

Its distinguishing features are:

- publisher attribution;
- resolver bucketization;
- controlled execution order;
- manual or automatic execution mode;
- duplicate-aware reruns;
- resolver-level statistics and diagnostics.

These features make it a structured escalation mechanism rather than a loose collection of publisher scripts.

## Strengths

From a dissertation perspective, the main strengths of Phase 2 are:

- modular resolver architecture;
- clear separation from generic retrieval;
- repeat-safe execution;
- strong debugging support;
- explicit status reporting;
- readiness for incremental expansion.

These characteristics are important because they demonstrate that specialized automation was integrated into a coherent workflow, rather than appended as isolated scripts.

## Limitations

Phase 2 also has clear limitations:

- browser-based resolvers are slower than generic requests;
- some publishers use anti-bot or access-control systems;
- resolver maintenance is publisher-dependent;
- publisher attribution can still be imperfect in edge cases;
- not all unresolved publishers are covered yet.

These limitations should be stated clearly in the dissertation because they are part of the realistic boundary conditions of automated full-text retrieval.

## Future extension logic

The intended future development path for Phase 2 is:

1. use diagnostics to identify unresolved publisher clusters;
2. prototype a new resolver in the archive area;
3. validate it manually and in batch form;
4. integrate it into the active app;
5. expose it automatically in the resolver menu and stats system.

This makes Phase 2 not only a retrieval stage, but also the main expansion point of the app.

## Implementation notes from active resolver development

The Phase 2 architecture was not implemented in one step. It evolved through iterative resolver integration, runtime observation, and targeted debugging against real publisher behavior.

The notes below summarize the most relevant implementation work carried out during active development and validation.

### General Phase 2 development decisions

Several design decisions were introduced at the orchestration level rather than inside a single resolver.

#### Resolver integration model

New specialized resolvers were integrated through a consistent pattern:

1. validate or prototype the resolver logic in the archive area;
2. create the active resolver under `tools/pdf_fetcher/core/resolvers/`;
3. register the resolver in the detector;
4. register the resolver in the Phase 2 pipeline;
5. expose the resolver through existing automatic and manual execution modes;
6. preserve the shared `DownloadResult` contract.

This pattern was followed when Wiley was added to the active app.

#### Resolver ordering

Phase 2 was maintained as an ordered resolver-by-resolver process rather than a loose retry sweep. During development, the active resolver sequence became:

1. `mdpi`
2. `frontiers`
3. `springer`
4. `wiley`
5. `elsevier`

The specific ordering can change later, but the important point for the dissertation is that the workflow remained explicit and inspectable.

#### Article-by-article terminal refresh

During practical runs it became clear that refreshing the Phase 2 dashboard only every few completed records made debugging difficult, especially when validating a single resolver such as Wiley.

The Phase 2 refresh logic was therefore changed so that the terminal now updates article-by-article. This made it easier to:

- observe the current resolver state in real time;
- identify where a resolver appeared to stall;
- inspect failures one case at a time during debugging.

#### Failure-detail observability

Originally, many specialized failures were visible only through coarse statuses such as:

- `download_failed_<resolver>`
- `pdf_link_not_found_<resolver>`
- `not_<resolver>`

This was useful for categorization but insufficient for debugging.

To improve observability without changing functional behavior, the specialized resolvers were updated so that controlled failures now also write a human-readable detail into `pdf_checked_at`.

Typical failure details now include:

- `final_url_not_<resolver>: ...`
- `no_pdf_link_found_on_page: ...`
- `session_request_http_403: ...`
- `session_request_not_pdf: ...`
- `browser_download_timeout: ...`
- `viewer_open_failed_or_empty: ...`

This was implemented conservatively: the success/failure logic remained the same, but the audit trail became much more informative.

### Resolver-specific development: Wiley

The Wiley resolver was integrated into the active app from the archive prototype area. This was one of the most important Phase 2 extensions because Wiley cases had repeatedly appeared in the unresolved set.

#### Wiley integration work

The active Wiley resolver was added by:

- creating `tools/pdf_fetcher/core/resolvers/wiley.py`;
- adding Wiley-specific configuration variables;
- registering Wiley in resolver detection;
- registering Wiley in the Phase 2 resolver pipeline;
- treating `downloaded_wiley` as a successful specialized outcome.

This brought Wiley into both:

- automatic Phase 2 execution;
- manual single-resolver testing mode.

#### Wiley attribution and domain recognition

An important issue emerged during early Wiley integration: the initial domain constraints were too narrow. Real Wiley cases appeared under hosts such as:

- `onlinelibrary.wiley.com`
- `acsess.onlinelibrary.wiley.com`
- `scijournals.onlinelibrary.wiley.com`

If domain matching was too strict, valid Wiley cases could be misclassified as `not_wiley`.

The resolver and detector were therefore adjusted so that Wiley attribution accepts Wiley subdomains more flexibly. This was necessary because the real platform does not use one single host consistently.

#### Why Wiley required iterative refinement

Wiley exposed several distinct runtime behaviors that were not fully captured by the first active integration:

- article pages that remained on institutional or legacy landing pages;
- cookie banners and overlays that could obstruct interactions;
- HTML viewer URLs that loaded a shell but not an actual PDF;
- cases where the PDF appeared only after viewer rendering;
- cases where the built-in viewer showed a printable/previewable document but not an immediately accessible direct link.

This made Wiley a good example of why Phase 2 needed resolver-specific debugging rather than generic retry logic.

### Wiley error patterns observed during validation

Several concrete Wiley failure patterns were observed during real runs.

#### 1. Institutional or legacy landing page instead of direct PDF access

In some cases, the DOI resolved to a Wiley-hosted page that showed branding, institutional access text, and cookie consent controls, but did not immediately expose a valid PDF retrieval path.

Typical signs included:

- Wiley Online Library landing layout;
- institutional access indicators;
- cookie or consent banners;
- absence of a directly usable PDF link.

These cases were important because they looked superficially valid while still blocking automation.

#### 2. Empty viewer state (`0 of 0` / `0 de 0`)

Another failure pattern appeared when the resolver opened the Wiley HTML viewer successfully at the URL level, but the viewer itself remained empty and showed no loaded pages.

This was a false-positive navigation success: the viewer shell loaded, but no PDF content was actually available.

The active resolver was updated so that this state is no longer accepted as a meaningful viewer success. It is now classified as a viewer failure instead.

#### 3. Viewer loaded, but retrieval still depended on viewer controls

Some Wiley cases appeared to load successfully inside the browser PDF viewer. In those situations, the document could sometimes be interacted with through native viewer controls such as save or print, even when direct resolver extraction had not yet succeeded.

This revealed an important distinction:

- some viewer cases are empty and unusable;
- some viewer cases have a real rendered PDF and are recoverable through viewer actions.

### Wiley fixes applied

The main Wiley refinements introduced during debugging were the following.

#### Cookie-banner handling

The resolver was updated to dismiss common consent banners before continuing with PDF-link detection and viewer interaction. This did not solve every Wiley case, but it removed an important class of avoidable interference.

At this stage, cookie handling is still being refined resolver-by-resolver rather than abstracted globally. That decision was made intentionally so that cross-publisher common logic can be extracted later from real observed patterns instead of premature assumptions.

#### Viewer readiness validation

The active resolver was updated to reintroduce a stricter notion of viewer readiness. It now checks for viewer-related elements rather than assuming that any successful navigation to a viewer URL means the PDF is usable.

This prevented empty viewer shells from being misinterpreted as valid progress.

#### Viewer candidate extraction

The active resolver was updated to reintroduce additional candidate collection from the viewer page, including JavaScript-based inspection of embedded sources such as:

- `embed`
- `iframe`
- `object`
- linked viewer elements

This increased the chance of recovering viewer-exposed PDF sources that were not visible through simple static selectors alone.

#### Native viewer save/download fallback

In cases where the PDF is visibly loaded inside the Chromium viewer, the resolver now also attempts the native viewer save/download control rather than relying only on publisher HTML download links.

This is important because some cases are recoverable once the PDF is genuinely rendered, even if the publisher-specific HTML flow is inconsistent.

The guiding rule became:

- if the viewer is empty, do not treat it as success;
- if the viewer has loaded a real PDF, attempt native save/download as a practical fallback.

### Why these notes matter for the dissertation

These Phase 2 development notes are important methodologically because they show that specialized retrieval was not treated as a black-box scraping exercise.

Instead, the workflow evolved through:

- staged integration;
- direct observation of publisher behavior;
- explicit categorization of error modes;
- conservative debugging that preserved rerun safety and auditability;
- gradual improvement of resolver robustness based on real cases.

This is especially relevant for dissertation writing because it demonstrates:

- engineering traceability;
- empirical refinement of publisher-specific automation;
- a clear distinction between general workflow logic and resolver-specific behavior.

### Open issues and next Wiley refinements

Even after the improvements described above, Wiley remains an active area of refinement. The following issues should be considered still under observation rather than definitively solved:

- institutional or legacy landing pages that do not expose a stable PDF path quickly;
- cases where cookie or consent layers still interfere with the article flow;
- viewer cases that appear to begin loading but do not fully expose a reusable PDF source;
- cases where the browser viewer may support print preview or save actions only after delayed rendering.

The practical strategy agreed during development was:

1. keep refining Wiley with conservative fixes based on observed runtime behavior;
2. avoid premature abstraction of cookie or consent handling across all publishers;
3. only extract common utilities after similar patterns have been confirmed resolver-by-resolver.

This point is important for dissertation notes because it captures not only what was implemented, but also the rationale for sequencing future work.

## Dissertation framing suggestion

A concise way to describe Phase 2 in the dissertation would be:

> Phase 2 is a resolver-based specialized retrieval stage that applies publisher-specific automation to records attributable to known publication platforms. Its design supports resolver-level execution, duplicate-safe reruns, controlled escalation from generic retrieval, and incremental system extension.

## Suggested writing angle

For dissertation writing, Phase 2 can be framed as the stage where the system shifts:

- from generic retrieval to platform-aware retrieval;
- from broad heuristics to targeted automation;
- from simple DOI resolution to controlled publisher-specific workflows.

That framing helps position Phase 2 as the main bridge between a robust baseline system and an extensible research-oriented automation framework.
