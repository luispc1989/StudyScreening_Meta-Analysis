# PDF Fetcher Development Log

## Purpose

This file is the detailed development log for the PDF Fetcher tool and its sub-tools.

It exists to capture, session by session:

- what changed;
- why it changed;
- what evidence motivated the change;
- what remains uncertain;
- why the change matters for the dissertation.

It should function as a technical lab notebook rather than as a public changelog.

## How to use this file

Each relevant development session should add one dated entry.

Each entry should follow the same structure:

1. `Date`
2. `Scope`
3. `Problem observed`
4. `Hypothesis`
5. `Implementation changes`
6. `Observed result`
7. `Open issues`
8. `Dissertation relevance`

## Writing rules

- Be specific rather than generic.
- Prefer real observed behavior over vague summaries.
- Record both successful fixes and unresolved uncertainty.
- Distinguish clearly between:
  - architectural decisions;
  - resolver-specific fixes;
  - UI or workflow changes;
  - temporary hypotheses.
- If a claim is based on runtime observation, say so explicitly.

---

## Session - 2026-04-06

### Date

2026-04-06

### Scope

- `SCOUT` reorganization and UI refinement
- `pdf_fetcher` Phase 2 development
- Wiley resolver integration and iterative refinement
- specialized resolver observability improvements
- dissertation-note consolidation

### Problem observed

Several different classes of issues were observed during this session.

#### A. Structural and organizational issues

- `SCOUT` had evolved into a substantial workflow but was still behaving partly like a loose page instead of an explicit sub-tool.
- The repository contained local browser-generated files that should not be versioned.
- The organization of the `pdf_fetcher` area needed to better reflect the conceptual hierarchy:
  - domain tool;
  - sub-tool;
  - shared core;
  - local runtime artifacts.

#### B. SCOUT interface issues

- The `SCOUT` sidebar had redundant controls such as:
  - `Save case review`
  - `Check download status`
- Navigation only supported moving forward or backward one case at a time.
- The `Open article link` control was duplicated in the page content and did not fit the final navigation pattern.
- Some visual elements were too noisy or not useful in practice, such as:
  - the `New download candidates now` stat line;
  - a success message shown after reopening articles.
- Streamlit header behavior and card layout needed refinement.

#### C. Phase 2 visibility issues

- The terminal was not refreshing article-by-article during Wiley runs, which made debugging difficult.
- Specialized failures were visible only through coarse statuses and were not informative enough for debugging.

#### D. Wiley integration and runtime issues

- Wiley was not yet present as an active specialized resolver in the live `pdf_fetcher` app.
- The first active Wiley integration used domain recognition that was too narrow.
- Real Wiley cases appeared under multiple hosts such as:
  - `onlinelibrary.wiley.com`
  - `acsess.onlinelibrary.wiley.com`
  - `scijournals.onlinelibrary.wiley.com`
- Some Wiley DOI resolutions led to institutional or legacy landing pages rather than directly reusable PDF flows.
- Some Wiley HTML viewers loaded but stayed in an empty `0 of 0` / `0 de 0` state.
- Some Wiley viewer cases appeared to render a real PDF only inside the Chromium viewer, which suggested that browser-native viewer controls might be usable even when publisher HTML download flows were inconsistent.
- Cookie and consent banners were visibly interfering with some Wiley interactions.

### Hypothesis

The working hypotheses during this session were the following.

#### A. Tool organization hypothesis

`SCOUT` should be treated as a formal sub-tool of `pdf_fetcher`, not as an isolated page or ad hoc script. This would improve:

- conceptual clarity;
- launcher consistency;
- maintainability;
- future reuse of the same UI pattern in other semi-assisted tools.

#### B. Navigation and UI hypothesis

The `SCOUT` UI should prioritize:

- direct operational clarity;
- minimal redundancy;
- fast navigation to the first unresolved case;
- compact advanced actions hidden behind progressive disclosure.

#### C. Wiley integration hypothesis

The validated archive prototype could be transferred into the active app if the surrounding resolver infrastructure was updated consistently.

However, Wiley would likely require iterative refinement rather than a single integration step, because real cases were showing:

- host variability;
- viewer variability;
- access-layer interference;
- mixed HTML and browser-viewer behavior.

#### D. Observability hypothesis

If specialized resolvers exposed richer failure detail without changing their success/failure logic, Phase 2 debugging would become much more efficient and more defensible for dissertation reporting.

### Implementation changes

#### A. Repository and tool organization

- `SCOUT` was moved into a dedicated sub-tool location under:
  - `tools/pdf_fetcher/scout/`
- the new sub-tool layout now includes:
  - `app.py`
  - `browser.py`
  - `README.md`
  - `__init__.py`
- `run_scout.bat` was updated to point to the new entrypoint.
- root and tool-specific requirements were updated locally to reflect the active dependencies.
- browser-generated local profile files were excluded from versioning.

#### B. SCOUT interface and workflow refinement

- removed redundant sidebar buttons:
  - `Save case review`
  - `Check download status`
- removed the unhelpful `New download candidates now` review stat
- moved `Open article link` into the sidebar
- removed the duplicate `Open article link` button from the article-information card
- introduced `Advanced navigation`
- added:
  - `First`
  - `Last`
  - `Go to case`
  - `Go to first pending`
- corrected a navigation bug where `Open article link` could unintentionally trigger a jump to another case
- removed the low-value success message shown when reopening an article
- refined card spacing, height, and visual hierarchy
- cleaned up Streamlit header behavior while preserving access to the native three-dot menu

#### C. Phase 2 orchestration and observability

- Phase 2 terminal refresh was changed to update article-by-article
- a common helper was introduced for richer `pdf_checked_at` formatting
- the specialized resolvers were updated so that controlled failures now include human-readable detail
- the following active specialized resolvers were updated for observability:
  - `frontiers`
  - `mdpi`
  - `springer`
  - `elsevier`
  - `wiley`

#### D. Wiley resolver activation

- created active resolver:
  - `tools/pdf_fetcher/core/resolvers/wiley.py`
