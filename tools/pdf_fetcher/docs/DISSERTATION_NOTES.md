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
- `PrismaLab`, a future app master coordinating multiple tools and phases of the meta-analysis workflow.

## Future PrismaLab application

The future system is expected to include a broader application layer called `PrismaLab`.

Its role would be to centralize:

- project opening/creation;
- access to multiple tools;
- phase navigation;
- shared project settings;
- integration credentials and app configuration;
- reuse of previous project state.

This is important because the `PDF Fetcher` is already evolving from a single-purpose tool into part of a larger meta-analysis workflow ecosystem.

## App master direction

The expected master application is no longer being conceptualized as a Streamlit-only layer.

During development, Streamlit proved highly effective for:

- rapid prototyping;
- workflow validation;
- tool-specific interfaces such as `S.C.O.U.T.`;
- fast iteration over research-use features.

However, once the project was reframed as a future multi-tool ecosystem, a different requirement emerged: the top-level application needs to feel like a coherent project workspace rather than a collection of internal scripts.

For that reason, the current direction for the app master is:

- `React / Next.js` for the master frontend;
- Python retained for workflow logic and tool backends;
- local database persistence for project state;
- Excel preserved as import/export format rather than as the living internal state.

This is not only a technical preference. It reflects a usability and architectural shift: the system is moving from a tool-first prototype into a project-first application.

## Why the app master should be phase-oriented

The expected master app should be organized by the phases of the meta-analysis workflow rather than by a flat list of tools.

The intended phases are:

1. question definition;
2. literature search;
3. study screening;
4. critical appraisal of studies;
5. data extraction;
6. statistical synthesis;
7. discussion and conclusion.

Within that structure, tools become subordinate to workflow meaning. This is important because it changes the interface from a technical launcher into a research-oriented workbench.

In this model:

- the app explains where the user is in the research process;
- each phase can expose its own tools;
- project continuity becomes easier to understand;
- future dissertation writing can map software structure directly onto methodological stages.

## Current prototyping step for the app master

A first visual prototype of the future master app has already been created in:

- `apps/prismalab`

This prototype is intentionally lightweight. It is not yet the operational application. Its purpose is to test:

- visual direction;
- navigation logic;
- phase-oriented organization;
- the relationship between project state, tools, and future database integration.

This is relevant for the dissertation because it demonstrates that architectural planning is already being translated into tangible interface prototypes rather than remaining only a conceptual future plan.

That prototyping stage has since been extended with a more substantial frontend shell in:

- `apps/prismalab-frontend`

This second prototype is important because it moves beyond static visual exploration and begins to test:

- the authenticated entry flow of the future platform;
- a phase-oriented workspace shell;
- the relationship between platform branding (`PrismaLab`) and assistant branding (`Ray`);
- local-first authentication assumptions;
- future project-oriented dashboard behavior.

In other words, the frontend work is no longer only aesthetic exploration. It is now beginning to encode product assumptions that are directly relevant to the future research workspace architecture.

## Current frontend direction inside PrismaLab

The current frontend prototyping work is already converging on a few concrete interaction principles.

### Access page as institutional entry point

The access page is being treated as a dedicated entry screen rather than as a marketing-style landing page.

This means the interface emphasizes:

- `PrismaLab` as the main platform identity;
- restrained branding rather than promotional language;
- local sign-in and local profile creation;
- continuity of use across sessions on the same machine.

This is relevant for the dissertation because it reflects a deliberate design choice: the system is being framed as a serious research workspace rather than a generic consumer dashboard.

### Local-first authentication model

The current frontend prototype now includes a local authentication layer designed for a desktop-style research environment.

Implemented assumptions include:

- local profile creation;
- local sign-in;
- remembered-session behavior;
- a temporary developer access path for testing;
- explicit future separation between profile identity and later external integrations.

At the current stage, these profile records are stored locally in browser storage rather than in the future project database. This is not the final architecture, but it is a useful intermediate step for validating the access flow and profile semantics before moving them into the local database layer.

### Recovery Key as the only recovery method

One important architectural decision in the current frontend prototype is that account recovery is not email-based.

Instead, the current direction uses a locally generated `Recovery Key` that is:

- shown only once after account creation or recovery;
- explicitly framed as the only way to recover access;
- regenerated after a password reset;
- intended to be stored securely by the user.

This is methodologically relevant because it aligns the authentication model with the local-first architecture. A remote email-reset workflow would imply backend infrastructure that does not match the current project direction.

### Platform versus assistant separation

The frontend prototype also clarifies an important branding and product distinction:

- `PrismaLab` is the platform;
- `Ray` is an assistant inside the platform.

This matters because the system is no longer being conceptualized as a loose mixture of tools and AI components. The frontend is starting to formalize a clearer architecture in which the assistant supports the workspace without replacing the platform identity itself.

### Dashboard as project-first workspace

The current authenticated dashboard is now evolving toward a project-first structure rather than a decorative landing screen.

The current UI direction emphasizes:

- active-project awareness;
- phase-based navigation;
- workflow entry points;
- local project continuity;
- the future role of preserved project memory.

This is still prototype work, but it is already relevant for the dissertation because it demonstrates the move from a tool launcher to a structured research environment that can later support reopening, continuation, and gradual project accumulation.

### Desktop shell groundwork

The repository now also contains a first dedicated desktop shell scaffold in:

- `apps/prismalab-desktop`

This matters because the intended PrismaLab direction is no longer a pure
browser-style application. The frontend can continue to be prototyped quickly in
web technologies, but the target runtime is now being formalized as a desktop
wrapper around the shared PrismaLab frontend.

The current architectural interpretation is:

- `apps/prismalab-frontend` = shared UI codebase;
- `apps/prismalab-desktop` = thin desktop shell;
- future local SQLite database = same source of truth for both;
- desktop-specific session behavior should be implemented in the native shell,
  not faked in the browser prototype.

This is relevant for the dissertation because it clarifies that the project is
not oscillating between two unrelated app models. Instead, it is converging on a
single local-first product with one interface and one persistence model, later
distributed through a desktop runtime.

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

This architectural direction has now moved from a purely conceptual intention
into an initial concrete foundation inside `tools/prismalab`.

The first implementation step is a minimal SQLite project database designed to:

- store project identity;
- preserve import provenance from multiple bibliographic databases;
- preserve row-level raw source data before merge;
- maintain a canonical article model with optional missing fields;
- include contact information such as author email when available;
- support future duplicate analysis and long-term project reopening.

This is especially relevant for a dissertation because it shows that the project already points toward a mature research software architecture rather than a disposable script.

## Writing value for the dissertation

These notes matter because they capture not just features, but design reasoning. The dissertation will benefit from documenting:

- why the app became phase-based;
- why persistence rules had to change;
- why `S.C.O.U.T.` exists as a separate layer;
- why baseline preservation matters;
- why the architecture is now moving conceptually toward a project database and hub model.

This allows the final dissertation text to describe the tool not just as code, but as a research-support system that evolved through observed practical constraints.
