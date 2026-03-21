from __future__ import annotations

import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from openpyxl import load_workbook

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright

    PLAYWRIGHT_AVAILABLE = True
except Exception:
    PLAYWRIGHT_AVAILABLE = False


# =========================
# CONFIGURATION
# =========================

EXTERNAL_WOS_DIR = Path(
    r"C:\Users\Luís Pinto Coelho\Desktop\Dissertação\metanalysis development\2 - literature search & study screening\data\wos"
)

EXCEL_INPUT_DIR = EXTERNAL_WOS_DIR / "excel_files"
PDF_BASE_DIR = EXTERNAL_WOS_DIR / "pdf_files"

PREFERRED_WORKBOOK_PATH = EXCEL_INPUT_DIR / "wos_workbook_03.03.2026_v2.xlsx"

if PREFERRED_WORKBOOK_PATH.exists():
    WORKBOOK_PATH = PREFERRED_WORKBOOK_PATH
else:
    candidates = sorted(
        [p for p in EXCEL_INPUT_DIR.glob("*.xlsx") if not p.name.startswith("~$")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not candidates:
        raise FileNotFoundError(f"No .xlsx workbook found in: {EXCEL_INPUT_DIR}")

    WORKBOOK_PATH = candidates[0]

OUTPUT_WORKBOOK_PATH = EXCEL_INPUT_DIR / f"{WORKBOOK_PATH.stem}_pdf_attempted_updated.xlsx"

FULL_TEXT_SHEET_NAME = "wos_full_text"
SCREENING_VIEW_SHEET_NAME = "wos_screening_view_full_text"

REQUEST_TIMEOUT = 25
SLEEP_BETWEEN_REQUESTS = 1.0
SAVE_EVERY_N_ROWS = 25

# For test runs, use a small number like 10 or 20.
# For full processing, set to None.
MAX_ROWS_TO_PROCESS: Optional[int] = None

# Open-access APIs
USE_UNPAYWALL = True
UNPAYWALL_EMAIL = "luispintocoelho1989@gmail.com"  # replace if needed

USE_CROSSREF = True

# Browser fallback
USE_PLAYWRIGHT_FALLBACK = True
PLAYWRIGHT_HEADLESS = False
PLAYWRIGHT_TIMEOUT_MS = 20000

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
# HELPER FUNCTIONS
# =========================

def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def is_blank(value) -> bool:
    return value is None or str(value).strip() == ""


def sanitize_filename(text: str, max_len: int = 140) -> str:
    text = str(text or "").strip()
    text = re.sub(r'[\\/:*?"<>|]', " ", text)
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" ", "_")
    text = re.sub(r"_+", "_", text).strip("_")

    if not text:
        text = "untitled"

    return text[:max_len].rstrip("_")


def build_pdf_filename(record_id: str, title: str) -> str:
    safe_title = sanitize_filename(title)
    return f"{record_id}__{safe_title}.pdf"


def normalize_doi(doi: str) -> Optional[str]:
    if is_blank(doi):
        return None

    doi = str(doi).strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    doi = doi.strip()

    if re.match(r"^10\.\d{4,9}/\S+$", doi):
        return doi

    return None


def make_doi_url(doi: str) -> str:
    return f"https://doi.org/{doi}"


def response_looks_like_pdf(resp: requests.Response) -> bool:
    content_type = (resp.headers.get("Content-Type") or "").lower()
    if "application/pdf" in content_type:
        return True

    try:
        return resp.content[:5] == b"%PDF-"
    except Exception:
        return False


def save_pdf_bytes(pdf_path: Path, content: bytes) -> bool:
    if not content:
        return False

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(content)

    return pdf_path.exists() and pdf_path.stat().st_size > 0


def extract_pdf_url_from_html(base_url: str, html: str) -> Optional[str]:
    if not html:
        return None

    patterns = [
        r'<meta[^>]+name=["\']citation_pdf_url["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']citation_pdf_url["\']',
        r'href=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']',
        r'src=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']',
    ]

    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if match:
            return urljoin(base_url, match.group(1))

    return None


def find_domain(url: str) -> str:
    try:
        return (urlparse(url).netloc or "").lower()
    except Exception:
        return ""


def html_contains_any(text: str, markers: List[str]) -> bool:
    text = (text or "").lower()
    return any(marker in text for marker in markers)


