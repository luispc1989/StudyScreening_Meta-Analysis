# Phase 1 - PDF Basic Download

## Purpose

Phase 1 is the first PDF retrieval stage of the tool. Its role is to attempt direct PDF acquisition using DOI-based access, simple HTTP retrieval, and lightweight HTML inspection, before invoking any publisher-specific resolver.

This phase exists to answer a practical question:

> can the article PDF be retrieved directly, without resorting to a specialized publisher workflow?

If the answer is yes, the system should avoid unnecessary complexity. If not, the resulting metadata should feed Phase 2.

## Position in the workflow

Phase 1 starts from the workbook already prepared by the previous stage. In the intended workflow:

1. Phase 0 enriches missing DOI data where possible;
2. Phase 1 attempts direct PDF download;
3. Phase 2 applies specialized publisher resolvers only where necessary.

This makes Phase 1 a bridge between metadata preparation and specialized retrieval.

## Main objective

The goal of Phase 1 is to maximize straightforward PDF acquisition while keeping the logic:

- fast;
- deterministic;
- explainable;
- reusable across many publishers.

Phase 1 is deliberately generic. It does not try to solve publisher-specific edge cases in depth. Instead, it attempts a robust baseline strategy and records enough information to support specialized handling later.

## Core strategy

For each record, Phase 1 follows this sequence:

1. check whether the PDF already exists locally;
2. build a list of candidate URLs from DOI metadata;
3. request those URLs with a regular HTTP session;
4. determine whether the response is already a PDF;
5. if not, inspect the returned HTML for direct PDF references;
6. if a PDF link is found, request that PDF;
7. classify the outcome and write the result into the workbook.

This logic is intentionally simpler than the specialized resolvers. It avoids browser automation whenever possible.

## Local duplicate detection

Before attempting any network retrieval, the phase checks whether the target PDF file already exists in the expected output location.

If the file exists and is non-empty, the record is immediately classified as:

- `duplicate_pdf`

This behavior is important because:

- it prevents unnecessary repeated downloads;
- it speeds up reruns;
- it preserves idempotency in iterative workflows.

## Candidate URL construction

Phase 1 builds its retrieval candidates from the bibliographic fields already present in the workbook:

- DOI link, when available;
- DOI normalized into a canonical `https://doi.org/<doi>` form.

The candidate list is deduplicated before requests are attempted.

## Response handling

The retrieval logic first checks whether the initial response already looks like a PDF. This can happen when the DOI resolves directly to a PDF endpoint or to an access-controlled PDF URL that is nevertheless readable in the current environment.

If the response is HTML instead of PDF, the phase searches for explicit PDF references using a small set of generic patterns, including:

- `citation_pdf_url` metadata;
- `href` links ending in `.pdf`;
- `src` links ending in `.pdf`.

If a candidate PDF URL is found, a second request is performed.

## Why HTML inspection was included

This was added because many publisher landing pages do not serve the PDF immediately, but do expose a machine-readable PDF link in the page source. Extracting these references allows Phase 1 to solve a meaningful number of cases without invoking a heavier browser-based workflow.

## Status classification

Phase 1 does not simply return success or failure. It classifies each outcome into operationally meaningful states.

### Available / successful states

- `downloaded`
- `duplicate_pdf`

These are considered available states and count toward immediate PDF availability.

### Common failure states

- `invalid_doi`
- `not_found`
- `broken_link`
- `paywalled`
- `metadata_only`
- `manual_check`

Each of these carries a different interpretation:

- `invalid_doi`: no usable DOI-based URL could be built;
- `not_found`: the target resource could not be found;
- `broken_link`: server-side or network-level failure;
- `paywalled`: access is restricted by the publisher;
- `metadata_only`: the page looks like article metadata but no PDF could be reached;
- `manual_check`: the page could be accessed but the generic logic was insufficient to retrieve the full text automatically.

## Why these statuses matter

The main design choice in Phase 1 was to preserve semantic information about failure. This matters for Phase 2 and for the diagnostic reports.

A simple “failed” flag would not be enough because it would hide important distinctions:

- some records fail because the DOI is invalid;
- some fail because access is restricted;
- some fail because the HTML requires a specialized resolver;
- some fail because the PDF already exists locally.

By storing explicit statuses, the workflow remains auditable and can support targeted follow-up actions.

## Data written to the workbook

Phase 1 writes operational retrieval metadata into the workbook, including:

- `pdf_downloaded`
- `pdf_download_status`
- `pdf_file_name`
- `pdf_source_url`
- `pdf_local_path`
- `pdf_http_status`
- `pdf_checked_at`

These fields are important because they form the state passed forward to the next phase.

## Relationship with Phase 2

Phase 1 is not intended to solve every publisher case. Instead, it provides:

- a first-pass retrieval attempt;
- local duplicate detection;
- a persistent status for each record;
- source URL evidence that can help identify publisher-specific cases later.

Phase 2 then uses this information to decide which records should be handled by specialized resolvers such as:

- MDPI
- Frontiers
- Springer
- Elsevier

This separation keeps the architecture modular.

## Why a generic first pass was preferred

The decision to create a strong generic retrieval phase before the specialized phase was motivated by several practical considerations:

1. many PDFs can be obtained without browser automation;
2. generic retrieval is faster and simpler to audit;
3. specialized resolvers should only be used when the baseline strategy is insufficient;
4. this reduces unnecessary complexity in the overall workflow.

In other words, Phase 1 acts as a cost-efficient filtering layer.

## Output behavior

When Phase 1 succeeds:

- the PDF is saved into the project PDF directory;
- the workbook is updated accordingly.

When it fails:

- the failure is classified;
- the workbook stores the relevant source URL and status;
- the record remains available for later analysis or specialized handling.

## What was done in the current implementation

The implemented Phase 1 includes:

- DOI-based candidate URL generation;
- duplicate detection before network requests;
- PDF content detection by content type and file signature;
- generic HTML parsing for PDF links;
- structured failure classification;
- workbook persistence of retrieval metadata;
- terminal monitoring of progress and outcomes.

## Why it was done this way

The phase was deliberately designed to be:

- predictable;
- publisher-agnostic in the first pass;
- safe to rerun;
- compatible with later specialized expansion.

This design is useful for dissertation work because it supports a clear methodological narrative:

- start from bibliographic identifiers;
- attempt a generic, reproducible retrieval strategy;
- escalate only the unresolved cases.

## Limitations

Phase 1 has known limitations:

- it cannot handle all publisher-specific JavaScript flows;
- it cannot bypass access restrictions;
- some pages expose metadata but not a directly retrievable PDF link;
- some cases require browser automation or manual review.

These limitations are intentional boundaries rather than implementation mistakes. They justify the existence of Phase 2.

## Dissertation framing suggestion

For the dissertation, Phase 1 can be described as:

> a generic DOI-driven PDF retrieval stage that attempts direct full-text acquisition using lightweight HTTP and HTML inspection, while recording structured outcomes that support reproducibility, diagnostics, and later specialized resolution.

This framing connects the implementation directly to the methodological rationale of the pipeline.
