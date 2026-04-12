# Dissertation Notes Writing Rules

## Purpose

This file defines the writing rules that should always be followed when adding
or updating dissertation notes in this repository.

Its purpose is to keep the dissertation documentation:

- consistent;
- analytically useful;
- justified rather than merely descriptive;
- suitable for later conversion into dissertation prose.

Before writing or updating dissertation notes, this file should be read first.

---

## Core Principle

Dissertation notes must not read like casual development scraps or generic
changelogs.

They must always explain:

- what was implemented;
- why it was implemented;
- what problem it solved;
- what architectural or methodological logic justified it;
- what bugs, frictions, or tradeoffs appeared;
- what impact the change had on the project direction.

The notes should help answer not only:

- "What was done?"

but also:

- "Why was this the right thing to do at this stage?"
- "What did this reveal about the system?"
- "Why does this matter for the dissertation?"

---

## Mandatory Writing Structure

Whenever substantial work is added to the dissertation notes, try to document it
using the following logic.

### 1. What Was Done

State clearly what was implemented or changed.

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
- persistence/state-management reason;
- product-semantics reason;
- branding/system-identity reason.

This section is mandatory because the dissertation must justify decisions, not
just list them.

### 3. Implementation Logic

Explain the internal logic of the solution.

This means describing:

- how the change works conceptually;
- what was separated from what;
- what source of truth is being used;
- how the flow behaves;
- what design assumptions it encodes.

This is especially important when the implementation reflects a broader system
idea rather than a small isolated fix.

### 4. Bugs, Frictions, or Constraints

Whenever relevant, explicitly document:

- bugs encountered;
- incorrect assumptions discovered;
- state-management problems;
- prototype limitations;
- reasons why a simpler-looking approach was not sufficient.

This is important because many dissertation-relevant decisions emerge from
practical friction rather than from abstract planning.

Do not hide implementation problems. They are often methodologically useful.

### 5. Impact

Always describe the impact of the change.

Examples of impact:

- clearer architecture;
- better continuity across sessions;
- better alignment with local-first assumptions;
- better separation between workspace and workflow;
- better basis for future desktop migration;
- stronger dissertation narrative.

This section should answer:

- "So what changed for the system as a whole?"

### 6. Dissertation Relevance

Whenever the change affects architecture, workflow logic, methodology, project
memory, or product framing, explicitly explain why it matters for the
dissertation.

Examples:

- it clarifies a methodological stage boundary;
- it demonstrates local-first design rationale;
- it shows why a database is needed instead of browser storage;
- it formalizes the distinction between platform and assistant;
- it turns visual prototyping into architectural evidence.

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
- the consequence.

Short notes are acceptable only for truly minor changes.

For important changes, prefer detailed notes over compressed summaries.

---

## Frontend-Specific Rule

For `PrismaLab` frontend work, notes must not describe changes as merely
visual unless they are purely cosmetic.

Whenever frontend changes are logged, they should be evaluated in terms of:

- access semantics;
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

Whenever notes mention saved state, continuity, sessions, or recovery, they
must clearly state where that state currently lives.

For example:

- browser local storage;
- Excel workbook;
- SQLite database;
- temporary prototype state.

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
- what still depends on future desktop or database work.

Do not describe a prototype workaround as if it were the final architecture.

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

These are too weak, too vague, and not reusable for dissertation writing.

Instead, rewrite them into analytical form such as:

- "The login flow was restructured around local account selection because the
  browser prototype already knows which accounts exist on the current machine."
- "The Ray history became account-scoped in order to test whether assistant
  memory should behave as part of local project continuity."

---

## Update Rule

Whenever new dissertation-relevant work is completed:

1. update the appropriate notes file;
2. follow the structure in this document;
3. include strategy, rationale, bugs, and impact;
4. avoid leaving major implementation phases undocumented;
5. prefer recording too much reasoning rather than too little.

---

## Final Rule

The dissertation notes are not only memory aids.

They are part of the project's research record.

They must therefore preserve the reasoning process behind the evolving system,
especially where implementation decisions reveal:

- methodological structure;
- architectural direction;
- limitations of current prototypes;
- justification for future migration steps.
