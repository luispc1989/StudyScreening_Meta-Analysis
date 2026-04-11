# PrismaLab Desktop

This folder contains the desktop shell for `PrismaLab`.

## Purpose

The desktop app is a thin `Tauri` wrapper around the shared frontend in:

- `apps/prismalab-frontend`

This keeps a single UI codebase while allowing PrismaLab to evolve into a true
local-first desktop application with:

- local filesystem access
- local database integration
- desktop session behavior
- future Python tool orchestration

## Current architecture

- `apps/prismalab-frontend`: shared React/TanStack frontend
- `apps/prismalab-desktop`: Tauri shell
- `tools/prismalab`: Python-side PrismaLab foundation

## Dev workflow

1. Run the frontend in dev mode:

```powershell
cd apps\prismalab-frontend
npm run dev
```

2. In another terminal, run the desktop shell:

```powershell
cd apps\prismalab-desktop
npm install
npm run dev
```

The desktop shell is configured to load the frontend from:

- `http://localhost:8080`

## Build workflow

When the frontend is ready to package:

```powershell
cd apps\prismalab-frontend
npm run build

cd ..\prismalab-desktop
npm install
npm run build
```

The desktop shell points to the built frontend output in:

- `../prismalab-frontend/dist`

## Notes

- The desktop shell is intentionally thin for now.
- The long-term goal is to keep the UI shared and move desktop-specific logic
  into the Tauri/native layer only where needed.
- Session policies tied to true PC boot / wake cycles should be implemented in
  the desktop runtime layer, not in the browser-only prototype.
