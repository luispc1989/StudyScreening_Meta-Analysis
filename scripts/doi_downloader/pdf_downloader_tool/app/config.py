from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional


# =========================
# PATHS
# =========================

EXTERNAL_WOS_DIR = Path(
    r"C:\Users\Luís Pinto Coelho\Desktop\Dissertação\metanalysis development\2 - literature search & study screening\data\wos"
)

EXCEL_INPUT_DIR = EXTERNAL_WOS_DIR / "excel_files"
PDF_BASE_DIR = EXTERNAL_WOS_DIR / "pdf_files"

APP_OUTPUTS_DIR = Path(
    r"C:\Users\Luís Pinto Coelho\Desktop\Dissertação\metanalysis development\2 - literature search & study screening\data\wos\excel_files\app_outputs"
)
REPORTS_OUTPUT_DIR = APP_OUTPUTS_DIR / "reports"
FINAL_OUTPUT_DIR = APP_OUTPUTS_DIR / "final"
TEMP_OUTPUT_DIR = APP_OUTPUTS_DIR / "temp"

PREFERRED_WORKBOOK_PATH = EXCEL_INPUT_DIR / "wos_workbook_03.03.2026_v2.xlsx"


# =========================
# WORKBOOK
# =========================

OUTPUT_WORKBOOK_SUFFIX = "_pdf_downloaded.xlsx"  # Temporary compatibility with current pipeline
SHEET_NAME = "wos_full_text"


# =========================
# PHASE 0 - DOI ENRICHMENT
# =========================

ENABLE_DOI_ENRICHMENT = True
DOI_MAX_ROWS_TO_PROCESS: Optional[int] = None

DOI_MIN_TITLE_SIMILARITY = 0.88
DOI_MIN_CONFIDENCE_SCORE = 75.0
DOI_OVERWRITE_EXISTING = False

DOI_CONNECT_TIMEOUT = 10
DOI_READ_TIMEOUT = 25
DOI_REQUEST_TIMEOUT = (DOI_CONNECT_TIMEOUT, DOI_READ_TIMEOUT)
DOI_SLEEP_BETWEEN_REQUESTS = 0.20

DOI_CROSSREF_MAILTO = ""
DOI_GENERATE_REPORT_BY_DEFAULT = False

DOI_REQUIRED_INPUT_COLUMNS = [
    "record_id",
    "Authors",
    "Publication Year",
    "Title",
    "DOI",
    "DOI Link",
]

DOI_REPORT_MAIN_SHEET_NAME = SHEET_NAME
DOI_REPORT_STATS_SHEET_NAME = "doi_stats"
DOI_REPORT_ALL_PROCESSED_SHEET_NAME = "doi_all_processed"
DOI_REPORT_ENRICHED_SHEET_NAME = "doi_enriched"
DOI_REPORT_UNRESOLVED_SHEET_NAME = "doi_unresolved"


# =========================
# PHASE 1 - BASE DOWNLOAD
# =========================

MAX_WORKERS = 4
CONNECT_TIMEOUT = 8
READ_TIMEOUT = 15
SLEEP_BETWEEN_REQUESTS = 0.05
MAX_ROWS_TO_PROCESS: Optional[int] = None


# =========================
# BENCHMARK MODE
# =========================

ENABLE_BENCHMARK_MODE = False
BENCHMARK_RECORD_IDS: set[str] = set()


# =========================
# SAVE CADENCE
# =========================

SAVE_EVERY_N_ROWS = 100
SPECIALIZED_SAVE_EVERY_N_ROWS = 10


# =========================
# DASHBOARD REFRESH
# =========================

REFRESH_DASHBOARD_EVERY_N_COMPLETIONS = 10
FORCE_SIMPLE_TERMINAL = False


# =========================
# PHASE 2 - SPECIALIZED RETRY
# =========================

ENABLE_SPECIALIZED_RESOLVERS = True


