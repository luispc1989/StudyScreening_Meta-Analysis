# Implementation Log

## Purpose

This file records the most important implementation changes in a concise chronological form. It is not meant to replace detailed technical notes; it is meant to preserve a readable sequence of major decisions, fixes, and structural changes.

Recommended structure per entry:

- Date
- Change
- Why
- Impact

---

## 2026-04-06 to 2026-04-09

### Change

SCOUT evolved from a lightweight review page into a more structured manual triage layer.

### Why

Residual unresolved cases needed a controlled interface for:

- opening article links;
- using manual search;
- adding or clearing DOI/source links;
- assigning decisions;
- preserving review state.

### Impact

The project now distinguishes more clearly between automated retrieval and manual residual-case handling.

---

## 2026-04-07

### Change

Explicit per-phase current workbooks were introduced:

- `wos_workbook_current_phase_0.xlsx`
- `wos_workbook_current_phase_1.xlsx`
- `wos_workbook_current_phase_2.xlsx`

### Why

A single generic `Current` workbook was becoming ambiguous and harder to reason about during reruns, transitions, and debugging.

### Impact

Phase boundaries became clearer, continuation became easier to explain, and file organization became more aligned with the actual staged workflow.

---

## 2026-04-07

### Change

The `Excel` folder used by the tool was moved conceptually under `PDF Fetcher`, and reports/checkpoints were reorganized by phase.

### Why

The previous structure mixed workflow artifacts too broadly and made the project harder to inspect.

### Impact

The project now has a clearer operational layout:

- `PDF Fetcher/Excel/Input`
- `PDF Fetcher/Excel/Current`
- `PDF Fetcher/Excel/Final`
- `Reports/Phase 0`, `Phase 1`, `Phase 2`, `SCOUT`
- `Checkpoints/Phase 0`, `Phase 1`, `Phase 2`, `SCOUT`

---

## 2026-04-07

### Change

Startup logic was added to distinguish:

- `Start new run from Input workbook`
- `Continue previous run from saved phase workbooks`

### Why

Users needed a clear way to decide whether to restart from the original input or continue from the last saved phase state.

### Impact

The terminal now supports explicit session continuity, and the `continue` option only appears when saved phase workbooks exist.

---

## 2026-04-08

### Change

Phase 0 baseline DOI-scope metadata started being stored in the workbook itself.

### Why

When rerunning Phase 0 on a previously enriched workbook, the current `missing DOI` count no longer reflected the original baseline. This created misleading interpretations of coverage.

### Impact

The app can now distinguish between:

- original missing DOI / original eligible
- current missing DOI / current eligible

This improves both terminal interpretation and dissertation reporting.

---

## 2026-04-08

### Change

Terminal interruption behavior was refined:

- lighter checkpoint saving on quit;
- fewer silent waits;
- more explicit transition/loading messages.

### Why

Users observed that `S` to exit could feel slow or visually confusing, especially during active requests.

### Impact

Quit behavior became more responsive and less visually erratic.

---

## 2026-04-08

### Change

Phase 1 end-of-phase save and phase transitions were simplified to avoid redundant workbook reloads.

### Why

Users reported unnecessary delays after Phase 1 finished and before Phase 2 menus appeared.

### Impact

The terminal now shows clear loading/saving messages and avoids some redundant reload operations.

---

## 2026-04-08

### Change

Phase 2 dashboard refresh logic was corrected to reduce excessive redraw behavior.

### Why

The terminal appeared to stall and then refresh in jumps during specialized resolver runs.

### Impact

Phase 2 should now behave more smoothly, with refreshes aligned to meaningful progress rather than every processed record.

---

## 2026-04-09

### Change

Documentation was updated to reflect the current architecture, phase-specific files, SCOUT role, and future direction toward a local project database and PrismaLab.

### Why

The documentation had become partly inconsistent with the actual implementation and no longer matched the current workflow accurately.

### Impact

The project now has a stronger foundation for dissertation writing and future structured notes.

---

## 2026-04-10

### Change

The architectural direction for the future master application was clarified:

- the master app should be phase-oriented rather than tool-flat;
- the long-term frontend direction should be `React / Next.js`;
- a first PrismaLab prototype was created in `apps/prismalab` and is now archived as `archive/apps/prismalab-prototype`.

### Why

The project is no longer only a PDF retrieval tool. It is evolving toward a broader local research environment with multiple tools, shared project state, and future long-term portability.

### Impact

The project now has an explicit prototype and direction for a future app master that can coordinate phases and tools in a more scalable way than a Streamlit-only launcher.

---

## 2026-04-10

### Change

The `S.C.O.U.T.` interface was refined again:

- article cards gained a review-status badge;
- PDF auto-save delay was reduced from `5s` to `3s`;
- an `Erase PDF` action was added to revert an incorrectly saved PDF and return the case to `Pending Review`;
- widget-state conflicts were resolved when resetting the review state.

### Why

Manual triage needed clearer visual status, faster feedback after download detection, and a safe recovery path when the wrong PDF had been saved.

### Impact

The SCOUT now supports a more realistic manual-review workflow with better reversibility and fewer state inconsistencies.

---

## 2026-04-10

### Change

The Phase 2 orchestration strategy was refined:

