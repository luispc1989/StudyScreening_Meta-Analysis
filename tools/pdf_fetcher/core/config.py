from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional


# =========================
# TOOLKIT / PROJECT PATHS
# =========================

TOOLKIT_NAME = "Study Screening Toolkit"
PROJECTS_DIR_NAME = "Projects"
DEFAULT_PROJECT_NAME = os.environ.get("SSTK_PROJECT_NAME", "My Project")

TOOL_DISPLAY_NAME = "PDF Fetcher"
TOOL_SLUG = "pdf_fetcher"

USER_DOCUMENTS_DIR = Path.home() / "Documents"
TOOLKIT_ROOT_DIR = Path(os.environ.get("SSTK_ROOT", str(USER_DOCUMENTS_DIR / TOOLKIT_NAME)))
PROJECTS_ROOT_DIR = TOOLKIT_ROOT_DIR / PROJECTS_DIR_NAME
ACTIVE_PROJECT_ROOT = PROJECTS_ROOT_DIR / DEFAULT_PROJECT_NAME

EXCEL_ROOT_DIR = ACTIVE_PROJECT_ROOT / "Excel"
INPUT_EXCEL_DIR = EXCEL_ROOT_DIR / "Input"
CURRENT_EXCEL_DIR = EXCEL_ROOT_DIR / "Current"
HISTORY_EXCEL_DIR = EXCEL_ROOT_DIR / "History"
FINAL_EXCEL_DIR = EXCEL_ROOT_DIR / "Final"

TOOL_ROOT_DIR = ACTIVE_PROJECT_ROOT / TOOL_DISPLAY_NAME
PDF_BASE_DIR = TOOL_ROOT_DIR / "PDFs"
REPORTS_OUTPUT_DIR = TOOL_ROOT_DIR / "Reports"
TEMP_OUTPUT_DIR = TOOL_ROOT_DIR / "Checkpoints"
FINAL_OUTPUT_DIR = FINAL_EXCEL_DIR

DEFAULT_INPUT_WORKBOOK_NAME = "wos_workbook_input.xlsx"
DEFAULT_CURRENT_WORKBOOK_NAME = "wos_workbook_current.xlsx"
PREFERRED_WORKBOOK_PATH = CURRENT_EXCEL_DIR / DEFAULT_CURRENT_WORKBOOK_NAME


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
DOI_AUTO_APPLY_MIN_TITLE_SIMILARITY = 0.93
DOI_AUTO_APPLY_MIN_CONFIDENCE_SCORE = 82.0
DOI_AUTO_APPLY_MIN_TOP2_GAP = 8.0
DOI_AUTO_APPLY_MIN_SOURCE_COUNT = 2
DOI_AUTO_APPLY_MIN_AUTHOR_SCORE = 25.0
DOI_AUTO_APPLY_MIN_YEAR_SCORE = 70.0
DOI_NEEDS_REVIEW_MIN_TITLE_SIMILARITY = 0.88
DOI_NEEDS_REVIEW_MIN_CONFIDENCE_SCORE = 70.0
DOI_MAX_QUERY_VARIANTS = 3
DOI_ENABLE_SOURCE_CASCADE = True
DOI_PRIMARY_SOURCE_ORDER = ("Crossref", "OpenAlex")
DOI_SECONDARY_SOURCE_ORDER = ("DataCite", "Europe PMC")
DOI_EARLY_STOP_MIN_TITLE_SIMILARITY = 0.97
DOI_EARLY_STOP_MIN_CONFIDENCE_SCORE = 88.0
DOI_EARLY_STOP_MIN_SOURCE_COUNT = 2
DOI_ACCEPT_FIRST_VARIANT_IF_PLAUSIBLE = True

DOI_CONNECT_TIMEOUT = 4
DOI_READ_TIMEOUT = 8
DOI_REQUEST_TIMEOUT = (DOI_CONNECT_TIMEOUT, DOI_READ_TIMEOUT)
DOI_SLEEP_BETWEEN_REQUESTS = 0.05

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
DOI_REPORT_NEEDS_REVIEW_SHEET_NAME = "doi_needs_review"
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
ENABLE_ELSEVIER_RESOLVER = True


# =========================
# FRONTIERS / PLAYWRIGHT
# =========================

FRONTIERS_BROWSER_MODE = "headed"
FRONTIERS_HEADLESS = False
FRONTIERS_NAVIGATION_TIMEOUT_MS = 120000
FRONTIERS_NETWORKIDLE_TIMEOUT_MS = 8000
FRONTIERS_DOWNLOAD_TIMEOUT_MS = 120000
FRONTIERS_POST_LOAD_WAIT_MS = 3000
FRONTIERS_ALLOWED_DOMAIN_PATTERN = r"(^|\.)frontiersin\.org$"


# =========================
# MDPI / PLAYWRIGHT
# =========================

MDPI_BROWSER_MODE = "headed"
MDPI_HEADLESS = False
MDPI_NAVIGATION_TIMEOUT_MS = 30000
MDPI_NETWORKIDLE_TIMEOUT_MS = 8000
MDPI_DOWNLOAD_TIMEOUT_MS = 40000
MDPI_POST_LOAD_WAIT_MS = 1000
MDPI_ALLOWED_DOMAIN_PATTERN = r"(^|\.)mdpi\.com$"


# =========================
# SPRINGER / PLAYWRIGHT
# =========================