- registered Wiley in:
  - config
  - resolver detector
  - Phase 2 pipeline
- integrated Wiley into the active resolver order
- treated `downloaded_wiley` as a specialized success outcome

#### E. Wiley-specific refinements

- widened Wiley attribution and host acceptance to support real Wiley subdomains
- restored stricter viewer readiness validation
- restored additional viewer candidate extraction through DOM and JavaScript inspection
- prevented empty viewer shells from counting as valid viewer success
- added a fallback that attempts the Chromium PDF viewer native save/download control when a real PDF appears to be loaded in the viewer
- added more explicit failure-detail messages such as:
  - `viewer_open_failed_or_empty`
  - `session_request_http_<code>`
  - `session_request_not_pdf`
  - `no_pdf_link_found_on_page`

#### F. Documentation strategy

- expanded `PHASE2_SPECIALIZED_DOWNLOAD_NOTES.md`
- expanded `PDF_FETCHER_APP_NOTES.md`
- updated `CHANGELOG.md`
- created this `DEVELOPMENT_LOG.md` to centralize session-level technical notes

### Observed result

#### A. Organizational result

- `SCOUT` now reads clearly as a sub-tool of `pdf_fetcher`
- the folder structure better matches the intended future model of:
  - master tool / hub
  - domain tool
  - sub-tool

#### B. SCOUT result

- the `SCOUT` interface became cleaner and more coherent
- redundant controls were removed
- navigation became more practical for real review work
- the resulting `SCOUT` layout was considered a reference pattern for future semi-assisted tools

#### C. Phase 2 observability result

- the terminal now exposes progress at a finer granularity during specialized runs
- failures are more interpretable without changing the decision logic of the resolvers

#### D. Wiley result

- Wiley became an active specialized resolver in the live app
- detection became more realistic for real Wiley hosts
- some previously ambiguous Wiley failures became easier to classify
- viewer-empty states are now handled more cautiously
- cases where the PDF genuinely loads in the browser viewer now have an additional recovery path through the native save/download fallback

### Open issues

The following points remain active or only partially resolved.

#### A. Wiley still under refinement

- some Wiley DOI resolutions still appear to land on institutional or legacy article pages
- some cookie or consent interactions may still interfere with Wiley behavior
- some viewer cases may require delayed handling or additional readiness checks
- print-preview behavior was observed as a potential clue in some cases, but the current strategy is to prefer stable save/download actions rather than automating print flows directly

#### B. Cross-publisher cookie handling

It was agreed not to generalize cookie/consent handling immediately across all resolvers.

Current strategy:

1. refine resolver-by-resolver first
2. observe patterns across publishers
3. abstract only after repeated evidence

#### C. Documentation still iterative

The note structure is now much stronger, but it will benefit from continued session-by-session discipline so that no later implementation details are lost.

#### D. Wiley deprioritized in favor of documentation and organization

Near the end of the session, an additional strategic decision was made:

- Wiley refinement was intentionally paused for the moment
- documentation consistency and project-note organization became the immediate priority

This was not because Wiley had been considered solved. On the contrary, the remaining Wiley issues were explicitly acknowledged. The decision was methodological:

- avoid continuing low-level resolver tweaks without first consolidating the development record
- ensure that architectural decisions, error patterns, debugging rationale, and construction strategy were documented while still fresh

#### E. SCOUT retained as a later aid for difficult Wiley cases

Another explicit decision was that some difficult Wiley cases may later be more productively investigated through `SCOUT` rather than by continuing immediate resolver automation work.

This means that:

- `SCOUT` was not understood only as a review tool for existing failed cases
- it was also treated as a possible future support environment for investigating unresolved Wiley behavior in a controlled semi-assisted manner

This is relevant because it links resolver limitations with the broader semi-assisted tooling strategy of the project.

### Dissertation relevance

This session is highly relevant for the dissertation because it documents several methodological themes:

- the move from prototype structure to explicit tool hierarchy
- the use of staged development rather than monolithic implementation
- the importance of resolver-specific empirical debugging
- the distinction between:
  - architecture notes
  - phase notes
  - changelog
  - development log
- the treatment of unresolved runtime behavior as evidence for extension priorities

In dissertation terms, this session provides concrete material for explaining:

- why publisher-specific resolvers are necessary
- how resolver integration is performed
- why observability matters in specialized automation
- how iterative refinement was used to improve robustness without sacrificing auditability
- why development effort was sometimes redirected from code changes to documentation consolidation
- how semi-assisted tooling can complement specialized resolver automation when publisher behavior remains unstable

---

## Prompt template for recovering missing history from other chats

Use the following prompt in another chat if earlier development details were discussed there and should be added to this log.

```text
I am consolidating dissertation-grade development notes for the PDF Fetcher project.

Please read the context of this chat and extract only the concrete development work discussed here.

Return the answer in the following structure:

1. Date or approximate session date
2. Scope
3. Problem observed
4. Hypothesis
5. Implementation changes
6. Observed result
7. Open issues
8. Dissertation relevance

Requirements:
- Be specific and technical.
- Include architectural decisions, UI decisions, resolver decisions, error patterns, fixes, and unresolved issues.
- Distinguish between things that were implemented and things that were only proposed.
- If the chat includes runtime errors or screenshots, summarize what the error showed and how it was interpreted.
- If information is uncertain, label it explicitly as uncertain.
- Do not invent details that are not supported by the chat.
- Write in English.

The goal is to paste your answer into `tools/pdf_fetcher/docs/DEVELOPMENT_LOG.md`.
```

---

## Session - 2026-04-06 (staged workflow, Wiley prototyping, SCOUT prototype)

Historical note:

This session captures an earlier development stage. Some file paths and implementation locations mentioned below refer to the prototype structure that existed at that time and should not be confused with the current active repository layout.

### Date or approximate session date

2026-04-06

### Scope

- clarification and correction of the staged workbook-driven workflow across:
  - Phase 0 (`DOI Enrichment`)
  - Phase 1 (`PDF Basic Download`)
  - Phase 2 (`PDF Specialized Download`)
