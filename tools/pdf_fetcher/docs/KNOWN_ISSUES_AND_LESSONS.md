# Known Issues and Lessons

## Purpose

This file captures the kinds of problems that are especially valuable for dissertation writing:

- bugs that revealed design weaknesses;
- workflow inconsistencies;
- session/persistence failures;
- performance issues;
- lessons that influenced architectural decisions.

It is not a troubleshooting manual. It is a record of relevant technical lessons.

## 1. State ambiguity is a real methodological problem

One of the most important lessons of the project is that state ambiguity is not only a programming inconvenience. It directly affects interpretation.

Examples:

- a rerun of `Phase 0` on an already enriched workbook changes the apparent number of missing DOI cases;
- a manual review session can appear to “lose” cases if the wrong SCOUT session file is reopened;
- a generic `Current` workbook hides which phase actually produced the current state.

### Lesson

State must be:

- explicit;
- phase-aware;
- resumable;
- interpretable after the fact.

This is one of the reasons why the project moved toward per-phase current workbooks.

## 2. Resume logic is harder than simple file loading

Another major lesson was that “continue previous run” is not just a convenience feature. It changes the semantics of the workflow.

If a user continues a session:

- `Phase 0` should not behave as if it is starting from the original input;
- SCOUT should not rebuild its world only from the latest unresolved rows in the workbook;
- the app must distinguish between current operational state and original baseline state.

### Lesson

Continuation needs explicit design rules. Without them, the app can become operationally misleading even when technically functional.

## 3. Terminal responsiveness matters for trust

Several issues were observed around:

- delayed exits;
- pauses after key presses;
- transitions that appeared frozen;
- redraws that looked like blocking.

Even when the underlying process was still working correctly, the user experience created uncertainty.

### Lesson

For a research-support application, responsiveness and visible progress matter because they influence trust in the workflow.

This led to changes such as:

- explicit loading messages;
- lighter checkpoints;
- reduced redundant reloads;
- more controlled dashboard refresh logic.

## 4. Specialized resolver work is not just feature expansion

Adding new resolvers revealed that specialized retrieval is not simply a matter of supporting more publishers. It also creates:

- more UI/monitoring needs;
- more error detail requirements;
- more performance variation;
- more importance for structured statuses.

### Lesson

Specialized automation requires observability. Without clear failure detail, resolver development becomes guesswork.

This is why explicit statuses and failure detail logging became more important over time.

## 5. SCOUT exposed the limits of workbook-only session memory

The SCOUT made one limitation especially visible: Excel is good as a phase handoff format, but less ideal as the sole source of truth for rich interactive session memory.

Observed issues included:

- reopening the wrong SCOUT case report;
- confusion between current and older reports;
- persistence complexity for review decisions, notes, and staged edits.

### Lesson

Interactive review memory is easier to reason about when treated as a structured internal state rather than as a set of loosely related Excel artifacts.

This is one of the strongest arguments for a future local project database.

## 6. “What was originally true?” is not always recoverable later

The Phase 0 baseline issue was a strong example of this.

Once a workbook has been updated, some original values are no longer recoverable from the workbook alone unless they were explicitly preserved.

### Lesson

If a value matters for interpretation later, it should be stored explicitly at the time it is first known.

This is a key dissertation lesson because it links software design directly to methodological validity.

## 7. File organization is part of usability

As the project grew, file organization stopped being cosmetic and became operationally important.

Problems observed:

- too many similarly named files;
- unclear distinction between current state and old artifacts;
- risk of reusing old SCOUT reports unintentionally.

### Lesson

Folder structure and naming are part of workflow design. They affect:

- error prevention;
- explainability;
- project portability;
- user confidence.

## 8. Why a local database now makes sense

The project started in a workbook-driven way, which was appropriate and practical. But several recurrent issues now point in the same direction:

- session continuity;
- phase continuity;
- project reopening years later;
- project sharing across users and locations;
- incremental addition of new articles to a previously reviewed project.

### Lesson

The future architecture should likely treat:

- Excel as import/export;
- a local database as the internal source of truth;
- the project itself as a portable local file.

The first practical implication of this is that the database should preserve
both:

- a canonical article entity;
- the raw imported source rows and their provenance.

Without both layers, importing from multiple bibliographic databases would risk
either losing auditability or overfitting the system to one source format.

## 9. Future launcher/hub implications

The expected future `PrismaLab` application changes the scale of the problem.

Once multiple tools exist in the same ecosystem, the application will need:

- shared project state;
- shared configuration;
- a central place for credentials and tool settings;
- stable project reopening rules;
- cleaner separation between project memory and exported artifacts.

### Lesson

The more the system evolves into a multi-tool workflow environment, the less viable it becomes to depend only on Excel files as the living operational layer.

This also means the first database version must accept incomplete metadata and
must not assume that fields such as DOI, abstract, or author email are always
available in every import source.

## 10. Remaining limitations worth acknowledging

Some current limitations remain important for dissertation discussion:

- Excel saves are still heavier than database updates would be;
- browser-heavy publisher automation remains variable in runtime behavior;
- some states are still hard to reconstruct retroactively if they were not explicitly preserved;
- anti-bot and publisher controls remain a real operational constraint;
- local tooling is strong for reproducibility, but collaboration portability will improve significantly only when the future project-file/database model is introduced.

## 11. Streamlit widget state can become a design constraint

The `S.C.O.U.T.` exposed a more subtle frontend issue: Streamlit widgets are convenient, but they impose rules on when widget state can be mutated.

One concrete example occurred when a saved PDF was erased and the app tried to reset the decision widget immediately. Streamlit raised an error because the widget value was being changed after instantiation in the same run.

### Lesson

In interactive research interfaces, frontend state rules are not trivial implementation details. They can affect:

- reversibility of user actions;
- apparent correctness of statuses;
- confidence in whether the UI truly reflects the underlying state.

This also reinforces why the future master app is likely better suited to a dedicated frontend framework.

## 12. Copy-to-clipboard UX is harder than it looks in lightweight app frameworks

An apparently simple requirement emerged in the SCOUT: copying DOI or DOI link values quickly.

Several variants were explored:

- direct clickable values;
- separate copy buttons;
- inline icons;
- HTML/JavaScript-based clipboard actions.

The result was that visually attractive solutions were not always stable, and stable solutions did not always preserve layout quality.

### Lesson

Small user-experience details can reveal framework limits. This was a useful reminder that:

- clean UI is not only about whether a feature works;
- stable interaction patterns should not damage visual coherence;
- not every seemingly simple interaction is equally well supported in all frontend stacks.

## 13. A master app needs different UX goals from a tool prototype

The project originally evolved through tool-specific interfaces, especially:

- terminal workflows;
- Streamlit prototypes;
- SCOUT-specific interactive pages.

As planning shifted toward a broader `Study Screening Toolkit`, it became clear that the top-level application should not look like an internal launcher or a developer control panel.

### Lesson

There is an important distinction between:

- a prototyping interface for building one tool quickly;
- a project-oriented application that should remain understandable across multiple phases and tools.

This is a key reason why the future app master is now expected to be:

- phase-oriented;
- project-oriented;
- likely implemented in `React / Next.js` rather than pure Streamlit.
