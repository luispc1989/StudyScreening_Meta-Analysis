# Dissertation Notes Writing Rules

## Purpose

This file defines the writing rules that must always be followed when adding or
updating dissertation notes in this repository.

Its purpose is to keep the dissertation documentation:

- consistent;
- analytically useful;
- justified rather than merely descriptive;
- traceable to concrete implementation work;
- suitable for later conversion into dissertation prose.

Before writing or updating dissertation notes, this file should be read first.

---

## Scope

These notes are part of the project's research record.

They must preserve not only what changed, but also the reasoning, constraints,
tradeoffs, and consequences that shaped the evolving system.

They must not be treated as casual development scraps, generic progress logs,
or vague summaries of work completed.

---

## Core Principle

Dissertation notes must not read like casual development scraps or generic
changelogs.

They must always explain:

- what was implemented;
- why it was implemented;
- what problem it solved;
- what alternatives were considered, when relevant;
- what architectural or methodological logic justified it;
- what bugs, frictions, constraints, or tradeoffs appeared;
- what was actually validated, and what remains provisional;
- what impact the change had on the project direction.

The notes should help answer not only:

- "What was done?"

but also:

- "Why was this the right thing to do at this stage?"
- "What alternative was not chosen, and why?"
- "What did this reveal about the system?"
- "What was confirmed versus merely implemented?"
- "Why does this matter for the dissertation?"

---

## Mandatory Metadata for Substantial Notes

Whenever substantial work is added to the dissertation notes, include the
following metadata whenever relevant:

- Date;
- Area or module;
- Decision status;
- Current source of truth or persistence location, if relevant;
- Related files, components, routes, or modules, if useful;
- Evidence references, when available.

Accepted decision-status labels:

- `prototype`
- `provisional`
- `validated`
- `replaced`

Evidence references may include:

- commit(s);
- screenshot(s);
- issue or bug references;
- failing or working examples;
- test notes;
- affected routes, pages, or modules.

This metadata is important because later dissertation writing may require
reconnecting the analytical note to concrete implementation evidence.

---

## Mandatory Writing Structure

Whenever substantial work is added to the dissertation notes, it must be
documented using the following logic.

### 1. What Was Done

State clearly what was implemented, changed, restructured, removed, or fixed.

This section should be concrete and factual.

Examples:

- a local recovery flow was implemented;
- the `Ray` assistant history became account-scoped;
- the entry route changed from `/app/dashboard` to `/app`;
- the home page was separated from the workflow area.

Avoid vague statements such as:

- "improved UI"
- "refined app"
- "made things cleaner"

These phrases are not specific enough for dissertation use.

### 2. Why It Was Done

Every note must explain the reason behind the implementation.

Possible types of reasons:

- architectural reason;
- usability reason;
- methodological reason;
- persistence or state-management reason;
- workflow reason;
- product-semantics reason;
- branding or system-identity reason.

This section is mandatory because the dissertation must justify decisions, not
just list them.

### 3. Alternatives Considered

Whenever a real alternative existed, briefly document it and explain why it was
not chosen at this stage.

This is important because dissertation writing should not present the implemented
solution as if it were the only possible path.

Examples of useful alternatives documentation:

- a browser-only shortcut was rejected because it weakened account continuity;
- a purely visual route merge was rejected because it blurred workflow
  boundaries;
- a local-storage solution was kept temporarily, but not treated as the final
  persistence architecture.

If no meaningful alternative existed, state that explicitly rather than leaving
the question ambiguous.

### 4. Implementation Logic

Explain the internal logic of the solution.

This means describing:

- how the change works conceptually;
- what was separated from what;
- what source of truth is being used;
- how the flow behaves;
- what design assumptions it encodes;
- what system boundary or semantic distinction it formalizes.

This is especially important when the implementation reflects a broader system
idea rather than a small isolated fix.

### 5. Bugs, Frictions, or Constraints

Whenever relevant, explicitly document:

- bugs encountered;
- incorrect assumptions discovered;
- state-management problems;
- prototype limitations;
- edge cases;
- reasons why a simpler-looking approach was not sufficient;
- reasons why the implementation remains provisional.

This is important because many dissertation-relevant decisions emerge from
practical friction rather than from abstract planning.

