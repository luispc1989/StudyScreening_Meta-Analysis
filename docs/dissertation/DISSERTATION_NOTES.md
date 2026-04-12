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

- `archive/apps/prismalab-prototype`

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

### Branding as architectural clarification rather than decoration

The current `PrismaLab` and `Ray` branding work should also be documented as
part of the product architecture.

This branding effort is not only about making the interface visually coherent.
It helps formalize several conceptual distinctions that matter for the
dissertation:

- `PrismaLab` is the persistent research workspace;
- `Ray` is an assistant embedded within that workspace;
- the platform should feel institutional, stable, and serious;
- the assistant should feel supportive and identifiable without visually
  replacing the platform itself.

This logic shaped several implementation decisions, including:

- keeping `PrismaLab` as the dominant identity on access and workspace screens;
- giving `Ray` its own visual system, lockups, avatars, and tab/icon assets;
- separating platform branding from assistant branding in the UI hierarchy;
- treating branding assets as reusable product resources rather than scattered
  prototype leftovers.

This matters for the dissertation because the identity system already expresses
architectural meaning. It tells the user that the software is not merely a
collection of scripts plus an AI chatbot. It is a research platform with an
internal assistant, and that distinction is part of the system design itself.

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

## Detailed rationale for the current PrismaLab frontend prototype

The recent frontend work should not be described in the dissertation as a
purely cosmetic redesign. It is better understood as an architectural
clarification phase in which the future product assumptions of `PrismaLab` were
made explicit through interface and interaction design.

Several important implementation lines emerged during this stage.

### 1. Access and authentication were treated as local-workspace concerns

The access page was intentionally implemented as the entrance to a local
research environment rather than as a conventional web SaaS sign-in screen.

This decision led to several implementation choices:

- local account creation instead of remote registration;
- local session continuity;
- remembered local account selection;
- explicit distinction between account access and later profile settings;
- removal of misleading email-reset assumptions.

The reason for this strategy is methodological and architectural. The intended
`PrismaLab` product is a local-first research environment, expected to support
long-running projects that may be reopened months or years later on the same
machine or under a portable local project model. A generic email-based
authentication flow would have implied backend infrastructure and trust
assumptions that do not currently match the project direction.

### 2. Recovery was implemented through a Recovery Key rather than email

The `Recovery Key` flow is one of the most important product decisions already
materialized in the prototype.

The implemented behavior now includes:

- generation of a unique recovery key at account creation;
- one-time display of that key;
- explicit warning that it is the only recovery mechanism;
- a dedicated local recovery flow;
- invalidation of the old key after successful password reset;
- regeneration and re-display of a new key after recovery.

The reason for this design is that recovery had to remain coherent with a
local-first system. Email-based reset would have introduced a false expectation
of remote account infrastructure. The recovery key, by contrast, fits the logic
of a local profile that must remain recoverable without a cloud backend.

### 3. The login model evolved from username entry to account selection

As soon as multiple local accounts began to exist on the same machine, the
original login pattern became less appropriate.

The prototype therefore evolved toward:

- selecting an existing local account first;
- entering the password only afterwards;
- remembering the previously used local account;
- keeping account creation as a separate explicit action.

This matters for the dissertation because it reflects a design decision derived
from observed product semantics rather than from generic UI fashion. In a
local-first multi-profile environment, the machine already knows what accounts
exist. Asking the user to type a username every time becomes less logical than
selecting the local account directly.

### 4. Account and profile semantics were intentionally separated

During implementation it became clear that the words `user`, `account`, and
`profile` were being used interchangeably, which created conceptual drift.

This was corrected by treating:

- `account` as the authentication and access concept;
- `profile` as the in-app identity and settings concept.

This distinction is methodologically useful because it prevents the future
dissertation text from describing a blurred identity model. It also creates a
cleaner basis for later features such as settings, preferences, external
integrations, and role-specific project behavior.

### 5. The frontend prototype exposed why an internal identifier is still needed

The registration flow originally exposed both a visible full name and a
username. Later evaluation showed that asking the user to manually define a
username was no longer justified by the desired experience.

The current direction therefore keeps:

- a human-facing full name;
- an internal stable identifier generated automatically.

This is worth documenting because it shows a transition from a conventional
website-style registration form to a more research-tool-oriented account model.
The decision was not merely cosmetic. It preserved internal stability while
reducing unnecessary cognitive overhead in the access flow.

### 6. Session handling was deliberately treated as a desktop-like behavior

One recurring design question concerned the meaning of session continuity in a
research tool used across long time spans.

The important conceptual distinction that emerged is:

- a password proves identity and should protect access and sensitive actions;
- a local session should preserve continuity of work across app restarts;
- `Remember me` should support local convenience rather than imply a cloud-like
  perpetual authentication contract.

Because the current implementation still lives in a browser-based prototype,
true system-level distinctions such as "same PC boot cycle" versus "new system
boot" cannot yet be enforced robustly. This limitation itself is relevant for
the dissertation, because it demonstrates why some session policies belong more
naturally to the future desktop shell than to a pure browser prototype.