- refinement of Phase 2 terminal UX and resolver orchestration
- active integration of the `Elsevier` specialized resolver into the main app
- archive-level development and batch validation of a `Wiley` prototype resolver
- creation of dissertation-oriented Markdown documentation for the app and phases
- initial implementation of `S.C.O.U.T.` (`Semi-assisted Case Opening and User Triage`) for failed-case review

### Problem observed

Several concrete issues were discussed and debugged during this session.

#### A. Staged workflow ambiguity

The user clarified that the correct architecture is workbook-driven and not only session-memory-driven:

1. read `Input`
2. run Phase 0
3. write `Current`
4. run Phase 1 from `Current`
5. write `Current`
6. run Phase 2 from the updated `Current`

At the beginning of the session, Phase 2 behavior was being interpreted too loosely as continuation from session memory, which did not fully match the intended design.

#### B. Misleading Phase 2 resolver attribution

A recurring Phase 2 screen showed a single Springer case:

- DOI `10.1007/s11284-013-1078-1`
- source URL hosted on Wiley:
  - `https://esj-journals.onlinelibrary.wiley.com/doi/10.1007/s11284-013-1078-1`
- final Phase 2 status:
  - `not_springer`

This indicated that DOI prefix heuristics alone were insufficient for resolver assignment.

#### C. Phase 2 observability and accounting issues

The user reported that:

- `duplicate_pdf` behavior in Phase 2 was not initially visible in the same useful way as in Phase 1
- the terminal at one point reported:
  - `PDFs available: 678`
  - while the folder actually contained `416`
- resolver statistics were visually truncated in the terminal
- the menu option `[6] Show all resolver stats` appeared but initially did not work
- resolver stats were still displayed in the summary screen even after a separate stats command had been introduced

#### D. Phase 0 progress and refresh issues

The user observed that Phase 0 sometimes appeared to remain in `starting` mode, and the terminal was not clearly refreshing while DOI enrichment was running. A screenshot showed:

- `Last result: searching sources`

This was misleading because the text described the current in-progress action rather than the outcome of a completed record.

Long output paths were also visibly truncated in the terminal rather than wrapped.

#### E. Phase 0 launch issues caused by stale processes

The app occasionally failed to start Phase 0 correctly because multiple `python.exe` processes remained active after interrupted runs. This created the impression that Phase 0 was not starting, or that it was stuck.

#### F. Wiley prototype instability

While testing the archive-level Wiley resolver, multiple runtime patterns were observed:

- some direct requests returned `200` but did not contain valid PDF bytes
- many direct PDF URL requests returned `403`
- some flows opened a viewer shell without a real PDF loading inside it
- some cases reached authentication-like pages (e.g. request username)
- some browser views appeared visually degraded or rudimentary

These issues indicated that Wiley behavior varied substantially across records and sessions.

#### G. Need for semi-assisted failed-case review

After the Wiley batch run, the user requested a semi-assisted prototype capable of:

- opening failed cases one by one
- recording a structured manual decision
- supporting previous/next navigation
- saving manually downloaded PDFs into the expected project filename/path

This became the basis for the `S.C.O.U.T.` prototype.

### Hypothesis

#### A. Workbook state should be authoritative

The correct architecture is:

- Phase 0 starts from `Input`
- each phase writes its result into `Current`
- the next phase reads from the updated `Current`

This hypothesis was explicitly confirmed by the user and guided later corrections.

#### B. Resolver assignment should consider host/source evidence

Resolver selection in Phase 2 should not rely only on DOI prefix patterns. It should also consider:

- `source_url`
- `doi_url`
- publisher host patterns

This was the interpretation used to explain the incorrect Springer attribution for Wiley-hosted content.

#### C. Phase 2 should support both full automation and selective execution

The user wanted Phase 2 to support:

- automatic mode: run all active specialized resolvers in sequence
- manual mode: choose a single resolver to run

This was considered useful both for debugging and for controlled resolver validation.

#### D. Terminal output should remain sparse but informative

The user explicitly preferred:

- essential operational information only
- good confidence/progress visibility
- hidden detail behind an explicit command instead of flooding the summary screen

#### E. Wiley should be validated in archive prototypes before main-app integration

Given the instability of Wiley behavior, the working assumption was that it should first be validated through:

- a single-record prototype
- then a `Current`-driven batch prototype
- with explicit failed-case reporting

before deciding on active integration into the main Phase 2 app.

#### F. Failed-case review needs a semi-assisted interface

The user proposed a manual review workflow that later evolved into `S.C.O.U.T.`. The hypothesis was that failed and unresolved cases need:

- a structured review UI
- controlled case opening
- manual outcome classification
- and reuse later as a semi-assisted mode for publishers without specialized resolvers

### Implementation changes

#### A. Phase workflow corrections

The staged workbook workflow was aligned with the user’s intended architecture. The changes discussed and reported as implemented included:

- addition of `reload_session_from_current(...)` in:
  - `tools/pdf_fetcher/core/excel_io.py`
- wiring of reload behavior between phases in:
  - `tools/pdf_fetcher/ui/terminal/main.py`
- startup preference correction so the app begins from `Input`, not `Current`, when Phase 0 is intended to run
- reconstruction of Phase 1 results from workbook state before running Phase 2

These changes were described as making the app behave consistently with:

- `Input -> Phase 0 -> Current`
- `Current -> Phase 1 -> Current`
- `Current -> Phase 2`

#### B. Phase 2 resolver attribution correction

A correction was reported in:

- `tools/pdf_fetcher/core/resolver_detector.py`

The stated behavior change was:

- if `source_url` clearly points to another known publisher, that evidence can block incorrect assignment to the current resolver

This was specifically used to prevent Wiley-hosted links from being treated as Springer records.

#### C. Phase 2 duplicate accounting correction

A correction was reported in:

- `tools/pdf_fetcher/core/pipeline.py`

The change was:

- `duplicate_pdf` remains visible as a resolver metric
- but no longer inflates `PDFs available`

This was intended to restore consistency between:

- terminal counts
- physical PDFs in the folder

#### D. Phase 2 terminal UX improvements

