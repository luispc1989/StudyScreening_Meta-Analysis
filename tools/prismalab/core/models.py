from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass(slots=True)
class ImportSource:
    """
    Describes the bibliographic system that originated an import.

    The canonical model must accept incomplete rows because bibliographic
    exports vary widely across sources and years.
    """

    slug: str
    display_name: str
    source_type: str = "bibliographic_database"
    description: Optional[str] = None


@dataclass(slots=True)
class ImportBatch:
    """
    Represents one imported file or dataset batch.
    """

    project_name: str
    source_slug: str
    file_name: str
    file_hash: Optional[str] = None
    imported_at: datetime = field(default_factory=datetime.utcnow)
    row_count: Optional[int] = None
    notes: Optional[str] = None


@dataclass(slots=True)
class SourceRecordPayload:
    """
    Stores the original row-level information before canonical merge.

    `raw_data` should preserve the incoming column names whenever possible so
    we can audit mappings later.
    """

    source_slug: str
    source_record_id: Optional[str] = None
    row_index: Optional[int] = None
    raw_data: dict[str, Any] = field(default_factory=dict)
    mapped_data: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CanonicalArticleRecord:
    """
    Minimum internal article model for PrismaLab.

    Every field is optional except `source_slug` because imports from multiple
    bibliographic databases will frequently contain missing values.
    """

    source_slug: str
    source_record_id: Optional[str] = None
    title: Optional[str] = None
    doi: Optional[str] = None
    doi_url: Optional[str] = None
    authors_text: Optional[str] = None
    first_author: Optional[str] = None
    corresponding_author: Optional[str] = None
    corresponding_email: Optional[str] = None
    publication_year: Optional[int] = None
    journal: Optional[str] = None
    abstract: Optional[str] = None
    keywords_text: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    language: Optional[str] = None
    document_type: Optional[str] = None
    source_url: Optional[str] = None
    pdf_url: Optional[str] = None
    issn: Optional[str] = None
    eissn: Optional[str] = None
    isbn: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    wos_id: Optional[str] = None
    scopus_id: Optional[str] = None
    openalex_id: Optional[str] = None
    merge_key_hint: Optional[str] = None
    notes: Optional[str] = None