def classify_html_failure(status_code: Optional[int], html: str) -> str:
    text = (html or "").lower()

    captcha_markers = [
        "are you a robot",
        "security check",
        "captcha",
        "verify you are human",
        "unusual traffic",
        "cloudflare",
        "checking your browser",
        "attention required",
    ]
    if any(marker in text for marker in captcha_markers):
        return "captcha_or_security_check"

    purchase_markers = [
        "purchase",
        "buy article",
        "add to cart",
        "cart",
        "vat excluded",
        "eur ",
        "usd ",
        "rent this article",
        "price:",
        "price ",
        "buy now",
    ]
    if any(marker in text for marker in purchase_markers):
        return "paywalled_purchase_required"

    institutional_markers = [
        "access through your institution",
        "institutional access",
        "subscribe to journal",
        "get access",
        "login via institution",
        "sign in via institution",
        "check access",
        "access options",
        "sign in to view",
        "subscription required",
    ]
    if any(marker in text for marker in institutional_markers):
        return "paywalled_institutional_access"

    login_markers = [
        "sign in",
        "log in",
        "login required",
        "please log in",
        "please sign in",
        "authenticated access",
    ]
    if any(marker in text for marker in login_markers):
        return "login_required"

    metadata_markers = [
        "abstract",
        "references",
        "metrics",
        "article info",
        "article information",
        "keywords",
        "supplementary data",
    ]
    if any(marker in text for marker in metadata_markers):
        return "metadata_only"

    if status_code == 401:
        return "login_required"

    if status_code == 403:
        return "paywalled_institutional_access"

    if status_code == 404:
        return "not_found"

    if status_code is not None and status_code >= 500:
        return "broken_link"

    return "manual_check"


def set_cell(ws, row_idx: int, col_map: Dict[str, int], header: str, value) -> None:
    if header in col_map:
        ws.cell(row=row_idx, column=col_map[header], value=value)


def get_cell(ws, row_idx: int, col_map: Dict[str, int], header: str):
    if header not in col_map:
        return None
    return ws.cell(row=row_idx, column=col_map[header]).value


def clear_pdf_result_fields(ws, row_idx: int, col_map: Dict[str, int], file_name: str) -> None:
    set_cell(ws, row_idx, col_map, "pdf_downloaded", "")
    set_cell(ws, row_idx, col_map, "pdf_download_status", "")
    set_cell(ws, row_idx, col_map, "pdf_file_name", file_name)
    set_cell(ws, row_idx, col_map, "pdf_local_path", "")
    set_cell(ws, row_idx, col_map, "pdf_source_url", "")
    set_cell(ws, row_idx, col_map, "pdf_http_status", "")
    set_cell(ws, row_idx, col_map, "pdf_checked_at", "")


def validate_required_columns(col_map: Dict[str, int], sheet_name: str) -> None:
    required_columns = [
        "record_id",
        "Title",
        "DOI",
        "DOI Link",
        "pdf_downloaded",
        "pdf_download_status",
        "pdf_file_name",
        "pdf_local_path",
        "pdf_source_url",
        "pdf_http_status",
        "pdf_checked_at",
    ]
    missing = [c for c in required_columns if c not in col_map]
    if missing:
        raise ValueError(f"Missing required columns in '{sheet_name}': {missing}")


def build_col_map(ws) -> Dict[str, int]:
    col_map: Dict[str, int] = {}
    for col_idx in range(1, ws.max_column + 1):
        header = ws.cell(row=1, column=col_idx).value
        if header is not None and str(header).strip():
            col_map[str(header).strip()] = col_idx
    return col_map


def build_record_row_map(ws, col_map: Dict[str, int]) -> Dict[str, int]:
    record_map: Dict[str, int] = {}
    if "record_id" not in col_map:
        return record_map

    for row_idx in range(2, ws.max_row + 1):
        record_id = str(get_cell(ws, row_idx, col_map, "record_id") or "").strip()
        if record_id:
            record_map[record_id] = row_idx
    return record_map


def sync_result_to_screening_view(
    record_id: str,
    full_ws,
    full_col_map: Dict[str, int],
    screen_ws,
    screen_col_map: Dict[str, int],
    screen_record_map: Dict[str, int],
) -> None:
    target_row = screen_record_map.get(record_id)
    if not target_row:
        return

    fields_to_sync = [
        "pdf_downloaded",
        "pdf_download_status",
        "pdf_file_name",
        "pdf_local_path",
        "pdf_source_url",
        "pdf_http_status",
        "pdf_checked_at",
    ]

    for field in fields_to_sync:
        value = get_cell(full_ws, full_col_map_row_idx := None, full_col_map, field)  # dummy to satisfy linter