A series of interface changes were implemented in:

- `tools/pdf_fetcher/ui/terminal/dashboard.py`
- `tools/pdf_fetcher/ui/terminal/main.py`

Implemented changes included:

- direct start from Phase 2 if valid Phase 1 data already exists in `Current`
- startup notice indicating that saved Phase 1 data is available
- support for Phase 2 run modes:
  - automatic
  - manual single-resolver selection
- candidate-count display in manual resolver selection
- explicit final command:
  - `[6] Show all resolver stats`
- separate resolver-stats screen instead of always showing stats in the summary view
- later simplification of the stats screen to a single “back to summary” command
- improved handling of truncated stats in the terminal
- reduced but more strategic refresh behavior during Phase 2

The chat also documented several intermediate bugs that were then fixed:

- `TypeError: TerminalDashboard.build_menu_lines() got an unexpected keyword argument 'info_lines'`
- `[6]` appearing but not being wired into the correct loop
- resolver stats being shown on the main Phase 2 screen even after the separate stats screen was introduced

#### E. Phase 0 display improvements

Reported changes in:

- `tools/pdf_fetcher/core/doi_enrichment.py`
- `tools/pdf_fetcher/ui/terminal/dashboard.py`

Included:

- earlier progress updates so the phase does not appear stuck in `starting`
- distinction between:
  - current action
  - last completed result
- line wrapping for long filesystem paths instead of truncation

This was motivated by a screenshot where:

- `Last result` incorrectly displayed `searching sources`

#### F. Process cleanup for Phase 0

During debugging, hanging `python.exe` processes were identified and terminated because they were interfering with app startup and giving the impression that Phase 0 was not launching correctly.

This was operational cleanup rather than a code change, but it was a concrete debugging step during the session.

#### G. Active Elsevier integration

The session states that `Elsevier` was integrated into the active app in:

- `tools/pdf_fetcher/core/resolvers/elsevier.py`
- `tools/pdf_fetcher/core/config.py`
- `tools/pdf_fetcher/core/resolver_detector.py`
- `tools/pdf_fetcher/core/pipeline.py`

The integration was described as preserving the core archive prototype flow:

- article opening
- `View PDF` discovery
- direct session request
- viewer fallback
- save to official PDF output path via app records

#### H. Archive resolver reorganization

Within:

- `archive/pdf_fetcher/old/types/base`

two folders were created:

- `implemented_resolvers`
- `pending_resolvers`

The user then worked in those folders as the archive prototype area for resolver validation.

#### I. Wiley prototype development

The following archive prototype files were developed and discussed:

- `archive/pdf_fetcher/old/types/base/pending_resolvers/wiley.py`
- `archive/pdf_fetcher/old/types/base/pending_resolvers/wiley_current.py`

Concrete prototype work included:

- creation of a Wiley single-record resolver prototype
- iterative testing of PDF URL patterns such as:
  - `/doi/pdf/...`
  - `/doi/epdf/...`
  - `/doi/pdfdirect/...`
- output to:
  - `Desktop/resolver_tests/wiley`
- final filename convention:
  - `record_id__title.pdf`
- creation of `wiley_current.py` to batch-run against the `Current` workbook
- fixing of `PROJECT_ROOT` import resolution so `tools` could be imported correctly
- addition of failed-case diagnostic export to Excel with columns:
  - `record_id`
  - `title`
  - `doi`
  - `doi_url`
  - `source_url`
  - `output_file`
  - `error_type`
  - `error_message`

One decisive implementation insight was explicitly validated:

- `/doi/pdf/...` often returned `200` but not real PDF bytes
- `/doi/pdfdirect/...` produced the real PDF in a validated case

#### J. Documentation files

The following Markdown documentation files were reported as created or expanded during the session:

- `tools/pdf_fetcher/docs/PHASE0_DOI_ENRICHMENT_NOTES.md`
- `tools/pdf_fetcher/docs/PHASE1_BASIC_DOWNLOAD_NOTES.md`
- `tools/pdf_fetcher/docs/PHASE2_SPECIALIZED_DOWNLOAD_NOTES.md`
- `tools/pdf_fetcher/docs/PDF_FETCHER_APP_NOTES.md`

These were intended as dissertation support notes describing:

- phase objectives
- workflow
- logic
- thresholds
- strengths and limitations

#### K. S.C.O.U.T. prototype creation

The following files were created for `S.C.O.U.T.`:

- `tools/pdf_fetcher/ui/web/scout.py`
- `tools/pdf_fetcher/ui/web/scout_browser.py`
- `tools/pdf_fetcher/run_scout.bat`

These paths should be understood as historical prototype paths for that session. In the current active structure, `SCOUT` was later reorganized into its dedicated sub-tool location under `tools/pdf_fetcher/scout/`.

Concrete implemented functionality included:

- loading a failed-case Excel report
- showing one failed case at a time
- navigation:
  - previous
  - next
- structured outcome classification:
  - `pending_review`
  - `downloaded_manual`
  - `paywalled`
  - `unavailable`
  - `wrong_link`
  - `article_not_found`
  - `other`
- notes field
- saving review results into a review workbook
- support for uploaded manual PDFs being saved into the expected `output_file`

Later, the SCOUT design moved toward a hybrid model:

- Streamlit as the control panel
- a dedicated browser window opened by the tool for the current case
- automatic saving of browser downloads into the expected output path

This hybrid model was concretely implemented in the code shown during the session.

### Observed result

#### A. Staged workflow was clarified and aligned

By the end of the session, the conceptual workflow was clearly established as:

- workbook-driven
- phase-staged
- persistent through `Current`

This resolved earlier confusion about whether Phase 2 should depend on volatile session memory alone.

#### B. Phase 2 became more transparent

The user confirmed that the later Phase 2 version was much closer to the intended design. Improvements included:

- manual vs automatic specialized resolver execution
- cleaner final menus
- explicit resolver stats screen
- better visibility of duplicates and per-resolver outcomes

#### C. Incorrect Springer attribution was explained and corrected