- specialized resolvers are kept distinct from `Sci-Hub`;
- `Sci-Hub` is treated as a final fallback pass;
- a second `Sci-Hub` retry pass was introduced for retryable failures only;
- resolver interruption responsiveness and timeout behavior were tightened.

### Why

Mixing `Sci-Hub` directly into every resolver path was methodologically messy and could overload the fallback layer. Users also observed that some resolver runs were too slow to interrupt and that Wiley in particular could hang in inconsistent viewer states.

### Impact

Phase 2 became more interpretable, more defensible for dissertation reporting, and more controllable during long-running browser-heavy automation.

---

## 2026-04-11

### Change

The first `PrismaLab` database foundation was introduced in code and documentation.

This includes:

- a dedicated database architecture note;
- a minimal SQLite schema per project;
- a canonical article model that accepts incomplete metadata;
- explicit provenance tables for imported rows and source batches;
- explicit contact storage including author email when available.

### Why

The project now needs a persistence layer that can evolve beyond a single
`Web of Science` workbook and support imports from multiple bibliographic
databases while preserving deduplication and long-term project memory.

### Impact

The repository now has a concrete starting point for the gradual transition
from workbook-driven persistence to a local-first project database coordinated
by `PrismaLab`.

---

## 2026-04-11

### Change

A more substantial `PrismaLab` frontend prototype was integrated in:

- `apps/prismalab-frontend`

This prototype now includes:

- a dedicated access page;
- local profile creation;
- remembered local sessions;
- a local `Recovery Key` recovery flow;
- a phase-oriented authenticated shell;
- a first project-oriented dashboard;
- a clearer separation between `PrismaLab` as platform and `Ray` as assistant.

### Why

The initial `apps/prismalab` prototype, now archived as `archive/apps/prismalab-prototype`, was useful for high-level visual direction, but it was still too lightweight to validate actual product behavior. A more concrete frontend layer was needed to test how the future master app should feel and behave as a local-first research workspace.

### Impact

The repository now contains a stronger frontend reference for dissertation writing and future implementation. The project is no longer only documenting a future app master concept; it is already testing the concrete access flow, workspace shell, and dashboard logic of the expected `PrismaLab` platform.

---

## 2026-04-11

### Change

Desktop-shell groundwork was added in:

- `apps/prismalab-desktop`

This shell is scaffolded as a thin `Tauri` wrapper around:

- `apps/prismalab-frontend`

### Why

The project needs to keep prototyping UI quickly in web technology while still
moving toward a serious desktop-local-first product. A separate frontend and
desktop codebase would introduce unnecessary divergence.

### Impact

The repository now has an explicit packaging direction for PrismaLab:

- one shared frontend;
- one future desktop runtime;
- one future local database;
- desktop-specific behaviors to be implemented in the native shell rather than
  simulated in the browser prototype.

---

## 2026-04-12

### Change

The `PrismaLab` frontend prototype was substantially refined in four connected
areas:

- local authentication and access semantics;
- local recovery and account continuity;
- `Ray` assistant interaction model;
- workspace home versus workflow separation.

Concretely, this included:

- account selection on the access page instead of a purely typed username flow;
- automatic generation of internal account identifiers instead of exposing
  `username` as a primary registration field;
- one-time `Recovery Key` display and local recovery flow;
- improved login validation, password visibility, disabled/loading states, and
  branded splash transitions;
- clearer distinction between `account` and `profile` language;
- `Ray` launcher, banner, avatars, theme-aware assets, history menu, delete
  controls, thinking state, movable/resizable panel, and per-account persisted
  history;
- explicit `Home` navigation entry separated from `Workflow`;
- routing changes so the post-login entry point is now `/app`, while workflow
  pages remain separate.

### Why

The previous prototype still mixed together several concepts that needed to be
made clearer before the dissertation could describe the future product
coherently:

- the difference between a local account and an in-app profile;
- the difference between a workspace home and a workflow phase;
- the difference between a platform (`PrismaLab`) and an assistant (`Ray`);
- the difference between browser-prototype persistence and the future local
  database source of truth.

The access flow also needed to become more consistent with a local-first
research environment rather than resembling a generic web-platform sign-in.

At the same time, the assistant needed to move beyond a decorative chat widget
and become a more plausible embedded research tool with account-scoped memory
and clearer behavioral rules.

### Impact

The frontend prototype now supports a much stronger dissertation narrative.

It no longer serves only as a visual mockup; it now demonstrates:

- a coherent local authentication model;
- recovery without remote email infrastructure;
- assistant persistence per local account;
- separation between workspace orientation and phase-oriented work;
- a practical bridge from web prototyping toward a future desktop-local-first
  runtime.

### Bugs and lessons recorded during this stage

Several implementation frictions shaped these refinements:

- temporary post-logout flicker caused by hydration timing;
- recovery errors that initially did not distinguish "same password" from
  "invalid recovery details";
- account/test data unexpectedly persisting because browser local storage was
  acting as the temporary persistence layer;
- assistant history being overwritten if startup hydration and persistence order
  were not carefully managed;
- the `Ray` panel opening at incorrect positions until its coordinates were
  constrained to the actual workspace area;
- overly large assistant banner proportions that had to be reduced from hero
  scale to side-panel scale;
- assistant history controls that initially felt visually unclear and therefore
  had to be reorganized.

These are useful dissertation notes because they show that the current
architecture emerged through observed interaction problems and incremental
correction, not merely through top-down design claims.