def sync_row_fields(
    source_ws,
    source_row: int,
    source_col_map: Dict[str, int],
    target_ws,
    target_row: int,
    target_col_map: Dict[str, int],
    fields: List[str],
) -> None:
    for field in fields:
        if field in source_col_map and field in target_col_map:
            value = source_ws.cell(row=source_row, column=source_col_map[field]).value
            target_ws.cell(row=target_row, column=target_col_map[field], value=value)


# =========================
# API LOOKUPS
# =========================

def try_unpaywall_pdf_url(doi: str, session: requests.Session) -> Optional[str]:
    if not USE_UNPAYWALL or not doi or not UNPAYWALL_EMAIL:
        return None

    api_url = f"https://api.unpaywall.org/v2/{doi}"
    params = {"email": UNPAYWALL_EMAIL}

    try:
        resp = session.get(api_url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if resp.status_code >= 400:
            return None

        data = resp.json()

        best_oa = data.get("best_oa_location") or {}
        pdf_url = best_oa.get("url_for_pdf")
        if pdf_url:
            return pdf_url

        oa_locations = data.get("oa_locations") or []
        for loc in oa_locations:
            pdf_url = (loc or {}).get("url_for_pdf")
            if pdf_url:
                return pdf_url

        return None

    except Exception:
        return None


def try_crossref_pdf_urls(doi: str, session: requests.Session) -> List[str]:
    if not USE_CROSSREF or not doi:
        return []

    urls: List[str] = []
    api_url = f"https://api.crossref.org/works/{doi}"

    try:
        resp = session.get(api_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if resp.status_code >= 400:
            return urls

        data = resp.json()
        message = data.get("message") or {}

        links = message.get("link") or []
        for item in links:
            content_type = str((item or {}).get("content-type") or "").lower()
            url = str((item or {}).get("URL") or "").strip()
            if not url:
                continue
            if "pdf" in content_type or url.lower().endswith(".pdf"):
                urls.append(url)

        return deduplicate_urls(urls)

    except Exception:
        return []


def deduplicate_urls(urls: List[str]) -> List[str]:
    seen = set()
    result = []
    for url in urls:
        cleaned = str(url or "").strip()
        if not cleaned:
            continue
        if cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


# =========================
# NETWORK DOWNLOAD
# =========================

def try_download_from_url(
    url: str,
    session: requests.Session,
) -> Tuple[bool, str, Optional[int], Optional[bytes], str]:
    """
    Returns:
        (success, status_label, http_status, pdf_bytes, final_url_used)
    """
    try:
        resp = session.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        http_status = resp.status_code
        final_url = resp.url

        if http_status >= 400:
            if http_status == 401:
                return False, "login_required", http_status, None, final_url
            if http_status == 403:
                return False, "paywalled_institutional_access", http_status, None, final_url
            if http_status == 404:
                return False, "not_found", http_status, None, final_url
            return False, "broken_link", http_status, None, final_url

        if response_looks_like_pdf(resp):
            return True, "downloaded", http_status, resp.content, final_url

        html = resp.text or ""

        early_status = classify_html_failure(http_status, html)
        if early_status in {
            "captcha_or_security_check",
            "paywalled_purchase_required",
            "paywalled_institutional_access",
            "login_required",
        }:
            return False, early_status, http_status, None, final_url

        pdf_url = extract_pdf_url_from_html(final_url, html)
        if pdf_url:
            pdf_resp = session.get(
                pdf_url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
            )
            pdf_http_status = pdf_resp.status_code
            pdf_final_url = pdf_resp.url

            if pdf_http_status >= 400:
                if pdf_http_status == 401:
                    return False, "login_required", pdf_http_status, None, pdf_final_url
                if pdf_http_status == 403:
                    return False, "paywalled_institutional_access", pdf_http_status, None, pdf_final_url
                if pdf_http_status == 404:
                    return False, "not_found", pdf_http_status, None, pdf_final_url
                return False, "broken_link", pdf_http_status, None, pdf_final_url

            if response_looks_like_pdf(pdf_resp):
                return True, "downloaded", pdf_http_status, pdf_resp.content, pdf_final_url

            return False, classify_html_failure(pdf_http_status, pdf_resp.text or ""), pdf_http_status, None, pdf_final_url

        return False, classify_html_failure(http_status, html), http_status, None, final_url

    except requests.Timeout:
        return False, "broken_link", None, None, url
    except requests.RequestException:
        return False, "broken_link", None, None, url


# =========================
# PLAYWRIGHT FALLBACK
# =========================

def domain_needs_playwright(url: str) -> bool:
    domain = find_domain(url)
    return any(
        d in domain
        for d in [
            "mdpi.com",
            "scielo.br",
            "scielo.org",
        ]
    )


def try_playwright_download(
    start_url: str,
    pdf_path: Path,
) -> Tuple[bool, str, Optional[int], str]:
    if not USE_PLAYWRIGHT_FALLBACK:
        return False, "manual_check", None, start_url

    if not PLAYWRIGHT_AVAILABLE:
        return False, "manual_check", None, start_url

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=PLAYWRIGHT_HEADLESS)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()
            page.set_default_timeout(PLAYWRIGHT_TIMEOUT_MS)

            page.goto(start_url, wait_until="domcontentloaded")
            final_url = page.url

            page_text = ""
            try:
                page_text = page.content()
            except Exception:
                page_text = ""

            early_status = classify_html_failure(200, page_text)
            if early_status in {
                "captcha_or_security_check",
                "paywalled_purchase_required",
                "paywalled_institutional_access",
                "login_required",
            }:
                browser.close()
                return False, early_status, 200, final_url

            domain = find_domain(final_url)

            if "mdpi.com" in domain:
                result = playwright_mdpi_flow(page, pdf_path)
                browser.close()
                return result

            if "scielo.br" in domain or "scielo.org" in domain:
                result = playwright_scielo_flow(page, pdf_path)
                browser.close()
                return result

            browser.close()
            return False, "manual_check", 200, final_url

    except PlaywrightTimeoutError:
        return False, "manual_check", None, start_url
    except Exception:
        return False, "manual_check", None, start_url


def playwright_mdpi_flow(page, pdf_path: Path) -> Tuple[bool, str, Optional[int], str]:
    final_url = page.url

    try:
        selectors = [
            "text=Download PDF",
            "a[aria-label*='Download PDF']",
            "a[href*='.pdf']",
            "text=Download",
        ]

        for selector in selectors:
            try:
                with page.expect_download(timeout=PLAYWRIGHT_TIMEOUT_MS) as download_info:
                    page.locator(selector).first.click()
                download = download_info.value
                download.save_as(str(pdf_path))
                if pdf_path.exists() and pdf_path.stat().st_size > 0:
                    return True, "downloaded_playwright", 200, page.url
            except Exception:
                continue

        html = page.content()
        status = classify_html_failure(200, html)
        return False, status, 200, final_url

    except Exception:
        return False, "manual_check", 200, final_url


def playwright_scielo_flow(page, pdf_path: Path) -> Tuple[bool, str, Optional[int], str]:
    final_url = page.url

    try:
        selectors = [
            "text=PDF",
            "a[href*='/pdf/']",
            "a[href$='.pdf']",
            "a[title*='PDF']",
        ]

        for selector in selectors:
            try:
                with page.expect_download(timeout=PLAYWRIGHT_TIMEOUT_MS) as download_info:
                    page.locator(selector).first.click()
                download = download_info.value
                download.save_as(str(pdf_path))
                if pdf_path.exists() and pdf_path.stat().st_size > 0:
                    return True, "downloaded_playwright", 200, page.url
            except Exception:
                continue

        html = page.content()
        status = classify_html_failure(200, html)
        return False, status, 200, final_url

    except Exception:
        return False, "manual_check", 200, final_url


# =========================
# RESULT WRITING
# =========================

def write_result(
    ws,
    row_idx: int,
    col_map: Dict[str, int],
    downloaded: int,
    status: str,
    file_name: str,
    local_path: str,
    source_url: str,
    http_status: Optional[int],
) -> None:
    set_cell(ws, row_idx, col_map, "pdf_downloaded", downloaded)
    set_cell(ws, row_idx, col_map, "pdf_download_status", status)
    set_cell(ws, row_idx, col_map, "pdf_file_name", file_name)
    set_cell(ws, row_idx, col_map, "pdf_local_path", local_path)
    set_cell(ws, row_idx, col_map, "pdf_source_url", source_url)
    set_cell(ws, row_idx, col_map, "pdf_http_status", http_status if http_status is not None else "")
    set_cell(ws, row_idx, col_map, "pdf_checked_at", now_str())


# =========================
# MAIN PROCESS
# =========================

def main() -> None:
    if not WORKBOOK_PATH.exists():
        raise FileNotFoundError(f"Workbook not found: {WORKBOOK_PATH}")

    PDF_BASE_DIR.mkdir(parents=True, exist_ok=True)

    wb = load_workbook(WORKBOOK_PATH)

    if FULL_TEXT_SHEET_NAME not in wb.sheetnames:
        raise ValueError(f"Sheet not found: {FULL_TEXT_SHEET_NAME}")

    if SCREENING_VIEW_SHEET_NAME not in wb.sheetnames:
        raise ValueError(f"Sheet not found: {SCREENING_VIEW_SHEET_NAME}")

    full_ws = wb[FULL_TEXT_SHEET_NAME]
    screen_ws = wb[SCREENING_VIEW_SHEET_NAME]

    full_col_map = build_col_map(full_ws)
    screen_col_map = build_col_map(screen_ws)

    validate_required_columns(full_col_map, FULL_TEXT_SHEET_NAME)
    validate_required_columns(screen_col_map, SCREENING_VIEW_SHEET_NAME)

    screen_record_map = build_record_row_map(screen_ws, screen_col_map)

    session = requests.Session()

    processed = 0
    attempted = 0
    success_count = 0

    print(f"Input workbook: {WORKBOOK_PATH}")
    print(f"Output workbook: {OUTPUT_WORKBOOK_PATH}")
    print(f"PDF folder: {PDF_BASE_DIR}")
    print(f"Sheet processed: {FULL_TEXT_SHEET_NAME}")
    print(f"Mirror sheet: {SCREENING_VIEW_SHEET_NAME}")
    print(f"MAX_ROWS_TO_PROCESS: {MAX_ROWS_TO_PROCESS}")
    print(f"Playwright available: {PLAYWRIGHT_AVAILABLE}")
    print(f"Use Playwright fallback: {USE_PLAYWRIGHT_FALLBACK}")

    for row_idx in range(2, full_ws.max_row + 1):
        if MAX_ROWS_TO_PROCESS is not None and attempted >= MAX_ROWS_TO_PROCESS:
            break

        record_id = str(get_cell(full_ws, row_idx, full_col_map, "record_id") or "").strip()
        title = str(get_cell(full_ws, row_idx, full_col_map, "Title") or "").strip()
        doi_raw = get_cell(full_ws, row_idx, full_col_map, "DOI")
        doi_link_raw = get_cell(full_ws, row_idx, full_col_map, "DOI Link")

        if not record_id:
            continue

        attempted += 1

        file_name = build_pdf_filename(record_id, title)
        relative_path = f"pdf_files/{file_name}"
        pdf_path = PDF_BASE_DIR / file_name

        if pdf_path.exists() and pdf_path.stat().st_size > 0:
            write_result(
                full_ws,
                row_idx,
                full_col_map,
                downloaded=1,
                status="duplicate_pdf",
                file_name=file_name,
                local_path=relative_path,
                source_url="",
                http_status=None,
            )

            target_row = screen_record_map.get(record_id)
            if target_row:
                sync_row_fields(
                    full_ws,
                    row_idx,
                    full_col_map,
                    screen_ws,
                    target_row,
                    screen_col_map,
                    [
                        "pdf_downloaded",
                        "pdf_download_status",
                        "pdf_file_name",
                        "pdf_local_path",
                        "pdf_source_url",
                        "pdf_http_status",
                        "pdf_checked_at",
                    ],
                )

            processed += 1
            success_count += 1
            print(f"[{attempted}] {record_id}: duplicate_pdf")
            continue

        clear_pdf_result_fields(full_ws, row_idx, full_col_map, file_name)

        doi = normalize_doi(str(doi_raw or ""))
        doi_link = str(doi_link_raw or "").strip()

        candidate_urls: List[str] = []

        # Priority 1: Unpaywall
        if doi:
            unpaywall_pdf_url = try_unpaywall_pdf_url(doi, session)
            if unpaywall_pdf_url:
                candidate_urls.append(unpaywall_pdf_url)

        # Priority 2: Crossref
        if doi:
            candidate_urls.extend(try_crossref_pdf_urls(doi, session))

        # Priority 3: DOI link from workbook
        if doi_link:
            candidate_urls.append(doi_link)

        # Priority 4: canonical DOI URL
        if doi:
            candidate_urls.append(make_doi_url(doi))

        candidate_urls = deduplicate_urls(candidate_urls)

        if not candidate_urls:
            write_result(
                full_ws,
                row_idx,
                full_col_map,
                downloaded=0,
                status="invalid_doi",
                file_name=file_name,
                local_path="",
                source_url="",
                http_status=None,
            )

            target_row = screen_record_map.get(record_id)
            if target_row:
                sync_row_fields(
                    full_ws,
                    row_idx,
                    full_col_map,
                    screen_ws,
                    target_row,
                    screen_col_map,
                    [
                        "pdf_downloaded",
                        "pdf_download_status",
                        "pdf_file_name",
                        "pdf_local_path",
                        "pdf_source_url",
                        "pdf_http_status",
                        "pdf_checked_at",
                    ],
                )

            processed += 1
            print(f"[{attempted}] {record_id}: invalid_doi")
            time.sleep(SLEEP_BETWEEN_REQUESTS)
            continue

        final_success = False
        final_status = "manual_check"
        final_http_status: Optional[int] = None
        final_source_url = ""

        for url in candidate_urls:
            success, status_label, http_status, pdf_bytes, final_url = try_download_from_url(url, session)

            final_status = status_label
            final_http_status = http_status
            final_source_url = final_url or url

            if success and pdf_bytes:
                saved = save_pdf_bytes(pdf_path, pdf_bytes)
                if saved:
                    status_to_write = "downloaded"

                    if url != doi_link and doi and url.startswith("https://api.unpaywall.org") is False:
                        pass

                    write_result(
                        full_ws,
                        row_idx,
                        full_col_map,
                        downloaded=1,
                        status=status_to_write,
                        file_name=file_name,
                        local_path=relative_path,
                        source_url=final_source_url,
                        http_status=http_status,
                    )

                    final_success = True
                    success_count += 1
                    print(f"[{attempted}] {record_id}: downloaded")
                    break
                else:
                    final_status = "manual_check"

            if (
                not final_success
                and USE_PLAYWRIGHT_FALLBACK
                and domain_needs_playwright(final_source_url or url)
                and final_status in {"metadata_only", "manual_check"}
            ):
                pw_success, pw_status, pw_http_status, pw_final_url = try_playwright_download(
                    final_source_url or url,
                    pdf_path,
                )

                final_status = pw_status
                final_http_status = pw_http_status
                final_source_url = pw_final_url

                if pw_success and pdf_path.exists() and pdf_path.stat().st_size > 0:
                    write_result(
                        full_ws,
                        row_idx,
                        full_col_map,
                        downloaded=1,
                        status=pw_status,
                        file_name=file_name,
                        local_path=relative_path,
                        source_url=final_source_url,
                        http_status=pw_http_status,
                    )

                    final_success = True
                    success_count += 1
                    print(f"[{attempted}] {record_id}: {pw_status}")
                    break

        if not final_success:
            write_result(
                full_ws,
                row_idx,
                full_col_map,
                downloaded=0,
                status=final_status,
                file_name=file_name,
                local_path="",
                source_url=final_source_url,
                http_status=final_http_status,
            )
            print(f"[{attempted}] {record_id}: {final_status}")

        target_row = screen_record_map.get(record_id)
        if target_row:
            sync_row_fields(
                full_ws,
                row_idx,
                full_col_map,
                screen_ws,
                target_row,
                screen_col_map,
                [
                    "pdf_downloaded",
                    "pdf_download_status",
                    "pdf_file_name",
                    "pdf_local_path",
                    "pdf_source_url",
                    "pdf_http_status",
                    "pdf_checked_at",
                ],
            )

        processed += 1

        if processed % SAVE_EVERY_N_ROWS == 0:
            wb.save(OUTPUT_WORKBOOK_PATH)
            print(f"Intermediate save after {processed} rows -> {OUTPUT_WORKBOOK_PATH}")

        time.sleep(SLEEP_BETWEEN_REQUESTS)

    wb.save(OUTPUT_WORKBOOK_PATH)

    print("\nDone.")
    print(f"Processed rows: {processed}")
    print(f"Attempted rows: {attempted}")
    print(f"Logical successes: {success_count}")
    print(f"Saved workbook: {OUTPUT_WORKBOOK_PATH}")
    print(f"PDF folder: {PDF_BASE_DIR}")


if __name__ == "__main__":
    main()