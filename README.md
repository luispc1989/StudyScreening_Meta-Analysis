# PrismaLab

Monorepo for the evolving `PrismaLab` research workspace and its related tools.

This repository now contains:

- active application code for the PrismaLab frontend and desktop shell;
- Python research tools such as `PDF Fetcher`;
- dissertation and cross-project documentation;
- supporting data, scripts, tests, and experimental archives.

## Current structure

```text
apps/
  prismalab-frontend/        active frontend application
  prismalab-desktop/         desktop shell scaffold

tools/
  pdf_fetcher/               staged PDF retrieval and SCOUT workflow
  prismalab/                 early database and backend-oriented PrismaLab foundations

docs/
  dissertation/              dissertation-wide and cross-project notes
  prismalab-brand/           PrismaLab and Ray brand/reference material

shared/
  README.md                  reserved for future shared code between apps/tools

archive/
  apps/prismalab-prototype/  archived earlier Next.js PrismaLab prototype

configs/
data/
models/
notebooks/
scripts/
tests/
```

## Repository logic

The repository should be understood as a workspace monorepo rather than as a
single app.

Use these rules:

- `apps/` for active application shells and user-facing interfaces;
- `tools/` for Python tools and backend-oriented workflow modules;
- `docs/` for cross-project documentation and dissertation material;
- `shared/` only for code that is genuinely reused across apps or tools;
- `archive/` for non-active prototypes or historical material.

## Current PrismaLab direction

The current product direction is:

- `apps/prismalab-frontend` as the active PrismaLab UI codebase;
- `apps/prismalab-desktop` as the desktop wrapper direction;
- `tools/prismalab` as the early local database/back-end foundation;
- `tools/pdf_fetcher` as one major workflow module inside the broader ecosystem.

An older visual prototype was retained for reference in:

- `archive/apps/prismalab-prototype`

## Documentation

Cross-project and dissertation documentation:

- `docs/dissertation/README.md`

PDF Fetcher-specific documentation:

- `tools/pdf_fetcher/docs/README.md`

## Important note on repository rename

The repository is being conceptually renamed from
`StudyScreening_Meta-Analysis` to `PrismaLab`.

Internal organization has been updated accordingly, but the outer folder and
GitHub repository name should be renamed explicitly as a separate step once the
working session can be safely closed or moved.
