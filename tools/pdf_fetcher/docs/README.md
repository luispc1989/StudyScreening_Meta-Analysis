# PDF Fetcher

Local Python tool for PDF retrieval in a meta-analysis and study-screening workflow. The system is phase-based, uses Excel workbooks as input and operational persistence, and includes a manual review layer through `S.C.O.U.T.`.

## What it does

The PDF Fetcher:

- reads an input Excel workbook;
- enriches missing DOI data in `Phase 0`;
- attempts generic PDF download in `Phase 1`;
- attempts specialized publisher-based download in `Phase 2`;
- prepares unresolved cases for manual review in `S.C.O.U.T.`;
- stores workflow state in explicit per-phase workbooks.

The tool is also now being treated as one module inside a larger future `Study Screening Toolkit`, rather than as a permanently standalone app.

## Current workflow

Recommended order:

1. `Input workbook`
2. `Phase 0 - DOI Enrichment`
3. `Phase 1 - PDF Basic Download`
4. `Phase 2 - PDF Specialized Download`
5. `S.C.O.U.T. - Semi-assisted Case Opening and User Triage`

The current Phase 2 logic now treats `Sci-Hub` as a final fallback layer after specialized resolvers, rather than embedding it directly inside each resolver path.

## Current file structure

Within the active project, the main folders are:

- `PDF Fetcher/Excel/Input`
- `PDF Fetcher/Excel/Current`
- `PDF Fetcher/Excel/Final`
- `PDF Fetcher/PDFs`
- `PDF Fetcher/Reports/Phase 0`
- `PDF Fetcher/Reports/Phase 1`
- `PDF Fetcher/Reports/Phase 2`
- `PDF Fetcher/Reports/SCOUT`
- `PDF Fetcher/Checkpoints/Phase 0`
- `PDF Fetcher/Checkpoints/Phase 1`
- `PDF Fetcher/Checkpoints/Phase 2`
- `PDF Fetcher/Checkpoints/SCOUT`

Current phase workbooks:

- `wos_workbook_current_phase_0.xlsx`
- `wos_workbook_current_phase_1.xlsx`
- `wos_workbook_current_phase_2.xlsx`

## Quick start

From the repository root:

```bat
py -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m playwright install chromium
```

Run the terminal app:

```bat
.venv\Scripts\python.exe -m tools.pdf_fetcher.ui.terminal.main
```

Run the SCOUT directly in Streamlit:

```bat
.venv\Scripts\python.exe -m streamlit run tools\pdf_fetcher\scout\app.py
```

## Session start

At startup, the terminal can show:

- `Start new run from Input workbook`
- `Continue previous run from saved phase workbooks`

The `continue` option only appears when at least one saved phase workbook already exists.

## Phase handoff logic

- `Phase 0` reads the input workbook and writes `wos_workbook_current_phase_0.xlsx`
- `Phase 1` reads `wos_workbook_current_phase_0.xlsx` and writes `wos_workbook_current_phase_1.xlsx`
- `Phase 2` reads `wos_workbook_current_phase_1.xlsx` and writes `wos_workbook_current_phase_2.xlsx`
- `S.C.O.U.T.` reads `wos_workbook_current_phase_2.xlsx`

## Main modes

### Terminal

The terminal is the main execution interface for the staged pipeline. It supports:

- sequential phase execution;
- resuming from saved phase workbooks;
- live metrics and status updates;
- interruption with checkpoint saving;
- report generation.

### S.C.O.U.T.

The SCOUT is the manual triage layer used after the automated pipeline. It allows the user to:

- open DOI links;
- use search;
- send author-request emails;
- insert or clear DOI/source links;
- assign manual decisions;
- preserve review memory until final synchronization.

Recent SCOUT refinements include:

- review-status badges per case;
- faster auto-save after PDF detection;
- safer widget-state handling;
- `Erase PDF` support to undo a wrongly saved PDF and return the case to `Pending Review`.

## Documentation in this folder

- [PDF_FETCHER_APP_NOTES.md](/c:/Users/Luís%20Pinto%20Coelho/Desktop/Dissertação/StudyScreening_Meta-Analysis/tools/pdf_fetcher/docs/PDF_FETCHER_APP_NOTES.md) - architectural and methodological notes
- [KNOWN_ISSUES_AND_LESSONS.md](/c:/Users/Luís%20Pinto%20Coelho/Desktop/Dissertação/StudyScreening_Meta-Analysis/tools/pdf_fetcher/docs/KNOWN_ISSUES_AND_LESSONS.md) - bugs, issues, and lessons learned
- [PHASE0_DOI_ENRICHMENT_NOTES.md](/c:/Users/Luís%20Pinto%20Coelho/Desktop/Dissertação/StudyScreening_Meta-Analysis/tools/pdf_fetcher/docs/PHASE0_DOI_ENRICHMENT_NOTES.md) - Phase 0 notes
- [PHASE1_BASIC_DOWNLOAD_NOTES.md](/c:/Users/Luís%20Pinto%20Coelho/Desktop/Dissertação/StudyScreening_Meta-Analysis/tools/pdf_fetcher/docs/PHASE1_BASIC_DOWNLOAD_NOTES.md) - Phase 1 notes
- [PHASE2_SPECIALIZED_DOWNLOAD_NOTES.md](/c:/Users/Luís%20Pinto%20Coelho/Desktop/Dissertação/StudyScreening_Meta-Analysis/tools/pdf_fetcher/docs/PHASE2_SPECIALIZED_DOWNLOAD_NOTES.md) - Phase 2 notes
- [USER_GUIDE.md](/c:/Users/Luís%20Pinto%20Coelho/Desktop/Dissertação/StudyScreening_Meta-Analysis/tools/pdf_fetcher/docs/USER_GUIDE.md) - user manual
- [DEVELOPER_GUIDE.md](/c:/Users/Luís%20Pinto%20Coelho/Desktop/Dissertação/StudyScreening_Meta-Analysis/tools/pdf_fetcher/docs/DEVELOPER_GUIDE.md) - technical developer guide
- [TROUBLESHOOTING.md](/c:/Users/Luís%20Pinto%20Coelho/Desktop/Dissertação/StudyScreening_Meta-Analysis/tools/pdf_fetcher/docs/TROUBLESHOOTING.md) - troubleshooting

## Dissertation and cross-project notes

General dissertation-support and cross-application notes now live in:

- [docs/dissertation](/c:/Users/Lu�s%20Pinto%20Coelho/Desktop/Disserta��o/StudyScreening_Meta-Analysis/docs/dissertation)

## Forward-looking note

The current system still uses Excel as the main persistence bridge between phases. That is appropriate for the present local workflow, but the project already points toward a future model with:

- a local project database;
- Excel as import/export layer;
- `PrismaLab`, a broader application coordinating multiple tools in the meta-analysis workflow.

An early visual prototype for that direction already exists in:

- `archive/apps/prismalab-prototype`

An initial database foundation for that direction now exists in:

- `tools/prismalab/core`
- `tools/prismalab/docs/DATABASE_ARCHITECTURE.md`

The current architectural expectation is:

- `React / Next.js` for the future app master frontend;
- Python retained for workflow logic and tool backends;
- a local project database as the long-term internal source of truth.