The misleading Springer case was interpreted as host-vs-DOI mismatch and was no longer treated as a valid Springer specialized target after resolver detection was refined.

#### D. Phase 0 became more legible

The user’s complaint that Phase 0 looked stuck in `starting` led to a better display of:

- current record
- current action
- last completed result

This improved user trust in the ongoing DOI enrichment process.

#### E. Elsevier showed concrete Phase 2 utility

One reported Elsevier run processed:

- `158` candidates
- `7` new downloads
- `147` duplicates
- `4` failures due to `TimeoutError`

This indicated that active specialized resolver integration was operational and measurable.

#### F. Wiley prototype produced a strong but incomplete result

The user reported a final Wiley batch outcome of:

- `Candidates : 159`
- `Downloaded : 132`
- `Duplicates : 0`
- `Failed : 27`

This result was interpreted as:

- promising enough to justify further analysis
- not yet stable enough for direct production integration without studying failure categories

#### G. Failed-case reporting became available

The Wiley batch now produced an explicit failed-case Excel workbook, enabling post-run analysis of failure patterns rather than relying only on terminal observation.

#### H. SCOUT was established as an initial semi-assisted review workbench

The initial prototype supported:

- structured case review
- manual PDF saving
- navigation across failed cases

The later hybrid browser idea was also concretely represented in code, although its final methodological direction became contested in the later discussion.

### Open issues

#### A. Wiley remains unresolved for active-app integration

Although the prototype achieved `132/159` successful downloads, unresolved technical issues remain:

- repeated `403` direct-PDF failures
- empty viewer shells / blank `PDF.js`-style views
- authentication-style pages for some cases
- variability across Wiley subflows and sessions

The chat strongly suggests Wiley should remain under prototype analysis before live integration.

#### B. Wiley failure taxonomy was discussed but not fully formalized

The session identified plausible failure classes such as:

- `403_direct_pdf`
- `viewer_blank`
- `request_username`
- `timeout`
- `missing_pdf_link`

However, the chat does not show a completed implementation of this taxonomy in the report itself. This remains an open analytical step.

#### C. SCOUT browser architecture remained unsettled

There was agreement that the user wanted a browser controlled by the platform rather than simply opening URLs in the default browser. A hybrid design was implemented in code, but the later direction of challenge/captcha handling became inconsistent.

This part is therefore technically **uncertain**:

- the code shown later in the chat includes optional challenge auto-resolution mechanisms
- but the broader discussion repeatedly rejected implementing automatic CAPTCHA/WAF bypass

For dissertation logging, this should be treated as an unstable or contested area rather than a settled implementation.

#### D. New DOI-enrichment sources were only proposed

The session discussed possible future Phase 0 extensions:

- `Semantic Scholar`
- `Scopus`
- later LLM assistance for ambiguous cases

These were explicitly exploratory and were not implemented in this session.

### Dissertation relevance

This session is highly relevant to the dissertation because it documents the transition from ad hoc prototypes to a more explicit staged workflow and review architecture.

It provides concrete evidence for:

- why the `PDF Fetcher` was structured as a multi-phase workbook-driven system
- why specialized publisher resolvers are necessary
- why resolver assignment cannot rely only on DOI patterns
- how runtime observability was treated as a methodological concern, not just a convenience
- how archive prototypes were used to validate specialized resolvers before app integration
- why semi-assisted tooling such as `S.C.O.U.T.` is relevant for unresolved or unsupported cases

It also records an important methodological principle for the dissertation:

- unresolved automation outcomes were not discarded
- instead, they were preserved as structured evidence for future resolver design, manual review workflows, and limitation reporting

---

## Session - 2026-04-06 (extended reconstruction from chat)

### 1. Date or approximate session date

2026-04-06

### 2. Scope

- correction and clarification of the staged `PDF Fetcher` workflow
- refinement of Phase 0 (`DOI Enrichment`) progress reporting
- refinement of Phase 2 (`PDF Specialized Download`) orchestration and UI
- active use and validation of specialized resolvers already in the app:
  - `mdpi`
  - `frontiers`
  - `springer`
  - `elsevier`
- archive-level prototype validation of a `Wiley` resolver prior to any active-app integration
- creation of a semi-assisted failed-case review prototype:
  - `S.C.O.U.T.`
- dissertation-note consolidation through Markdown documentation files

### 3. Problem observed

#### A. Workflow confusion between in-memory continuation and workbook continuation

The user explicitly corrected the interpretation of the app lifecycle. The intended model was:

1. read `Input`
2. Phase 0 enriches DOI information
3. write updated workbook to `Current`
4. Phase 1 reads `Current`
5. Phase 1 performs basic PDF download
6. write updated workbook to `Current`
7. Phase 2 reads the latest `Current`
8. Phase 2 processes unresolved or resolver-eligible cases

At the start of the session, Phase 2 behavior was being discussed too much as if it depended mainly on live session state. The user insisted that the persisted workbook state was the correct authority.

#### B. Phase 2 apparently “not running”

The user repeatedly reported that Phase 2 seemed not to run or seemed to stop at a single Springer case. Screenshots showed:

- `Current resolver : springer`
- `Resolver progress : 1/1`
- `Last DOI : 10.1007/s11284-013-1078-1`
- `Last status : not_springer`

This gave the impression that the entire Phase 2 was starting and ending with only one record, despite the project containing many unresolved cases.

#### C. Misleading resolver attribution

The specific Springer case above was later found to correspond to a Wiley-hosted URL:

- `https://esj-journals.onlinelibrary.wiley.com/doi/10.1007/s11284-013-1078-1`

This showed that DOI prefix heuristics alone were insufficient for resolver attribution.

#### D. Missing Phase 2 duplicate semantics and incorrect global PDF counts

The user wanted Phase 2 to mimic Phase 1’s usefulness in distinguishing:

- new downloads
- already existing PDFs (`duplicate_pdf`)

The terminal later showed a mismatch:

- `PDFs available : 678`
- `PDFs in folder : 416`

with `duplicate_pdf` clearly visible in per-resolver stats. This suggested that duplicates were being double-counted into global availability metrics.

