# app/models.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Record:
    row_idx: int
    record_id: str
    title: str
    doi_raw: str
    doi_link_raw: str
    file_name: str
    pdf_path: Path
    relative_path: str


@dataclass
class DownloadResult:
    pdf_downloaded: int
    pdf_download_status: str
    pdf_file_name: str
    pdf_source_url: str
    pdf_local_path: str
    pdf_http_status: Optional[int]
    pdf_checked_at: str


@dataclass
class RetryTask:
    record: Record
    resolver_name: str