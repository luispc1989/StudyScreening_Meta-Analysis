# Dissertation Notes Prompt Rules

## Purpose

Use these rules whenever writing or updating dissertation notes in this
repository. Treat every dissertation note as part of the project's research
record, not as a changelog or informal development log.

## Non-Negotiable Rules

- Write analytically, not casually.
- Explain what was done, why it was done, how it works, what problem it solved,
  what frictions or tradeoffs appeared, what was validated, what remains
  provisional, and why the change matters for the dissertation.
- Preserve reasoning, constraints, tradeoffs, and consequences, not only the
  final implementation state.
- Distinguish implemented from validated. Do not treat implementation as proof.
- Distinguish intended outcome from observed consequence whenever relevant.
- Preserve evidence and traceability whenever available.
- Use direct, precise, restrained language.
- Do not mention Codex, Claude Code, AI assistance, prompting, or code
  generation.

## Metadata for Substantial Notes

For every substantial note, include metadata whenever relevant:

- Date
- Area / Module
- Decision Status
- Current Source of Truth / Persistence
- Related Files / Routes / Components
- Evidence / References

Accepted decision-status labels:

- `prototype`
- `provisional`
- `validated`
- `replaced`

Evidence may include:

- commits
- screenshots
- issue or bug references
- failing or working examples
- test notes
- affected routes, pages, files, or modules

## Required Structure for Substantial Notes

Every substantial note must include:

### What Was Done

State concretely what was implemented, changed, removed, restructured, or fixed.
Do not use vague labels.

### Why It Was Done

State the reason for the change. This may be architectural, usability-related,
methodological, persistence-related, workflow-related, semantic, or branding-
related.

### Alternatives Considered

Record the meaningful alternative, if one existed, and explain why it was not
chosen. If no real alternative existed, say so explicitly.

### Implementation Logic

Explain how the solution works conceptually. State what was separated, what
became the source of truth, how the flow behaves, and what system boundary or
design assumption the change formalizes.

### Bugs, Frictions, or Constraints

Record bugs, incorrect assumptions, edge cases, prototype limitations,
state-management problems, tradeoffs, and reasons the solution remains
provisional when relevant.

### Validation / What Was Confirmed

State what was actually checked and what is known at the current stage. Make
clear whether the change is:

- implemented only
- observed working
- partially working
- not yet validated

### Impact

State the architectural, workflow, continuity, platform, or project-level
impact of the change.

### Dissertation Relevance

State explicitly why the change matters for the dissertation narrative,
architectural argument, methodological structure, or future migration logic.

### Evidence / Traceability

When available, tie the note to concrete implementation evidence.

## Frontend Rule

For `PrismaLab` frontend work, do not describe changes as merely visual unless
they are purely cosmetic. Evaluate frontend changes in terms of:

- access semantics
- navigation semantics
- workflow structure
- project continuity
- account behavior
- local-first logic
- assistant behavior
- platform-versus-tool distinction
- desktop migration implications

## Persistence / Source-of-Truth Rule

Whenever continuity, memory, sessions, history, recovery, saved state, or
persistence are mentioned, state where that state currently lives.

Examples:

- browser local storage
- Excel workbook
- SQLite database
- temporary prototype state
- in-memory only state

Always distinguish current prototype persistence from intended final
architecture.

## Prototype Honesty Rule

Describe prototypes honestly.

- Do not present prototype workarounds as final architecture.
- Do not present scaffolded work as validated.
- Do not present happy-path confirmation as full validation.
- State clearly whether something is implemented, scaffolded, partially
  working, conceptually planned, or still dependent on later desktop or
  database work.

## Decision Status Rule

Use decision status consistently:

- `prototype` = exploratory, temporary, or intentionally incomplete
- `provisional` = currently adopted but likely to change
- `validated` = implemented and checked sufficiently for the current stage
- `replaced` = historically important but superseded

If one decision replaces another, record that replacement explicitly and explain
why.

## Tooling Neutrality Rule

Keep dissertation notes tooling-neutral.

- Do not mention Codex.
- Do not mention Claude Code.
- Do not mention AI assistance.
- Do not mention prompting.
- Do not mention code generation.

Describe only the system, the implementation, the constraints, the reasoning,
and the consequences.

## Naming Rule

Use project terminology consistently:

- `PrismaLab` = platform
- `Ray` = assistant
- `account` = access/authentication concept
- `profile` = in-app identity/settings concept
- `Home` = workspace-level entry page
- `Workflow` = phase-specific work area

If naming changes, update the notes and explain why the naming changed.

## Tone Rules

- Be serious.
- Be precise.
- Be restrained.
- Be analytical.
- Be explicit.

Prefer formulations such as:

- "This was implemented because..."
- "This revealed that..."
- "The architectural consequence was..."
- "This remained provisional because..."

Do not write in product, marketing, or casual-dev tone.

## Anti-Pattern List

Do not write notes like these:

- "improved UI"
- "refined app"
- "made things cleaner"
- "fixed some bugs in login"
- "updated Ray"
- "made dashboard nicer"
- "improved flow"
- "added settings"
- "cleaned up persistence"
- "tested the new route"

Replace vague summaries with analytical statements that explain rationale,
constraints, validation status, and consequences.

## Update Rule

Whenever dissertation-relevant work is completed:

1. update the appropriate notes file;
2. include metadata for substantial changes;
3. follow the required structure in this file;
4. include rationale, alternatives, implementation logic, bugs/frictions,
   validation, impact, and dissertation relevance;
5. record the current source of truth where relevant;
6. include evidence or traceability when available;
7. do not leave major implementation phases undocumented;
8. prefer preserving too much reasoning rather than too little.

## Reusable Note Template

### Title

### Metadata

- Date:
- Area / Module:
- Decision Status:
- Current Source of Truth / Persistence:
- Related Files / Routes / Components:
- Evidence / References:

### What Was Done

### Why It Was Done

### Alternatives Considered

### Implementation Logic

### Bugs, Frictions, or Constraints

### Validation / What Was Confirmed

### Impact

### Dissertation Relevance