#### E. Phase 2 terminal UX problems

Multiple terminal UX problems were observed:

- resolver stats printed inline were truncated when the resolver list grew
- the user anticipated the future addition of many resolvers and considered the existing layout non-scalable
- menu option `[6] Show all resolver stats` was introduced but initially did not work
- a separate resolver-stats view was desired, rather than always printing all resolver stats in the main summary screen
- the user explicitly wanted a clean summary screen and an explicit “show stats” interaction

#### F. Phase 2 run-control limitations

The user wanted Phase 2 to support:

- automatic execution of all resolvers
- manual execution of a single chosen resolver

This was motivated by debugging and selective validation needs.

#### G. Phase 0 refresh and status ambiguity

The user reported that DOI enrichment appeared to “hang” or remain at `starting`. A screenshot showed:

- `Last result : searching sources`

This was interpreted as misleading because the text reflected the current in-progress step rather than the result of a completed record.

#### H. Phase 0 operational instability from hanging Python processes

When Phase 0 seemed stuck or not to start, leftover `python.exe` processes were found. This was interpreted as stale background state interfering with new launches.

#### I. Wiley prototype instability

Archive-level testing of Wiley revealed several concrete failure patterns:

- direct session requests to candidate PDF URLs often returned `403`
- some requests returned `200` but not actual PDF bytes
- some attempts opened viewer shells with no real PDF loaded inside
- some sessions displayed authentication-like pages such as “Request Username”
- visual rendering sometimes appeared degraded or “rudimentary”

These issues suggested significant variation across Wiley records and session states.

#### J. Need for semi-assisted review

After observing unresolved Wiley failures, the user requested a prototype that would:

- open failed cases one by one
- allow manual triage decisions such as:
  - `paywalled`
  - `unavailable`
  - `wrong_link`
  - `article_not_found`
- allow previous/next navigation
- support manual PDF saving into the expected project filename/path

This requirement became the basis for `S.C.O.U.T.`.

### 4. Hypothesis

#### A. Workbook-driven staging is the correct architecture

The user insisted that:

- `Current` is the working workbook
- each phase must consume the latest `Current`
- each phase must write back to `Current`

This was treated as the correct architectural interpretation.

#### B. Resolver attribution must combine DOI and publisher-host evidence

The incorrect Springer example suggested that resolver assignment should use:

- DOI patterns
- `source_url`
- `doi_url`
- publisher hostnames

rather than DOI prefix alone.

#### C. Phase 2 should be resolver-bucket based

The intended Phase 2 behavior was explicitly defined as:

- inspect all relevant cases left after Phase 1
- assign them to resolver buckets
- execute resolver-by-resolver

The user later clarified an additional operating requirement:

- automatic mode for all resolvers
- manual mode for a single selected resolver

#### D. Observability should be explicit but not verbose

The user explicitly favored:

- essential metrics only
- clear confidence/progress indicators
- expanded detail only when requested

This hypothesis guided the final terminal behavior.

#### E. Wiley should remain in historical/archive prototyping until batch behavior is better understood

The working assumption was that Wiley should first be tested through:

- a single-article prototype
- then a `Current`-driven batch prototype
- then failure analysis via an exported report

before any decision on active integration.

#### F. Semi-assisted review should bridge automation gaps

`S.C.O.U.T.` was hypothesized to be useful as:

- an investigative prototype for failed cases
- a future semi-assisted mode for unsupported publishers and unresolved links

### 5. Implementation changes

#### A. Workflow and persistence corrections

The session reports the following workflow-alignment changes:

- `reload_session_from_current(...)` added in:
  - `tools/pdf_fetcher/core/excel_io.py`
- reload logic wired between phases in:
  - `tools/pdf_fetcher/ui/terminal/main.py`
- startup preference corrected so the app begins from `Input` when Phase 0 is intended to run
- reconstruction of Phase 1 results from workbook state before entering Phase 2

These changes were described as enforcing:

- `Input -> Phase 0 -> Current`
- `Current -> Phase 1 -> Current`
- `Current -> Phase 2`

#### B. Phase 2 resolver attribution correction

A correction was reported in:

- `tools/pdf_fetcher/core/resolver_detector.py`

The intended behavior was:

- if the source URL clearly points to another known publisher, that evidence should block incorrect assignment to the current resolver

This was explicitly motivated by Wiley-hosted content being incorrectly sent to Springer.

#### C. Phase 2 duplicate accounting correction

A correction was reported in:

- `tools/pdf_fetcher/core/pipeline.py`

The implemented change was described as:

- `duplicate_pdf` remains visible per resolver
- but no longer increases `PDFs available` globally

This was meant to reconcile terminal counts with actual folder contents.

#### D. Phase 2 terminal design and navigation changes

Implemented changes were reported in:

- `tools/pdf_fetcher/ui/terminal/dashboard.py`
- `tools/pdf_fetcher/ui/terminal/main.py`

The following changes were stated as implemented:

- Phase 2 may start directly from the initial menu if valid Phase 1 data already exists in `Current`
- a startup notice is shown when saved Phase 1 data is available
- Phase 2 supports:
  - automatic mode
  - manual single-resolver mode
- manual selection displays candidate counts
- resolver stats were moved behind an explicit command:
  - `[6] Show all resolver stats`
- a separate stats screen was introduced
- later, that screen was simplified so it offered only a “back to summary” action

The session also described several fixes to intermediate bugs:

- `TerminalDashboard.build_menu_lines() got an unexpected keyword argument 'info_lines'`
- `[6]` appearing but not working because it had been attached to the wrong loop
- the main summary screen still showing resolver stats when those stats were supposed to be hidden until requested

#### E. Phase 0 progress/UI fixes

Reported changes in:

- `tools/pdf_fetcher/core/doi_enrichment.py`
- `tools/pdf_fetcher/ui/terminal/dashboard.py`

included:

- earlier status updates so Phase 0 does not appear stuck in `starting`
- explicit distinction between:
  - current action
  - last completed result
- long path strings now wrap instead of being truncated

#### F. Runtime cleanup