Do not hide implementation problems. They are often methodologically useful.

### 6. Validation / What Was Confirmed

Every substantial note should explain how the change was checked and what is
actually known at the current stage.

Possible forms of validation include:

- manual testing;
- real workflow use;
- route or state verification;
- partial confirmation only;
- happy-path confirmation only;
- scaffolded but not meaningfully validated.

The note must distinguish between:

- implemented;
- observed working;
- partially working;
- not yet validated.

This distinction is necessary because dissertation notes must not treat
implementation and verification as the same thing.

### 7. Impact

Always describe the impact of the change.

Examples of impact:

- clearer architecture;
- better continuity across sessions;
- better alignment with local-first assumptions;
- better separation between workspace and workflow;
- better basis for future desktop migration;
- stronger distinction between platform and assistant;
- stronger dissertation narrative.

This section should answer:

- "So what changed for the system as a whole?"

### 8. Dissertation Relevance

Whenever the change affects architecture, workflow logic, methodology, project
memory, product framing, or system boundaries, explicitly explain why it matters
for the dissertation.

Examples:

- it clarifies a methodological stage boundary;
- it demonstrates local-first design rationale;
- it shows why a database is needed instead of browser storage;
- it formalizes the distinction between platform and assistant;
- it turns visual prototyping into architectural evidence;
- it reveals a limitation of the browser prototype that justifies future
  migration steps.

### 9. Evidence / Traceability

Whenever possible, include traceable references to concrete implementation
material.

Possible references include:

- affected files or folders;
- relevant routes or pages;
- commit(s);
- screenshots;
- failing cases;
- test notes;
- before/after prototype states.

This section exists so that the analytical note can later be tied back to
concrete development evidence instead of relying only on memory.

---

## Tone Rules

Dissertation notes should be:

- serious;
- precise;
- restrained;
- analytical;
- explicit.

They should not sound like:

- marketing copy;
- product hype;
- casual dev chat;
- vague progress updates.

Preferred tone:

- "This was implemented because..."
- "This revealed that..."
- "This is relevant because..."
- "The architectural consequence was..."
- "This remained provisional because..."

Avoid tone such as:

- "This was awesome"
- "This looks better now"
- "We improved the UX a lot"

These are too informal and too weak analytically.

---

## Required Level of Detail

Notes must be detailed enough that, later, they can be transformed into
dissertation writing without having to reconstruct the reasoning from memory.

That means the notes should preserve:

- the decision;
- the rationale;
- the implementation direction;
- the observed problem;
- the alternative, when relevant;
- the validation status;
- the consequence.

Short notes are acceptable only for truly minor changes.

For minor changes, the note may be compressed, but it must still preserve at
least:

- what changed;
- why it changed;
- whether it was actually validated;
- whether it affects architecture, workflow, persistence, or system semantics.

For important changes, prefer detailed notes over compressed summaries.

---

## Frontend-Specific Rule

For `PrismaLab` frontend work, notes must not describe changes as merely visual
unless they are purely cosmetic.

Whenever frontend changes are logged, they should be evaluated in terms of:

- access semantics;
- navigation semantics;
- workflow structure;
- project continuity;
- account behavior;
- local-first logic;
- assistant behavior;
- platform-versus-tool distinction;
- desktop migration implications.

This is especially important because the frontend prototype is part of the
architectural story of the dissertation, not just a design exercise.

---

## Persistence and Source-of-Truth Rule

Whenever notes mention saved state, continuity, sessions, recovery, memory, or
history, they must clearly state where that state currently lives.

For example:

- browser local storage;
- Excel workbook;
- SQLite database;
- temporary prototype state;
- in-memory only state.

This avoids confusion between:

- current prototype persistence;
- intended final persistence architecture.

This distinction is mandatory.

---

## Prototype Honesty Rule

If something is still a prototype, it must be described honestly as a prototype.

Notes should explicitly distinguish between:

- what is already implemented;
- what is only scaffolded;
- what is only conceptually planned;
- what is partially working;
- what still depends on future desktop or database work.

Do not describe a prototype workaround as if it were the final architecture.

Do not describe a happy-path confirmation as if the feature were fully validated.

---

## Decision Status Rule

Use decision status consistently in substantial notes:

