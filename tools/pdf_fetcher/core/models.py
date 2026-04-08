# app/models.py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


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
    resolver_names: list[str]


@dataclass
class Phase0Summary:
    total_rows_read: int = 0
    total_existing_doi: int = 0
    total_missing_doi: int = 0
    total_eligible: int = 0
    original_baseline_available: bool = True
    original_total_rows_read: int = 0
    original_total_existing_doi: int = 0
    original_total_missing_doi: int = 0
    original_total_eligible: int = 0
    total_skipped_missing_title: int = 0
    total_skipped_already_downloaded: int = 0
    total_enriched: int = 0
    total_needs_review: int = 0
    total_unresolved: int = 0
    total_errors: int = 0
    report_path: Optional[Path] = None


@dataclass
class Phase1Summary:
    total_records_considered: int = 0
    total_available_before: int = 0
    total_downloaded_now: int = 0
    total_failed: int = 0
    total_skipped: int = 0


@dataclass
class Phase2Summary:
    total_retry_candidates: int = 0
    total_recovered_now: int = 0
    total_failed: int = 0
    total_skipped: int = 0


@dataclass
class DiagnosticSummary:
    diagnostic_label: str = ""
    total_rows_considered: int = 0
    total_rows_diagnosed: int = 0
    total_downloaded: int = 0
    total_errors: int = 0
    report_path: Optional[Path] = None


@dataclass
class SessionState:
    workbook_path: Path
    sheet_name: str
    project_root: Optional[Path] = None
    tool_root: Optional[Path] = None

    workbook: Optional[Any] = None
    worksheet: Optional[Any] = None
    col_map: dict[str, int] = field(default_factory=dict)

    records: list[Record] = field(default_factory=list)
    retry_tasks: list[RetryTask] = field(default_factory=list)

    current_phase: str = "initial"
    timestamp: str = ""

    phase0_summary: Phase0Summary = field(default_factory=Phase0Summary)
    phase1_summary: Phase1Summary = field(default_factory=Phase1Summary)
    phase2_summary: Phase2Summary = field(default_factory=Phase2Summary)

    diagnostics_history: list[DiagnosticSummary] = field(default_factory=list)
    generated_report_paths: list[Path] = field(default_factory=list)

    final_workbook_path: Optional[Path] = None
    temp_workbook_path: Optional[Path] = None
    current_workbook_path: Optional[Path] = None
    history_workbook_path: Optional[Path] = None

    def add_generated_report(self, report_path: Optional[Path]) -> None:
        if report_path is None:
            return
        self.generated_report_paths.append(report_path)

    def add_diagnostic_summary(self, summary: DiagnosticSummary) -> None:
        self.diagnostics_history.append(summary)
        if summary.report_path is not None:
            self.generated_report_paths.append(summary.report_path)

    @property
    def is_workbook_loaded(self) -> bool:
        return self.workbook is not None and self.worksheet is not None

    @property
    def has_retry_tasks(self) -> bool:
        return len(self.retry_tasks) > 0

    @property
    def has_records(self) -> bool:
        return len(self.records) > 0
