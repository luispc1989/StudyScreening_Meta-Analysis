# Final Delivery Cleanup Checklist

## Purpose

This file records what should be reviewed, removed, simplified, or cleaned up
before the final dissertation submission or final software delivery snapshot.

It is intentionally conservative. Items should only be removed after checking
whether they still have dissertation value, implementation value, or delivery
value.

The purpose is to avoid delivering a repository that still contains:

- temporary prototypes;
- debug-only helpers;
- experimental assets;
- misleading scaffolds;
- non-essential clutter.

---

## Important Rule

Do not delete items blindly.

Before final removal, each item should be classified as one of:

- keep for final product;
- keep for dissertation evidence;
- archive outside the final delivery snapshot;
- remove as temporary development artifact.

---

## Category A: Temporary Development Utilities To Review

These are likely candidates for removal or disabling before final delivery.

### 1. DEV-only access paths

Examples:

- `DEV` login shortcuts;
- developer bypass buttons;
- temporary local account inspector/editor menus;
- debug-only test-account helpers.

Why review:

- useful during prototyping;
- inappropriate in a final delivered build unless explicitly justified as admin
  tools.

Likely final action:

- remove from production-facing build;
- or isolate behind a development-only flag.

### 2. Temporary state reset / debug controls

Examples:

- reset local auth data helpers;
- local test-profile editors;
- temporary delete/seed shortcuts used only for manual testing.

Why review:

- these are operationally useful during development;
- they may confuse evaluation or weaken the final product impression.

Likely final action:

- remove;
- or move to a dedicated internal developer mode not present in the delivery
  snapshot.

### 3. Mock assistant behavior

Examples:

- placeholder `Ray` responses;
- fake "thinking" flows not yet connected to actual model execution;
- conceptual preview replies.

Why review:

- acceptable in prototyping;
- may be misleading in final evaluation if presented as if fully functional.

Likely final action:

- replace with real integration;
- or clearly label as conceptual preview if kept for dissertation demo.

---

## Category B: Prototype Artifacts To Audit Carefully

These items may still be useful, but they should be reviewed before final
delivery.

### 4. Obsolete or superseded frontend prototypes

Examples:

- `archive/apps/prismalab-prototype` if its role becomes fully superseded by
  `archive/apps/prismalab-prototype-frontend`;
- duplicate visual experiments that are no longer part of the chosen direction.

Why review:

- early prototypes can be useful for dissertation evidence;
- but may clutter the final repository if left without explanation.

Likely final action:

- keep only if explicitly referenced in dissertation methodology or evolution;
- otherwise archive or remove from delivery snapshot.

### 5. Desktop shell scaffolds that are not yet operational

Examples:

- partial `Tauri` scaffolding in `archive/apps/prismalab-prototype-desktop`;
- temporary icon/config scaffolds;
- placeholder desktop integration files.

Why review:

- useful as evidence of architectural direction;
- risky if presented as a finished desktop app when still scaffold-level.

Likely final action:

- keep with clear documentation if it supports dissertation direction;
- otherwise exclude from final delivery package if not meant to be run.

### 6. Branding experiments and duplicate assets

Examples:

- alternate logos;
- test favicons;
- temporary banner variants;
- duplicate `Ray` or `PrismaLab` assets copied during experimentation.

Why review:

- many of these are harmless but create noise;
- some were only used to compare visibility or proportions.

Likely final action:

- keep only the approved asset set;
- remove redundant variants that are no longer referenced.

---

## Category C: Documentation Cleanup

Documentation should also be cleaned before final submission.

### 7. Notes that are too rough or redundant

Review whether any note files contain:

- repeated points already documented elsewhere;
- outdated architectural assumptions;
- temporary statements contradicted by later implementation;
- informal wording unsuitable for dissertation support.

Likely final action:

- consolidate;
- archive rough notes;
- keep a cleaner final set of dissertation-support documents.

### 8. Temporary TODO-style documentation

Examples:

- ad hoc scratch notes;
- incomplete planning fragments;
- one-off reminder files not useful for final interpretation.

Likely final action:

- integrate useful content into formal notes;
- remove the scratch artifact itself.

---

## Category D: Code and Configuration Review

### 9. Hardcoded temporary values

Examples:

- dev usernames;
- placeholder emails;
- temporary local account defaults;
- mock assistant labels or fallback text intended only for testing.

Likely final action:

- replace with configurable or production-appropriate behavior;
- remove if not justified.

### 10. Browser-only persistence used as temporary architecture

Examples:

- auth state in local storage;
- assistant history in local storage;
- settings stored only in prototype browser state.

Why review:

- acceptable for frontend validation;
- not necessarily aligned with final local database architecture.

Likely final action:

- either migrate to final persistence layer;
- or document clearly as prototype-only if final delivery is still a prototype.

### 11. Placeholder routing or duplicated pages

Examples:

- pages temporarily reusing other page structures;
- duplicated route behavior created to unblock design iteration;
- transitional route names kept only for compatibility.

Likely final action:

- reduce to final route structure;
- remove transitional duplication if no longer needed.

---

## Category E: Assets and Files That Are Commonly Non-Essential

The following types of files should always be reviewed before final delivery:

- unused screenshots;
- duplicate exported icons;
- temporary PNG/SVG comparisons;
- abandoned favicon variants;
- stale generated artifacts;
- unreferenced HTML lockup previews;
- build leftovers;
- local cache outputs;
- temporary exports from design experiments.

These should not be removed automatically, but they should all be audited.

---

## Current PrismaLab-Specific Review Targets

Based on the present repository state, the following areas should definitely be
reviewed before finalization.

### Review target 1: `archive/apps/prismalab-prototype`

Question:

- Is this still needed as a retained early prototype for dissertation evidence,
  or has it been fully superseded by `archive/apps/prismalab-prototype-frontend`?

### Review target 2: DEV access and DEV menus in `archive/apps/prismalab-prototype-frontend`

Question:

- Should the final delivered build still expose these controls?

Expected answer:

- probably no, unless a clear evaluator/admin justification exists.

### Review target 3: placeholder Ray responses

Question:

- Is `Ray` actually connected to a model/provider by final submission?

If not:

- either document it explicitly as conceptual prototype behavior;
- or reduce its prominence in the delivered app.

### Review target 4: desktop shell readiness

Question:

- Is `archive/apps/prismalab-prototype-desktop` mature enough to be part of the final runnable
  delivery?

If not:

- keep as architectural evidence only if clearly documented.

### Review target 5: branding asset sprawl

Question:

- Are all current `Ray` and `PrismaLab` assets actively used?

If not:

- remove unreferenced variants to reduce confusion.

---

## Final Pre-Submission Questions

Before final delivery, explicitly answer these questions:

1. Which app is the official final frontend entry point?
2. Which persistence layer is the authoritative one in the delivered version?
3. Which experimental features are still prototype-only?
4. Which developer conveniences are still exposed and should be removed?
5. Which prototype folders are still necessary for dissertation evidence?
6. Which assets are approved final assets and which are leftovers?
7. Is the delivered repository understandable to an evaluator who did not watch
   the project evolve?

---

## Final Rule

The final repository should look intentional.

It does not need to erase the history of experimentation, but it should avoid
making the final delivered work look accidental, cluttered, or ambiguous.

The cleanup process should therefore preserve:

- evidence that supports the dissertation;
- code and files needed to run the chosen final prototype/product;
- documentation that explains the final architecture.

It should remove or isolate:

- temporary development shortcuts;
- duplicated experiments with no retained value;
- debug-facing controls;
- misleading placeholders presented as final behavior.