### 7. A unified loading language was implemented on purpose

The access flow, logout flow, and sign-in flow originally risked using
different loading behaviors or temporary blank states.

This was corrected by introducing a unified branded loading/splash treatment
based on the `PrismaLab` identity, adaptable to light and dark themes.

The importance of this decision is not only aesthetic. Consistent loading
states reduce the perception of instability and make a research application feel
more reliable, especially when profile state, routing, or local session
hydration introduce brief transitions.

### 8. The Ray assistant was treated as a product component, not just a chat box

The `Ray` prototype went through substantial refinement. This matters because
the dissertation should not present the assistant as a generic LLM wrapper.

The implemented direction now includes:

- separate `Ray` branding and lockups;
- theme-aware assistant identity assets;
- a floating launcher distinct from the main platform brand;
- a resizable and movable side panel;
- keyboard closing (`Esc`);
- persistent per-account chat history;
- internal conversation history management;
- a dedicated thinking state;
- separation between the assistant as helper and the platform as workspace.

This is important conceptually because it defines `Ray` as an assistant inside
the platform, not as the platform itself.

### 9. Ray history persistence became a concrete test of profile-local state

The assistant history was deliberately moved toward per-account persistence.

This exposed a very relevant product requirement:

- when a user leaves the app and returns with the same account,
- the assistant history should still be there;
- another account should see its own distinct history.

This requirement is especially important for dissertation framing because it
shows how the frontend prototype is already functioning as a testbed for
account-scoped project memory, not merely for visual interface experiments.

### 10. The Home page versus Workflow separation became explicit

One major architectural clarification in the recent frontend work was that the
first page after access should not simply be another workflow phase.

Instead, the interface now distinguishes:

- a `Home` entry page for workspace-level orientation;
- a separate `Workflow` area for phase-specific work.

The current home is intentionally limited to:

- workspace welcome and state summary;
- key actions such as opening or starting a project;
- short project-state cards;
- immediate next actions.

The reason for this is that the user first needs orientation at the workspace
level before entering a methodological phase. This distinction will help the
dissertation explain that the system is moving from "tool launching" toward a
structured project environment.

## Bugs, frictions, and implementation lessons from the frontend prototype

The dissertation notes should also preserve the fact that the current frontend
direction was shaped by concrete implementation frictions rather than by
abstract planning alone.

### Temporary state flicker after logout

At one point, after logout the access page briefly showed older user-oriented
state before switching to the corrected account-based version.

The underlying problem was hydration timing: the first render occurred before
local account state had been fully read.

The fix was to delay the final access-page decision until local state hydration
completed. This is worth documenting because it shows how local-first interfaces
can easily produce misleading transient states if hydration order is not handled
carefully.

### Password reset logic originally failed to explain one important case

During recovery, setting a new password identical to the old one initially led
to an unhelpful error path.

This revealed that the recovery logic was not yet distinguishing clearly
between:

- invalid recovery details;
- valid recovery details but invalid new-password choice.

The correction was important because it turned a vague security-style failure
into a meaningful user explanation, improving both usability and interpretive
clarity.

### Session and browser storage semantics produced false assumptions

Several issues emerged because the browser prototype stores local accounts and
session information in local storage:

- existing accounts could persist unexpectedly across tests;
- old developer/test users remained present;
- browser state could be mistaken for application database state.

This is highly relevant for dissertation writing because it reinforces a key
point: browser storage is a temporary prototyping layer, not the intended final
source of truth. It works well for validating flows, but it also exposes why the
project needs a future local database and desktop shell.

### Ray history could be overwritten during initialization

One important bug occurred when the assistant state initialized with an empty
default conversation and wrote that state too early, thereby replacing the
persisted history of the active account.

The fix required making history hydration explicit and delaying writes until the
stored account history had first been loaded.

This is especially valuable as dissertation material because it illustrates a
general software-engineering lesson: local persistence is not only about saving
state; it is also about preserving load order and avoiding accidental overwrite
during startup.

### Drawer sizing and positioning required iteration

The `Ray` panel went through multiple refinements:

- too tall for the intended workspace context;
- too large in hero-banner style for a side panel;
- incorrect opening position within the main workspace area;
- drag and history interactions interfering with one another.

These iterations are worth recording because they show that interaction design
in a research workspace is not trivial decoration. Window behavior, history
management, and visual density affect whether the assistant feels like a useful
embedded tool or a disruptive overlay.

## Why this level of documentation matters

The dissertation should show that the frontend work was not simply a matter of
"making the interface nicer." It already functioned as a concrete site for
testing:

- local-first account semantics;
- recovery logic without backend dependency;
- session and continuity behavior;
- the boundary between platform and assistant;
- the distinction between workspace home and methodological workflow;
- the future suitability of desktop deployment over a purely browser-based app.

In other words, the frontend prototype is already part of the research and
architecture story of the project. It should therefore be documented with the
same seriousness as the retrieval pipeline and persistence-layer decisions.

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