When Phase 0 appeared non-responsive, hanging `python.exe` processes were identified and terminated. This was not a source-code change, but it was a concrete operational debugging step in the session.

#### G. Active integration of `Elsevier`

The session states that `Elsevier` was integrated into the active app in:

- `tools/pdf_fetcher/core/resolvers/elsevier.py`
- `tools/pdf_fetcher/core/config.py`
- `tools/pdf_fetcher/core/resolver_detector.py`
- `tools/pdf_fetcher/core/pipeline.py`

The integration was described as preserving the archive prototype flow:

- article opening
- `View PDF` discovery
- direct session request
- viewer fallback
- save into the official app PDF path

#### H. Archive resolver reorganization

Within:

- `archive/pdf_fetcher/old/types/base`

two folders were created:

- `implemented_resolvers`
- `pending_resolvers`

This was an explicit organizational step to separate mature archive prototypes from prototypes still under development.

#### I. Wiley single-record prototype

The file:

- `archive/pdf_fetcher/old/types/base/pending_resolvers/wiley.py`

was iteratively developed as a single-case prototype. The implemented features reported during the session included:

- article opening through DOI
- lightweight cookie-banner dismissal
- extraction of candidate PDF-related links such as:
  - `/doi/pdf/...`
  - `/doi/epdf/...`
- generation of direct-download URL variants
- validation of PDF bytes
- saving to:
  - `Desktop/resolver_tests/wiley`
- later use of final filename format:
  - `record_id__title.pdf`

The decisive runtime insight that guided the working version was:

- `/doi/pdf/...` could return `200` but not actual PDF bytes
- `/doi/pdfdirect/...` produced the actual PDF in a validated case

#### J. Wiley batch prototype

The file:

- `archive/pdf_fetcher/old/types/base/pending_resolvers/wiley_current.py`

was created to run Wiley cases from `Current`. Reported concrete changes included:

- reading candidates from the `Current` workbook
- identifying Wiley candidates by DOI / DOI link / source URL
- using the working `wiley.py` logic per case
- duplicate detection
- fixing `PROJECT_ROOT` resolution so imports of `tools` would work
- exporting failed cases into an Excel report with:
  - `record_id`
  - `title`
  - `doi`
  - `doi_url`
  - `source_url`
  - `output_file`
  - `error_type`
  - `error_message`

#### K. Dissertation-oriented documentation

The following documentation files were created or expanded:

- `tools/pdf_fetcher/docs/PHASE0_DOI_ENRICHMENT_NOTES.md`
- `tools/pdf_fetcher/docs/PHASE1_BASIC_DOWNLOAD_NOTES.md`
- `tools/pdf_fetcher/docs/PHASE2_SPECIALIZED_DOWNLOAD_NOTES.md`
- `tools/pdf_fetcher/docs/PDF_FETCHER_APP_NOTES.md`

They were explicitly intended as dissertation-grade notes covering:

- rationale
- workflow
- thresholds
- logic
- strengths
- limitations

#### L. S.C.O.U.T. prototype

The following files were created:

- `tools/pdf_fetcher/ui/web/scout.py`
- `tools/pdf_fetcher/ui/web/scout_browser.py`
- `tools/pdf_fetcher/run_scout.bat`

Implemented functionality included:

- loading a failed-case Excel report
- case-by-case review
- previous/next navigation
- structured decision capture
- notes
- manual PDF upload to the expected output file
- review workbook export

Later in the same session, the design shifted to a hybrid model:

- Streamlit control panel
- separate Playwright-driven browser window for the current case
- automatic saving of browser downloads to the expected output path

The code shown in the session demonstrates that this hybrid model was at least partially implemented.

### 6. Observed result

#### A. Workflow clarity improved

By the end of the session, the staged workflow was clearly articulated and aligned with the user’s intended architecture. This resolved earlier conceptual confusion about Phase 2 continuity.

#### B. Phase 2 became more usable

The user explicitly expressed satisfaction with the later Phase 2 interface, especially after:

- adding automatic/manual run modes
- separating resolver stats from the summary screen
- simplifying the resolver-stats view

#### C. Elsevier showed measurable specialized-resolver utility

One concrete reported Elsevier run produced:

- `158` resolver candidates
- `7` new downloads
- `147` duplicates
- `4` failures due to `TimeoutError`

This showed that active specialized resolver integration was already productive and measurable.

#### D. Wiley prototype showed promising but incomplete batch performance

The user reported the final Wiley batch metrics exactly as:

- `Candidates : 159`
- `Downloaded : 132`
- `Duplicates : 0`
- `Failed : 27`

This was interpreted during the session as:

- strong enough to justify further refinement
- not yet stable enough for direct integration into the active app

#### E. Failed-case reporting became available

The Wiley batch report produced an Excel workbook of failures, allowing systematic post-run inspection rather than relying only on terminal logs.

#### F. SCOUT became a concrete semi-assisted prototype

The session moved SCOUT from idea to implementation:

- first as a Streamlit reviewer with manual upload
- then as a hybrid reviewer with a dedicated controlled browser window

### 7. Open issues

#### A. Wiley is still unresolved for active integration

Even after a promising batch run, the following remained unresolved:

- why some `pdfdirect` requests succeed while others return `403`
- why some viewers remain blank
- how many failure cases belong to each distinct error category
- whether Wiley is robust enough for inclusion in the active Phase 2 resolver set

#### B. Wiley failure taxonomy was discussed but not fully formalized

The chat identified potential categories such as:

- `403_direct_pdf`
- `viewer_blank`
- `request_username`
- `timeout`
- `missing_pdf_link`

However, the session does not show a completed formal implementation of that taxonomy into the report itself.

#### C. SCOUT challenge-handling state is uncertain

The user repeatedly requested that `cloudscraper` and `pyautogui` be replicated from `elsevier` into SCOUT. The surrounding discussion repeatedly rejected or resisted this direction. However, the code shown later in the session for:

- `tools/pdf_fetcher/ui/web/scout_browser.py`

contains optional imports and functions related to `cloudscraper` and `pyautogui`.