# =========================
# SPECIALIZED RESOLVERS
# =========================

ENABLE_FRONTIERS_RESOLVER = True
ENABLE_MDPI_RESOLVER = True
ENABLE_SPRINGER_RESOLVER = True


# =========================
# FRONTIERS / PLAYWRIGHT
# =========================

FRONTIERS_HEADLESS = False
FRONTIERS_NAVIGATION_TIMEOUT_MS = 30000
FRONTIERS_DOWNLOAD_TIMEOUT_MS = 40000
FRONTIERS_POST_LOAD_WAIT_MS = 1000
FRONTIERS_ALLOWED_DOMAIN_PATTERN = r"(^|\.)frontiersin\.org$"


# =========================
# MDPI / PLAYWRIGHT
# =========================

MDPI_HEADLESS = False
MDPI_NAVIGATION_TIMEOUT_MS = 30000
MDPI_DOWNLOAD_TIMEOUT_MS = 40000
MDPI_POST_LOAD_WAIT_MS = 1000
MDPI_ALLOWED_DOMAIN_PATTERN = r"(^|\.)mdpi\.com$"


# =========================
# SPRINGER / PLAYWRIGHT
# =========================

SPRINGER_HEADLESS = False
SPRINGER_NAVIGATION_TIMEOUT_MS = 30000
SPRINGER_DOWNLOAD_TIMEOUT_MS = 40000
SPRINGER_POST_LOAD_WAIT_MS = 1000
SPRINGER_ALLOWED_DOMAIN_PATTERN = r"(^|\.)springer\.com$|(^|\.)link\.springer\.com$"


# =========================
# DIAGNOSTICS
# =========================

ENABLE_DIAGNOSTICS = True

DIAGNOSTIC_CONNECT_TIMEOUT = 5
DIAGNOSTIC_READ_TIMEOUT = 10
DIAGNOSTIC_REQUEST_TIMEOUT = (DIAGNOSTIC_CONNECT_TIMEOUT, DIAGNOSTIC_READ_TIMEOUT)

DIAGNOSTIC_MAX_WORKERS = 12
DIAGNOSTIC_MAX_ROWS_TO_PROCESS: Optional[int] = None

DIAGNOSTIC_PROGRESS_REFRESH_EVERY_N = 20
DIAGNOSTIC_PROGRESS_REFRESH_EVERY_SECONDS = 1.5

DIAGNOSTIC_OUTPUT_SHEET_NAME = SHEET_NAME
DIAGNOSTIC_STATS_SHEET_NAME = "pdf_error_stats"

DIAGNOSTIC_REQUIRED_INPUT_COLUMNS_INITIAL = [
    "record_id",
    "source",
    "Authors",
    "Publication Year",
    "Title",
    "Abstract",
    "Author Keywords",
    "Source Title",
    "Volume",
    "Issue",
    "Begin Page",
    "End Page",
    "E-mail Address",
    "DOI",
    "DOI Link",
]

DIAGNOSTIC_REQUIRED_INPUT_COLUMNS_SESSION = [
    "record_id",
    "Authors",
    "Title",
    "DOI",
    "DOI Link",
    "pdf_download_status",
]

DIAGNOSTIC_OUTPUT_COLUMNS = [
    "record_id",
    "Authors",
    "Title",
    "DOI",
    "DOI Link",
    "pdf_download_status",
    "pdf_source_url",
    "pdf_http_status",
]

DIAGNOSTIC_ERROR_TAB_COLUMNS = [
    "record_id",
    "Authors",
    "Title",
    "DOI",
    "DOI Link",
    "pdf_download_status",
    "pdf_source_url",
    "pdf_http_status",
]

DIAGNOSTIC_EXCLUDED_FROM_ERROR_RANKING = {"downloaded", "", None}


# =========================
# OUTPUT FILE NAMING
# =========================