SPRINGER_BROWSER_MODE = "headed"
SPRINGER_HEADLESS = False
SPRINGER_NAVIGATION_TIMEOUT_MS = 120000
SPRINGER_NETWORKIDLE_TIMEOUT_MS = 8000
SPRINGER_DOWNLOAD_TIMEOUT_MS = 120000
SPRINGER_POST_LOAD_WAIT_MS = 2000
SPRINGER_ALLOWED_DOMAIN_PATTERN = r"(^|\.)springer\.com$|(^|\.)link\.springer\.com$"


# =========================
# ELSEVIER / PLAYWRIGHT
# =========================

ELSEVIER_BROWSER_MODE = "headed"
ELSEVIER_HEADLESS = False
ELSEVIER_NAVIGATION_TIMEOUT_MS = 120000
ELSEVIER_NETWORKIDLE_TIMEOUT_MS = 30000
ELSEVIER_DOWNLOAD_TIMEOUT_MS = 120000
ELSEVIER_POST_LOAD_WAIT_MS = 2000
ELSEVIER_ALLOWED_DOMAIN_PATTERN = r"(^|\.)sciencedirect\.com$|(^|\.)elsevier\.com$|(^|\.)linkinghub\.elsevier\.com$"


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

FINAL_WORKBOOK_NAME = "wos_workbook_final"
CURRENT_WORKBOOK_NAME = DEFAULT_CURRENT_WORKBOOK_NAME


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
    "downloaded_elsevier",
}


# =========================
# TERMINAL / DASHBOARD
# =========================

FRAME_WIDTH = 78


# =========================
# HELPER FUNCTIONS
# =========================

def ensure_project_directories() -> None:
    directories = [
        TOOLKIT_ROOT_DIR,
        PROJECTS_ROOT_DIR,
        ACTIVE_PROJECT_ROOT,
        EXCEL_ROOT_DIR,
        INPUT_EXCEL_DIR,
        CURRENT_EXCEL_DIR,
        HISTORY_EXCEL_DIR,
        FINAL_EXCEL_DIR,
        TOOL_ROOT_DIR,
        PDF_BASE_DIR,
        REPORTS_OUTPUT_DIR,
        TEMP_OUTPUT_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def build_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def _sorted_xlsx_candidates(directory: Path) -> list[Path]:
    if not directory.exists():
        return []

    return sorted(
        [path for path in directory.glob("*.xlsx") if not path.name.startswith("~$")],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def resolve_workbook_path() -> Path:
    ensure_project_directories()

    input_candidates = _sorted_xlsx_candidates(INPUT_EXCEL_DIR)
    if input_candidates:
        return input_candidates[0]

    if PREFERRED_WORKBOOK_PATH.exists():
        return PREFERRED_WORKBOOK_PATH

    for directory in (CURRENT_EXCEL_DIR, INPUT_EXCEL_DIR):
        candidates = _sorted_xlsx_candidates(directory)
        if candidates:
            return candidates[0]

    raise FileNotFoundError(
        "No .xlsx workbook found in the active project. "
        f"Checked: {CURRENT_EXCEL_DIR} and {INPUT_EXCEL_DIR}"
    )


def ensure_output_directories() -> None:
    ensure_project_directories()


def build_output_workbook_path(workbook_path: Path) -> Path:
    return CURRENT_EXCEL_DIR / f"{workbook_path.stem}{OUTPUT_WORKBOOK_SUFFIX}"


def build_current_workbook_path() -> Path:
    ensure_project_directories()
    return CURRENT_EXCEL_DIR / CURRENT_WORKBOOK_NAME


def build_input_workbook_path(file_name: str = DEFAULT_INPUT_WORKBOOK_NAME) -> Path:
    ensure_project_directories()
    safe_name = Path(str(file_name or DEFAULT_INPUT_WORKBOOK_NAME)).name
    if not safe_name.lower().endswith(".xlsx"):
        safe_name = f"{safe_name}.xlsx"
    return INPUT_EXCEL_DIR / safe_name


def _next_history_step_index() -> int:
    ensure_project_directories()

    pattern = re.compile(r"^(\d{2})_")
    max_index = 0

    for path in HISTORY_EXCEL_DIR.glob("*.xlsx"):
        match = pattern.match(path.name)
        if not match:
            continue
        try:
            max_index = max(max_index, int(match.group(1)))
        except ValueError:
            continue

    return max_index + 1


def build_history_workbook_path(
    tool_name: str = TOOL_SLUG,
    timestamp: Optional[str] = None,
    suffix: str = "output",
) -> Path:
    ensure_project_directories()
    ts = timestamp or build_timestamp()
    step_idx = _next_history_step_index()
    safe_tool_name = str(tool_name).strip().lower().replace(" ", "_")
    safe_suffix = str(suffix).strip().lower().replace(" ", "_")
    return HISTORY_EXCEL_DIR / f"{step_idx:02d}_{safe_tool_name}_{ts}_{safe_suffix}.xlsx"


def build_final_workbook_path(timestamp: Optional[str] = None) -> Path:
    ensure_project_directories()
    ts = timestamp or build_timestamp()
    return FINAL_OUTPUT_DIR / f"{FINAL_WORKBOOK_NAME}_{ts}.xlsx"


def build_report_output_path(report_prefix: str, timestamp: Optional[str] = None) -> Path:
    ensure_project_directories()
    ts = timestamp or build_timestamp()
    return REPORTS_OUTPUT_DIR / f"{report_prefix}_{ts}.xlsx"


def build_temp_workbook_path(label: str, timestamp: Optional[str] = None) -> Path:
    ensure_project_directories()
    ts = timestamp or build_timestamp()
    safe_label = str(label).strip().replace(" ", "_")
    return TEMP_OUTPUT_DIR / f"{safe_label}_{ts}.xlsx"