Therefore, the final intended status of SCOUT challenge handling is **uncertain** in this session record and should be treated cautiously in dissertation writing.

#### D. DOI-enrichment expansion ideas remained conceptual only

The following ideas were discussed but not implemented in this session:

- use of `Semantic Scholar` as a secondary DOI-enrichment source
- potential use of `Scopus` as a secondary source if institutional access is available
- later use of LLM assistance for ambiguous DOI cases

### 8. Dissertation relevance

This session is highly relevant to the dissertation because it documents:

- the move from informal prototype behavior to an explicit workbook-driven staged architecture
- the practical need for publisher-specific specialized resolvers
- the importance of resolver attribution beyond DOI prefix heuristics
- the treatment of observability and terminal UX as part of methodological robustness
- the use of archive prototypes to validate resolvers before active integration
- the design rationale for a semi-assisted review tool (`S.C.O.U.T.`) to bridge unresolved automation gaps

It also provides strong material for describing how automation was treated empirically:

- successes were measured
- failures were logged explicitly
- unresolved cases were preserved for later analysis and semi-assisted review rather than discarded

### 9. Metrics and evidence

The following exact or near-exact metrics and evidence appeared in the chat.

#### A. Elsevier

Reported Phase 2 Elsevier run:

- `Resolver progress : 158/158`
- `Resolver downloads : 7/158`
- `Resolver duplicates : 147/158`
- inferred failures:
  - `4`
- last reported failure type:
  - `resolver_exception_elsevier`
- detail:
  - `TimeoutError: Timeout 30000ms`

Four Elsevier timeout records were explicitly listed:

- `10.1016/b978-0-12-800131-8.00003-0`
- `10.1016/0378-4290(88)90018-4`
- `10.1016/bs.agron.2016.06.003`
- `10.1006/jcrs.1993.1030`

#### B. Phase 0 DOI counts

The session reported:

- initially `121` records without DOI
- one later reported state:
  - `107` still without DOI
  - interpreted as `14` net DOI enrichments

This DOI-enrichment interpretation was explicitly contested by the user as possibly too low relative to expectations. Therefore, the exact enrichment interpretation should be treated with caution unless revalidated from workbook history.

#### C. Wiley batch

Final user-reported Wiley batch result:

- `Candidates : 159`
- `Downloaded : 132`
- `Duplicates : 0`
- `Failed : 27`

Generated failed-case report:

- `C:\Users\Luís Pinto Coelho\Desktop\resolver_tests\wiley\reports\wiley_failed_cases_2026-04-06_14-46-15.xlsx`

#### D. Phase 2 PDF count mismatch

The user observed a concrete mismatch:

- `PDFs available : 678`
- `PDFs in folder : 416`

This was interpreted as duplicate handling inflating global availability counts.

#### E. Phase 0 screenshot evidence

One Phase 0 screenshot showed:

- `Records read : 994`
- `Eligible for lookup : 121`
- `Missing DOI : 121`
- `Enriched DOIs : 6`
- `Needs review : 0`
- `Unresolved : 8`
- `Auto-applied rate : 4.96%`
- `Potential match rate : 4.96%`
- `Records processed : 14`
- `Records remaining : 107`
- `Last result : searching sources`

This screenshot was specifically used to argue that the UI wording was misleading.

### 10. Alternatives considered or rejected

#### A. Rejected: treating Phase 2 as session-memory-only continuation

The user explicitly rejected the idea that Phase 2 should depend only on what was left in memory during the current live app session. The workbook-driven model was treated as the correct design.

#### B. Rejected: always listing all resolver stats in the main summary screen

The user preferred:

- compact summary by default
- explicit command for expanded resolver statistics

Therefore, always-on full resolver stats in the main terminal view was rejected.

#### C. Rejected or postponed: generic abstraction of cookie handling across publishers

The session indicated that cookie/consent handling should not yet be generalized. The working approach remained:

1. refine publisher by publisher
2. observe recurring patterns
3. abstract later only if warranted

#### D. Rejected or postponed: immediate Wiley integration into the active app

Although Wiley showed promising prototype performance, the session favored:

- archive-level prototyping first
- error analysis second
- app integration only later if warranted

#### E. Proposed but not implemented: new DOI-enrichment sources

The following ideas were discussed but not implemented:

- `Semantic Scholar`
- `Scopus`
- LLM-assisted DOI ambiguity handling

These were exploratory design considerations only.

#### F. SCOUT browser embedding

One design tension concerned whether SCOUT should:

- embed a browser directly inside the platform UI
- or use a separate controlled browser window

The practical implementation moved toward:

- Streamlit control panel
- dedicated browser window

Full embedded-browser behavior was not achieved in this session.

### 11. State at that time vs current-state implications

#### A. Historical prototype paths vs active app paths

This session worked across two different layers:

1. **Historical/archive prototype layer**
   - `archive/pdf_fetcher/old/types/base/...`
   - used for resolver experimentation (`elsevier`, `wiley`, etc.)
2. **Current active implementation layer**
   - `tools/pdf_fetcher/...`
   - used for the live staged app, terminal UI, and SCOUT prototype

For dissertation writing, these layers must not be conflated. The archive prototypes are evidence of construction strategy and validation history, not necessarily current production behavior.

#### B. Active-app state at that time

At the time of this session:

- `Elsevier` was described as actively integrated into the main Phase 2 app
- `MDPI`, `Frontiers`, and `Springer` were already established active specialized resolvers
- Wiley was still in archive prototype validation and failed-case analysis

#### C. SCOUT state at that time

At this stage, SCOUT had become a concrete prototype, but its final architecture and especially its challenge-handling policy remained unsettled. For dissertation use, SCOUT should therefore be described as:

- implemented as a prototype
- motivated by manual-review needs
- still evolving in browser/session behavior

#### D. Implication for current-state interpretation

Because the session contains both stable implemented changes and contested prototype steps, later dissertation writing should distinguish:

- clearly validated workflow and UI changes
- active resolver integrations known to be in the app
- archive-only publisher prototypes
- uncertain or transient prototype states, especially where interrupted discussion or conflicting requests occurred