REPORT_NAME_DIAGNOSTICO_INICIAL = "diagnostico_inicial"
REPORT_NAME_FASE0_DOI = "fase0_doi"
REPORT_NAME_DIAGNOSTICO_FASE0 = "diagnostico_fase0"
REPORT_NAME_DIAGNOSTICO_FASE1 = "diagnostico_fase1"
REPORT_NAME_DIAGNOSTICO_FASE2 = "diagnostico_fase2"

FINAL_WORKBOOK_NAME = "workbook_final"


# =========================
# HTTP HEADERS
# =========================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "application/pdf,*/*;q=0.8"
    ),
}


# =========================
# REQUIRED COLUMNS
# =========================

REQUIRED_INPUT_COLUMNS = [
    "record_id",
    "Title",
    "DOI",
    "DOI Link",
]

REQUIRED_OUTPUT_COLUMNS = [
    "pdf_downloaded",
    "pdf_download_status",
    "pdf_file_name",
    "pdf_source_url",
    "pdf_local_path",
    "pdf_http_status",
    "pdf_checked_at",
]

REQUIRED_COLUMNS = REQUIRED_INPUT_COLUMNS + REQUIRED_OUTPUT_COLUMNS


# =========================
# STATUS SETS
# =========================

BASE_AVAILABLE_STATUSES = {"downloaded", "duplicate_pdf"}
BASE_DOWNLOADED_NOW_STATUSES = {"downloaded"}

SPECIALIZED_DOWNLOADED_NOW_STATUSES = {
    "downloaded_frontiers",
    "downloaded_mdpi",
    "downloaded_springer",
}


# =========================
# TERMINAL / DASHBOARD
# =========================

FRAME_WIDTH = 78


# =========================
# HELPER FUNCTIONS
# =========================

def resolve_workbook_path() -> Path:
    """
    Return the preferred workbook if it exists.
    Otherwise, return the most recently modified .xlsx file
    found inside EXCEL_INPUT_DIR.
    """
    if PREFERRED_WORKBOOK_PATH.exists():
        return PREFERRED_WORKBOOK_PATH

    candidates = sorted(
        [p for p in EXCEL_INPUT_DIR.glob("*.xlsx") if not p.name.startswith("~$")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not candidates:
        raise FileNotFoundError(f"No .xlsx workbook found in: {EXCEL_INPUT_DIR}")

    return candidates[0]


def ensure_output_directories() -> None:
    """
    Create output directories if they do not already exist.
    """
    REPORTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_timestamp() -> str:
    """
    Return a filesystem-safe timestamp.
    """
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def build_output_workbook_path(workbook_path: Path) -> Path:
    """
    Build the legacy output workbook path based on the input workbook name.

    This helper is kept temporarily for compatibility with the current pipeline.
    """
    return EXCEL_INPUT_DIR / f"{workbook_path.stem}{OUTPUT_WORKBOOK_SUFFIX}"


def build_final_workbook_path(timestamp: Optional[str] = None) -> Path:
    """
    Build the final workbook output path inside the final output directory.
    """
    ensure_output_directories()
    ts = timestamp or build_timestamp()
    return FINAL_OUTPUT_DIR / f"{FINAL_WORKBOOK_NAME}_{ts}.xlsx"


def build_report_output_path(report_prefix: str, timestamp: Optional[str] = None) -> Path:
    """
    Build a report output path inside the reports output directory.
    """
    ensure_output_directories()
    ts = timestamp or build_timestamp()
    return REPORTS_OUTPUT_DIR / f"{report_prefix}_{ts}.xlsx"


def build_temp_workbook_path(label: str, timestamp: Optional[str] = None) -> Path:
    """
    Build a temporary checkpoint workbook path inside the temp output directory.
    """
    ensure_output_directories()
    ts = timestamp or build_timestamp()
    safe_label = str(label).strip().replace(" ", "_")
    return TEMP_OUTPUT_DIR / f"{safe_label}_{ts}.xlsx"