# PrismaLab Database Architecture

## Purpose

This document defines the first database foundation for `PrismaLab`.

The goal is not to replace the current workbook workflow overnight. The goal is
to introduce a minimal local-first project database that can gradually become
the internal source of truth while Excel remains available for import and
export.

## Architectural direction

The intended flow is:

1. import bibliographic files from one or more databases;
2. preserve each imported row as source-level evidence;
3. map heterogeneous columns into a canonical article model;
4. detect duplicates and unresolved conflicts;
5. maintain a project-level local SQLite database;
6. let tools such as `PDF Fetcher` read and write project state progressively;
7. keep Excel available as an interoperability layer rather than the live
   operational memory.

This keeps the project:

- local-first;
- lightweight;
- resumable years later;
- auditable across multiple bibliographic sources.

## Why the database should not mirror one Excel format

The current `wos_workbook` is operationally useful, but it is a source-shaped
artifact. The future system needs to accept records from:

- Web of Science;
- Scopus;
- PubMed;
- other bibliographic exports;
- future manual or semi-structured imports.

For that reason, the database must not be modeled as a direct copy of one
source workbook. It must instead store:

- project state;
- import provenance;
- raw imported rows;
- canonical article records;
- duplicate-analysis links;
- future workflow statuses.

## Minimum canonical article model

The current minimum article model includes:

- `title`
- `doi`
- `doi_url`
- `authors_text`
- `first_author`
- `corresponding_author`
- `corresponding_email`
- `publication_year`
- `journal`
- `abstract`
- `keywords_text`
- `volume`
- `issue`
- `pages`
- `language`
- `document_type`
- `source_url`
- `pdf_url`
- common identifiers where available (`pmid`, `pmcid`, `wos_id`, `scopus_id`, `openalex_id`, `issn`, `eissn`, `isbn`)

Every field is allowed to be missing. This is essential because bibliographic
exports vary considerably in completeness.

The canonical model now explicitly includes `corresponding_email` because the
research workflow can require later contact with authors and because some
sources or later enrichment steps may provide usable contact data.

## Database tables in the first foundation

### `projects`

One row per project. Stores the identity and path of the local project.

### `import_batches`

One row per imported file or batch. Stores:

- project link;
- source name;
- imported filename;
- file hash;
- row count;
- import timestamp.

### `source_records`

Stores each imported row before canonical merge. This preserves:

- raw input payload;
- mapped payload;
- row index;
- source-specific record id;
- ingest and duplicate-analysis state.

### `articles`

Stores the project-level canonical article record. This is the main internal
entity that later tools should use.

### `article_identifiers`

Stores identifiers as a separate table to support multiple identifiers per
article and easier lookup during deduplication.

### `article_sources`

Links canonical articles back to source rows so provenance is never lost.

### `article_contacts`

Stores article-related contacts such as corresponding author email. This allows
future workflows such as manual outreach without forcing every contact field
into the core article table only.

### `article_status`

Stores phase-oriented workflow status. This is where future tools can mark:

- screening progress;
- PDF retrieval progress;
- appraisal progress;
- extraction progress;
- synthesis progress.

### `article_notes`

Stores notes that should survive across sessions and future project reopening.

## Import pipeline concept

The first database-backed ingestion should follow these layers:

1. `raw import`
   Read the file exactly as provided.
2. `column mapping`
   Map source-specific column names to the canonical field names.
3. `normalization`
   Clean DOI, title, year, author text, and URLs into a more comparable form.
4. `duplicate analysis`
   Detect exact and probable duplicates.
5. `canonical merge`
   Create or update the project-level article entity.

This layered design is safer than writing source rows directly into the final
article table.

## Initial duplicate strategy

The first duplicate strategy should be simple and explainable:

1. exact DOI match after normalization;
2. exact external identifier match when available;
3. probable duplicate match using title similarity + publication year +
   first-author compatibility.

Potential duplicates should remain reviewable rather than being merged blindly.

## Relationship with the current PDF Fetcher

The `PDF Fetcher` should not be rewritten immediately.

Instead, the migration path is:

1. create the database file per project;
2. import workbook-derived records into the database;
3. expose project/database state inside `PrismaLab`;
4. progressively let `PDF Fetcher` consume and update database state;
5. keep workbook import/export during the transition.

This preserves existing value while improving the foundation.
