
from __future__ import annotations

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

PREFERRED_WORKBOOK_PATH = EXCEL_INPUT_DIR / "wos_workbook_03.03.2026_v2.xlsx"


# =========================
# WORKBOOK
# =========================

OUTPUT_WORKBOOK_SUFFIX = "_pdf_downloaded.xlsx"
SHEET_NAME = "wos_full_text"


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
# FRONTIERS / PLAYWRIGHT
# =========================

ENABLE_FRONTIERS_RESOLVER = True
FRONTIERS_HEADLESS = False
FRONTIERS_NAVIGATION_TIMEOUT_MS = 30000
FRONTIERS_DOWNLOAD_TIMEOUT_MS = 40000
FRONTIERS_POST_LOAD_WAIT_MS = 1000
FRONTIERS_ALLOWED_DOMAIN_PATTERN = r"(^|\.)frontiersin\.org$"


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


def build_output_workbook_path(workbook_path: Path) -> Path:
    """
    Build the output workbook path based on the input workbook name.
    """
    return EXCEL_INPUT_DIR / f"{workbook_path.stem}{OUTPUT_WORKBOOK_SUFFIX}"