# Dissertation Notes

## Purpose

This file is the high-level methodological and architectural memory of the `PDF Fetcher` project. It is intended to support dissertation writing by recording:

- what was built;
- why it was built that way;
- how the design evolved;
- what limitations shaped the implementation;
- what future architecture is already envisioned.

It should be read as a bridge between technical implementation and dissertation narrative.

## Core framing

The `PDF Fetcher` is not just a downloader. It is a staged research-support system designed to improve full-text availability for a meta-analysis workflow in a controlled, auditable, and incrementally extensible way.

The current logic is:

1. start from a bibliographic Excel input;
2. enrich DOI metadata where possible;
3. attempt generic PDF retrieval;
4. escalate unresolved cases to specialized publisher resolvers;
5. pass residual cases to a semi-assisted manual triage layer (`S.C.O.U.T.`).

This staged design was chosen to preserve:

- methodological clarity;
- traceability of actions;
- rerun safety;
- explainability of failures;
- future extensibility.

## Why a staged architecture was chosen

The workflow was separated into phases because the underlying problems are different:

- `Phase 0` solves metadata incompleteness;
- `Phase 1` solves generic retrieval;
- `Phase 2` solves publisher-specific retrieval;
- `S.C.O.U.T.` solves manual residual handling.

This separation prevents the system from collapsing into a single opaque script where all concerns are mixed together.

From a dissertation perspective, this matters because it allows each stage to be described as a distinct methodological step with a clear rationale.

## Workbook-based persistence as the current architecture

At the current stage of development, Excel workbooks are the persistent bridge between phases.

The workflow now uses explicit per-phase workbooks:

- `wos_workbook_current_phase_0.xlsx`
- `wos_workbook_current_phase_1.xlsx`
- `wos_workbook_current_phase_2.xlsx`

This was an important refinement because a single generic `Current` workbook had become too ambiguous. Phase-specific naming makes the workflow easier to:

- resume;
- debug;
- explain in writing;
- inspect after interruptions.

## Why session continuity became an architectural theme

As the project evolved, it became clear that persistence was not only about saving outputs. It was also about preserving operational memory:

- where the user stopped;
- what had already been reviewed;
- what had already been enriched;
- what had already been downloaded;
- what was still pending.

This became especially visible in:

- `Phase 0` reruns, where the current missing-DOI count no longer reflected the original baseline;
- `S.C.O.U.T.` resume logic, where reopened sessions could accidentally use old or incomplete case reports if naming and persistence rules were not strict enough.

These issues are methodologically relevant because they affect how progress, coverage, and unresolved cases are interpreted.

## Phase 0 and the importance of preserving the original baseline

One important lesson was that the current state of a workbook is not always enough to reconstruct the original problem size.

Example:

- if `Phase 0` enriches some DOI values,
- a later rerun on the same workbook will see fewer missing DOI rows,
- but this does not mean the original input had fewer missing DOIs.

To address this, `Phase 0` now stores baseline scope metadata inside the workbook itself. This preserves the distinction between:

- original missing DOI / eligible rows;
- current missing DOI / eligible rows after enrichment.

This is important for the dissertation because it prevents misleading interpretations of the Phase 0 contribution.

## Why the SCOUT exists

The `S.C.O.U.T.` (Semi-assisted Case Opening and User Triage) emerged because not all unresolved cases should be treated as failures of automation. Some are better understood as cases requiring:

- manual search;
- alternative link insertion;
- author contact;
- manual classification.

The SCOUT therefore acts as a post-automation triage layer rather than as part of the automated retrieval core.

This is methodologically important because it distinguishes between:

- automated acquisition capacity;
- researcher-supervised resolution of residual cases.

## Current direction for future architecture

The current workbook-based system is functional and suitable for a local research tool, but it already reveals structural limitations:

- many intermediate files;
- state spread across workbooks and reports;
- friction in long-term continuation;
- more difficulty in sharing projects across people and time.

Because of this, a future architectural direction has already been identified:

- Excel as import/output layer;
- a local project database as the internal source of truth;
- a project file that can be reopened later, by the same or another user;
- a `hub launcher` coordinating multiple tools and phases of the meta-analysis workflow.

## Future hub launcher

The future system is expected to include a broader launcher layer, tentatively described as a `hub launcher`.

Its role would be to centralize:

- project opening/creation;
- access to multiple tools;
- phase navigation;
- shared project settings;
- integration credentials and app configuration;
- reuse of previous project state.

This is important because the `PDF Fetcher` is already evolving from a single-purpose tool into part of a larger meta-analysis workflow ecosystem.

## Future database rationale

The database direction is motivated by practical and methodological concerns.

A local database would make it easier to support:

- long-term project continuity;
- reopening by another person in another location;
- importing new search results years later;
- merging new records with previously reviewed records;
- preserving decisions, notes, statuses, and provenance without relying on multiple Excel files as the living state.

In this future model:

- Excel remains the import and export interface;
- the database becomes the internal operational memory;
- the project becomes portable through a local project file.

This is especially relevant for a dissertation because it shows that the project already points toward a mature research software architecture rather than a disposable script.

## Writing value for the dissertation

These notes matter because they capture not just features, but design reasoning. The dissertation will benefit from documenting:

- why the app became phase-based;
- why persistence rules had to change;
- why `S.C.O.U.T.` exists as a separate layer;
- why baseline preservation matters;
- why the architecture is now moving conceptually toward a project database and hub model.

This allows the final dissertation text to describe the tool not just as code, but as a research-support system that evolved through observed practical constraints.
