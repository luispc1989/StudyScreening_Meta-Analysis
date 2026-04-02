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
4. `elsevier`

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

## Dissertation framing suggestion

A concise way to describe Phase 2 in the dissertation would be:

> Phase 2 is a resolver-based specialized retrieval stage that applies publisher-specific automation to records attributable to known publication platforms. Its design supports resolver-level execution, duplicate-safe reruns, controlled escalation from generic retrieval, and incremental system extension.

## Suggested writing angle

For dissertation writing, Phase 2 can be framed as the stage where the system shifts:

- from generic retrieval to platform-aware retrieval;
- from broad heuristics to targeted automation;
- from simple DOI resolution to controlled publisher-specific workflows.

That framing helps position Phase 2 as the main bridge between a robust baseline system and an extensible research-oriented automation framework.