- `prototype` = exploratory, temporary, or intentionally incomplete;
- `provisional` = currently adopted, but still likely to change;
- `validated` = implemented and checked sufficiently for the current project
  stage;
- `replaced` = historically important, but superseded by a later decision.

If a later decision replaces an earlier one, do not silently overwrite the
earlier reasoning. Record that the earlier solution was replaced and explain why.

This is important because dissertation writing often depends on the historical
sequence of decisions, not only on the final state.

---

## Intended vs Observed Consequence Rule

Whenever relevant, distinguish between:

- the intended reason for a change; and
- the consequence that was actually observed after implementation.

This matters because a change may be introduced for one reason but reveal
something else that becomes methodologically or architecturally more important.

Unexpected consequences should not be omitted.

They are often among the most dissertation-relevant outcomes.

---

## Tooling Neutrality Rule

Do not mention Codex, Claude Code, AI assistance, prompting, code generation,
or tooling support in the dissertation notes.

The notes must describe the work as project implementation, architectural
decisions, design reasoning, constraints, and consequences.

They must not read like logs of how code or text was produced.

The dissertation notes are concerned with the system and its evolution, not with
tool provenance.

---

## Naming Rule

Use project terminology consistently.

Examples:

- `PrismaLab` = platform;
- `Ray` = assistant;
- `account` = access/authentication concept;
- `profile` = in-app identity/settings concept;
- `Home` = workspace-level entry page;
- `Workflow` = phase-specific work area.

If naming changes during implementation, update the notes accordingly and
explain why the naming changed.

---

## Anti-Pattern List

Do not write dissertation notes like this:

- "Fixed some bugs in login"
- "Updated Ray"
- "Made dashboard nicer"
- "Improved flow"
- "Added settings"
- "Cleaned up persistence"
- "Tested the new route"

These are too weak, too vague, and not reusable for dissertation writing.

Instead, rewrite them into analytical form such as:

- "The login flow was restructured around local account selection because the
  browser prototype already knows which accounts exist on the current machine."
- "The `Ray` history became account-scoped in order to test whether assistant
  memory should behave as part of local project continuity."
- "The route structure was separated into `Home` and `Workflow` areas because
  the previous entry model mixed workspace access with phase-specific work."
- "Local persistence remained in browser storage at this stage, but the change
  revealed that future database-backed continuity will be required."
- "The route worked in the main happy path, but validation remained incomplete
  because recovery and back-navigation states were not yet tested."

---

## Update Rule

Whenever new dissertation-relevant work is completed:

1. update the appropriate notes file;
2. include the relevant metadata for substantial changes;
3. follow the structure in this document;
4. include rationale, alternatives, implementation logic, bugs, validation,
   impact, and dissertation relevance;
5. record the current source of truth where relevant;
6. include evidence references when available;
7. avoid leaving major implementation phases undocumented;
8. prefer recording too much reasoning rather than too little.

---

## Recommended Note Skeleton

Use the following structure for substantial notes:

### Title

A precise title describing the implemented change.

### Metadata

- Date:
- Area / Module:
- Decision Status:
- Current Source of Truth / Persistence:
- Related Files / Routes / Components:
- Evidence / References:

### What Was Done

State clearly what was implemented or changed.

### Why It Was Done

Explain the reason for the change.

### Alternatives Considered

Record the main alternative, if relevant, and why it was not chosen.

### Implementation Logic

Explain how the solution works conceptually and what system logic it encodes.

### Bugs, Frictions, or Constraints

Document implementation problems, edge cases, incorrect assumptions, or reasons
the solution remains limited.

### Validation / What Was Confirmed

State what was tested or observed working, and what remains unvalidated.

### Impact

Explain the architectural, workflow, continuity, or product-level impact.

### Dissertation Relevance

Explain why this change matters for the dissertation narrative, methodology, or
architectural argument.

---

## Final Rule

The dissertation notes are not only memory aids.

They are part of the project's research record.

They must therefore preserve the reasoning process behind the evolving system,
especially where implementation decisions reveal:

- methodological structure;
- architectural direction;
- limitations of current prototypes;
- justification for future migration steps;
- the difference between intended design and observed system behavior.

If a note would not help support later dissertation writing, it is not yet
written at the right level.
