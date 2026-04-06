from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime
from pathlib import Path
from time import time
from typing import Any
from urllib.parse import urlparse

from openpyxl import Workbook, load_workbook
import streamlit as st
import streamlit.components.v1 as components


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


BRIDGE_HOST = "127.0.0.1"
BRIDGE_PORT = 8765
DOWNLOAD_BRIDGE_STATE: dict[str, Any] = {
    "server_started": False,
    "events": [],
    "active_cases": {},
    "lock": threading.Lock(),
}


DECISION_OPTIONS = [
    "pending_review",
    "downloaded_manual",
    "paywalled",
    "unavailable",
    "wrong_link",
    "article_not_found",
    "other",
]


def set_page() -> None:
    st.set_page_config(
        page_title="S.C.O.U.T. - Semi-assisted Case Opening and User Triage",
        page_icon="SC",
        layout="wide",
    )


def init_state() -> None:
    defaults = {
        "scout_cases": [],
        "scout_current_index": 0,
        "scout_report_path": "",
        "scout_review_path": "",
        "scout_decisions": {},
        "scout_loaded": False,
        "scout_browser_message": "",
        "scout_download_markers": {},
        "scout_report_source_expanded": True,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def normalize_header(value: Any) -> str:
    return str(value or "").strip().lower()


def normalize_url(value: str) -> str:
    return str(value or "").strip()


def extract_host(value: str) -> str:
    try:
        return (urlparse(value).netloc or "").lower()
    except Exception:
        return ""


def build_case_signals(case: dict) -> dict[str, Any]:
    urls = [normalize_url(case.get("doi_url", "")), normalize_url(case.get("source_url", ""))]
    doi = str(case.get("doi", "") or "").strip().lower()
    doi_token = doi.replace("/", "").replace(".", "").replace("-", "") if doi else ""
    return {
        "record_id": case["record_id"],
        "title": case["title"],
        "output_file": case["output_file"],
        "doi": doi,
        "doi_token": doi_token,
        "urls": [url for url in urls if url],
        "hosts": sorted({extract_host(url) for url in urls if url}),
        "opened_at": time(),
        "watch_until": time() + 900,
    }


def get_preferred_case_url(case: dict) -> tuple[str, str]:
    source_url = normalize_url(case.get("source_url", ""))
    doi_url = normalize_url(case.get("doi_url", ""))
    if source_url:
        return source_url, "source"
    if doi_url:
        return doi_url, "doi"
    return "", "none"


def find_windows_browser_executable() -> str | None:
    candidates = [
        Path(os.environ.get("PROGRAMFILES", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
    ]
    for candidate in candidates:
        if str(candidate) and candidate.exists():
            return str(candidate)
    return None


def start_download_bridge_server() -> None:
    if DOWNLOAD_BRIDGE_STATE["server_started"]:
        return

    class DownloadBridgeHandler(BaseHTTPRequestHandler):
        def _write_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self) -> None:
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
            self.end_headers()

        def do_POST(self) -> None:
            if self.path != "/download-event":
                self._write_json(404, {"ok": False, "error": "not_found"})
                return

            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except Exception as exc:
                self._write_json(400, {"ok": False, "error": f"invalid_json: {exc}"})
                return

            payload["received_at"] = time()
            payload["matched_record_id"] = None
            payload["status"] = "pending"

            with DOWNLOAD_BRIDGE_STATE["lock"]:
                DOWNLOAD_BRIDGE_STATE["events"].append(payload)

            self._write_json(200, {"ok": True})

        def do_GET(self) -> None:
            if self.path != "/health":
                self._write_json(404, {"ok": False, "error": "not_found"})
                return
            self._write_json(200, {"ok": True})

        def log_message(self, format: str, *args) -> None:
            return

    server = ThreadingHTTPServer((BRIDGE_HOST, BRIDGE_PORT), DownloadBridgeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    DOWNLOAD_BRIDGE_STATE["server_started"] = True


def register_active_case(case: dict) -> None:
    signals = build_case_signals(case)
    with DOWNLOAD_BRIDGE_STATE["lock"]:
        DOWNLOAD_BRIDGE_STATE["active_cases"][case["record_id"]] = signals


def get_active_case_info(record_id: str) -> dict[str, Any] | None:
    with DOWNLOAD_BRIDGE_STATE["lock"]:
        info = DOWNLOAD_BRIDGE_STATE["active_cases"].get(record_id)
        return dict(info) if info else None


def prune_expired_active_cases() -> None:
    now_ts = time()
    with DOWNLOAD_BRIDGE_STATE["lock"]:
        expired = [
            record_id
            for record_id, info in DOWNLOAD_BRIDGE_STATE["active_cases"].items()
            if float(info.get("watch_until") or 0) <= now_ts
        ]
        for record_id in expired:
            DOWNLOAD_BRIDGE_STATE["active_cases"].pop(record_id, None)


def score_event_for_case(event: dict[str, Any], case_info: dict[str, Any]) -> int:
    score = 0
    event_text = " ".join(
        str(event.get(key, "") or "").lower()
        for key in ("finalUrl", "referrer", "tabUrl", "filename", "mime")
    )

    if event.get("mime", "").lower() == "application/pdf":
        score += 2
    if str(event.get("filename", "")).lower().endswith(".pdf"):
        score += 2

    for host in case_info["hosts"]:
        if host and host in event_text:
            score += 4

    doi = case_info["doi"]
    if doi and doi in event_text:
        score += 8

    doi_token = case_info["doi_token"]
    if doi_token and doi_token in event_text.replace("/", "").replace(".", "").replace("-", ""):
        score += 6

    event_time = float(event.get("received_at") or time())
    opened_at = float(case_info.get("opened_at") or 0)
    if event_time >= opened_at:
        score += 3
        delta = event_time - opened_at
        if delta <= 300:
            score += 3
        elif delta <= 1800:
            score += 1
    else:
        score -= 10

    return score


def move_download_to_case(case: dict, source_path: Path) -> Path:
    if not source_path.exists():
        raise FileNotFoundError(f"Downloaded file not found: {source_path}")

    output_path = Path(case["output_file"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source_path), str(output_path))
    return output_path


def process_download_bridge_events(cases: list[dict]) -> None:
    case_map = {case["record_id"]: case for case in cases}
    decisions = st.session_state["scout_decisions"]

    with DOWNLOAD_BRIDGE_STATE["lock"]:
        events = DOWNLOAD_BRIDGE_STATE["events"]
        active_cases = dict(DOWNLOAD_BRIDGE_STATE["active_cases"])

        for event in events:
            if event.get("status") != "pending":
                continue

            filename = str(event.get("filename", "") or "").strip()
            if not filename.lower().endswith(".pdf"):
                event["status"] = "ignored"
                continue

            scores: list[tuple[int, str]] = []
            for record_id, case_info in active_cases.items():
                if record_id not in case_map:
                    continue
                score = score_event_for_case(event, case_info)
                if score > 0:
                    scores.append((score, record_id))

            scores.sort(reverse=True)
            if not scores:
                event["status"] = "unmatched"
                continue

            best_score, best_record_id = scores[0]
            second_score = scores[1][0] if len(scores) > 1 else -999
            if best_score < 8 or (best_score - second_score) < 3:
                event["status"] = "ambiguous"
                event["candidate_record_ids"] = [record_id for _, record_id in scores[:3]]
                continue

            try:
                saved_path = move_download_to_case(case_map[best_record_id], Path(filename))
            except Exception as exc:
                event["status"] = "error"
                event["error"] = str(exc)
                continue

            event["status"] = "matched"
            event["matched_record_id"] = best_record_id
            event["saved_path"] = str(saved_path)
            active_cases.pop(best_record_id, None)
            DOWNLOAD_BRIDGE_STATE["active_cases"].pop(best_record_id, None)

            case = case_map[best_record_id]
            current_notes = st.session_state.get(f"notes_{best_record_id}", decisions.get(best_record_id, {}).get("notes", ""))
            save_case_review(case, "downloaded_manual", current_notes, True)


def get_bridge_events_for_case(record_id: str) -> list[dict[str, Any]]:
    with DOWNLOAD_BRIDGE_STATE["lock"]:
        result = []
        for idx, event in enumerate(DOWNLOAD_BRIDGE_STATE["events"]):
            event_copy = dict(event)
            event_copy["event_index"] = idx
            if event.get("matched_record_id") == record_id:
                result.append(event_copy)
                continue
            if record_id in event.get("candidate_record_ids", []):
                result.append(event_copy)
        return result


def assign_download_event_to_case(event_index: int, case: dict) -> Path:
    with DOWNLOAD_BRIDGE_STATE["lock"]:
        event = DOWNLOAD_BRIDGE_STATE["events"][event_index]
        source_path = Path(str(event.get("filename", "")))

    saved_path = move_download_to_case(case, source_path)

    with DOWNLOAD_BRIDGE_STATE["lock"]:
        event = DOWNLOAD_BRIDGE_STATE["events"][event_index]
        event["status"] = "matched"
        event["matched_record_id"] = case["record_id"]
        event["saved_path"] = str(saved_path)
        event["candidate_record_ids"] = []
        DOWNLOAD_BRIDGE_STATE["active_cases"].pop(case["record_id"], None)

    current_notes = st.session_state.get(
        f"notes_{case['record_id']}",
        st.session_state["scout_decisions"].get(case["record_id"], {}).get("notes", ""),
    )
    save_case_review(case, "downloaded_manual", current_notes, True)
    return saved_path


def load_cases_from_report(report_path: Path) -> list[dict]:
    wb = load_workbook(report_path)
    try:
        ws = wb.active
        headers = [normalize_header(cell.value) for cell in ws[1]]
        rows: list[dict] = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not any(row):
                continue
            case = {headers[idx]: row[idx] for idx in range(min(len(headers), len(row)))}
            rows.append(
                {
                    "record_id": str(case.get("record_id", "") or "").strip(),
                    "title": str(case.get("title", "") or "").strip(),
                    "doi": str(case.get("doi", "") or "").strip(),
                    "doi_url": str(case.get("doi_url", "") or "").strip(),
                    "source_url": str(case.get("source_url", "") or "").strip(),
                    "output_file": str(case.get("output_file", "") or "").strip(),
                    "error_type": str(case.get("error_type", "") or "").strip(),
                    "error_message": str(case.get("error_message", "") or "").strip(),
                }
            )
        return rows
    finally:
        wb.close()


def review_output_path_for(report_path: Path) -> Path:
    target_dir = report_path.parent / "scout_reviews"
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir / f"{report_path.stem}_scout_review.xlsx"


def save_review_workbook(cases: list[dict], decisions: dict[str, dict], review_path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "scout_review"
    ws.append(
        [
            "record_id",
            "title",
            "doi",
            "doi_url",
            "source_url",
            "output_file",
            "original_error_type",
            "original_error_message",
            "decision",
            "notes",
            "reviewed_at",
            "pdf_saved",
        ]
    )

    for case in cases:
        record_id = case["record_id"]
        review = decisions.get(record_id, {})
        ws.append(
            [
                record_id,
                case["title"],
                case["doi"],
                case["doi_url"],
                case["source_url"],
                case["output_file"],
                case["error_type"],
                case["error_message"],
                review.get("decision", ""),
                review.get("notes", ""),
                review.get("reviewed_at", ""),
                "yes" if review.get("pdf_saved") else "no",
            ]
        )

    wb.save(review_path)


def load_existing_review(review_path: Path) -> dict[str, dict]:
    if not review_path.exists():
        return {}

    wb = load_workbook(review_path)
    try:
        ws = wb.active
        headers = [normalize_header(cell.value) for cell in ws[1]]
        decisions: dict[str, dict] = {}
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not any(row):
                continue
            data = {headers[idx]: row[idx] for idx in range(min(len(headers), len(row)))}
            record_id = str(data.get("record_id", "") or "").strip()
            if not record_id:
                continue
            decisions[record_id] = {
                "decision": str(data.get("decision", "") or "").strip(),
                "notes": str(data.get("notes", "") or "").strip(),
                "reviewed_at": str(data.get("reviewed_at", "") or "").strip(),
                "pdf_saved": str(data.get("pdf_saved", "") or "").strip().lower() == "yes",
            }
        return decisions
    finally:
        wb.close()


def find_resume_index(cases: list[dict], decisions: dict[str, dict]) -> int:
    if not cases:
        return 0

    for idx, case in enumerate(cases):
        review = decisions.get(case["record_id"], {})
        decision = str(review.get("decision", "") or "").strip()
        if not decision or decision == "pending_review":
            return idx

    return max(0, len(cases) - 1)


def load_report(report_path_value: str) -> None:
    report_path = Path(report_path_value).expanduser()
    cases = load_cases_from_report(report_path)
    review_path = review_output_path_for(report_path)
    decisions = load_existing_review(review_path)

    with DOWNLOAD_BRIDGE_STATE["lock"]:
        DOWNLOAD_BRIDGE_STATE["events"].clear()
        DOWNLOAD_BRIDGE_STATE["active_cases"].clear()

    st.session_state["scout_cases"] = cases
    st.session_state["scout_current_index"] = find_resume_index(cases, decisions)
    st.session_state["scout_report_path"] = str(report_path)
    st.session_state["scout_review_path"] = str(review_path)
    st.session_state["scout_decisions"] = decisions
    st.session_state["scout_loaded"] = True


def get_current_case() -> dict | None:
    cases = st.session_state["scout_cases"]
    if not cases:
        return None
    idx = max(0, min(st.session_state["scout_current_index"], len(cases) - 1))
    st.session_state["scout_current_index"] = idx
    return cases[idx]


def launch_scout_browser(url: str, case: dict) -> None:
    if not url:
        raise ValueError("No URL is available for this case.")

    label = f"{case.get('record_id', '')} - {case.get('title', '')}".strip(" -") or "Current case"
    opened = False
    launch_mode = "browser"

    if sys.platform.startswith("win"):
        browser_executable = find_windows_browser_executable()
        if browser_executable:
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            subprocess.Popen(
                [browser_executable, url],
                creationflags=creationflags,
                close_fds=False,
            )
            opened = True
            launch_mode = "browser tab"

    if not opened:
        opened = webbrowser.open_new(url)
        launch_mode = "new tab"

    if not opened:
        raise RuntimeError("The system browser could not be opened for this URL.")

    st.session_state["scout_download_markers"][case["record_id"]] = time()
    register_active_case(case)
    return None


def save_case_review(case: dict, decision: str, notes: str, pdf_saved: bool) -> None:
    record_id = case["record_id"]
    decisions = st.session_state["scout_decisions"]
    decisions[record_id] = {
        "decision": decision,
        "notes": notes.strip(),
        "reviewed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pdf_saved": pdf_saved,
    }
    save_review_workbook(
        st.session_state["scout_cases"],
        decisions,
        Path(st.session_state["scout_review_path"]),
    )


def clear_case_review(case: dict) -> None:
    record_id = case["record_id"]
    decisions = st.session_state["scout_decisions"]
    decisions.pop(record_id, None)
    save_review_workbook(
        st.session_state["scout_cases"],
        decisions,
        Path(st.session_state["scout_review_path"]),
    )


def sync_case_review_from_widgets(case: dict, existing: dict) -> None:
    record_id = case["record_id"]
    decision_value = st.session_state.get(f"decision_{record_id}", existing.get("decision", "pending_review"))
    notes_value = st.session_state.get(f"notes_{record_id}", existing.get("notes", ""))
    pdf_saved_value = bool(existing.get("pdf_saved", False))

    if decision_value == "pending_review":
        if record_id in st.session_state["scout_decisions"]:
            clear_case_review(case)
        return

    if (
        existing.get("decision") != decision_value
        or existing.get("notes", "") != notes_value.strip()
        or bool(existing.get("pdf_saved", False)) != pdf_saved_value
    ):
        save_case_review(case, decision_value, notes_value, pdf_saved_value)


def get_new_download_candidates(case: dict) -> list[Path]:
    downloads_dir = Path.home() / "Downloads"
    if not downloads_dir.exists():
        return []

    record_id = case["record_id"]
    marker = st.session_state.get("scout_download_markers", {}).get(record_id)
    if marker is None:
        return []

    return sorted(
        [
            path for path in downloads_dir.glob("*.pdf")
            if path.is_file() and path.stat().st_mtime >= marker
        ],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def import_latest_downloaded_pdf(case: dict) -> Path:
    candidates = get_new_download_candidates(case)
    record_id = case["record_id"]
    if st.session_state.get("scout_download_markers", {}).get(record_id) is None:
        raise RuntimeError("Open the DOI or source link for this case first so S.C.O.U.T. can watch for a new download.")
    if not candidates:
        raise FileNotFoundError("No new PDF downloads were found for this case since the link was opened.")

    if len(candidates) > 1:
        candidate_names = ", ".join(path.name for path in sorted(candidates, key=lambda path: path.stat().st_mtime, reverse=True)[:3])
        raise RuntimeError(
            "More than one new PDF was found in Downloads for this case. "
            f"Candidates: {candidate_names}. Use manual upload instead."
        )

    latest_pdf = candidates[0]
    output_path = Path(case["output_file"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(latest_pdf), str(output_path))
    st.session_state["scout_download_markers"].pop(record_id, None)
    with DOWNLOAD_BRIDGE_STATE["lock"]:
        DOWNLOAD_BRIDGE_STATE["active_cases"].pop(record_id, None)
    return output_path


def try_auto_import_download_for_case(case: dict) -> Path | None:
    output_file = str(case.get("output_file", "") or "").strip()
    if output_file and Path(output_file).exists():
        return None

    candidates = get_new_download_candidates(case)
    if len(candidates) != 1:
        return None

    saved_path = import_latest_downloaded_pdf(case)
    st.session_state[f"decision_{case['record_id']}"] = "downloaded_manual"
    current_notes = st.session_state.get(f"notes_{case['record_id']}", "")
    save_case_review(case, "downloaded_manual", current_notes, True)
    return saved_path


def try_auto_import_downloads(cases: list[dict]) -> tuple[dict | None, Path | None]:
    for case in cases:
        saved_path = try_auto_import_download_for_case(case)
        if saved_path is not None:
            return case, saved_path
    return None, None


def build_progress_stats(cases: list[dict], decisions: dict[str, dict]) -> dict[str, int]:
    stats = {
        "pending": 0,
        "downloaded": 0,
        "paywalled": 0,
        "unavailable": 0,
        "other_done": 0,
        "pdf_saved": 0,
    }

    for case in cases:
        review = decisions.get(case["record_id"], {})
        decision = str(review.get("decision", "") or "").strip()
        pdf_saved = bool(review.get("pdf_saved", False))

        if not decision or decision == "pending_review":
            stats["pending"] += 1
        elif decision == "downloaded_manual":
            stats["downloaded"] += 1
        elif decision == "paywalled":
            stats["paywalled"] += 1
        elif decision in {"unavailable", "article_not_found", "wrong_link"}:
            stats["unavailable"] += 1
        else:
            stats["other_done"] += 1

        if pdf_saved:
            stats["pdf_saved"] += 1

    return stats


def render_header() -> None:
    st.markdown(
        """
        <style>
        :root {
            --scout-hero-bg: color-mix(in srgb, var(--primary-color) 18%, var(--secondary-background-color) 82%);
            --scout-summary-bg: color-mix(in srgb, var(--primary-color) 11%, var(--secondary-background-color) 89%);
            --scout-panel-bg: var(--secondary-background-color);
            --scout-hero-border: color-mix(in srgb, var(--primary-color) 34%, transparent);
            --scout-summary-border: color-mix(in srgb, var(--primary-color) 24%, transparent);
            --scout-panel-border: color-mix(in srgb, var(--text-color) 12%, transparent);
            --scout-hero-shadow: 0 10px 30px color-mix(in srgb, var(--primary-color) 12%, transparent);
            --scout-summary-shadow: 0 10px 28px color-mix(in srgb, var(--primary-color) 8%, transparent);
        }
        header[data-testid="stHeader"] {
            height: auto;
        }
        [data-testid="stToolbar"] {
            visibility: visible;
        }
        #MainMenu {
            visibility: visible;
        }
        .stAppDeployButton {
            display: none;
        }
        .block-container {
            padding-top: 3.25rem;
        }
        .scout-card {
            padding: 0.9rem 1.1rem 0.95rem 1.1rem;
            border: 1px solid var(--scout-hero-border);
            border-radius: 18px;
            background: var(--scout-hero-bg);
            box-shadow: var(--scout-hero-shadow);
            margin-top: 0;
            margin-bottom: 0.75rem;
        }
        .scout-title {
            font-size: 1.95rem;
            font-weight: 800;
            margin: 0.15rem 0 0.35rem 0;
        }
        .scout-title-accent {
            color: #7dd3fc;
        }
        .scout-sub {
            color: #aab4bf;
            margin: 0;
        }
        .scout-stats {
            padding: 0.95rem 1.1rem 1rem 1.1rem;
            border: 1px solid var(--scout-summary-border);
            border-radius: 18px;
            background: var(--scout-summary-bg);
            box-shadow: var(--scout-summary-shadow);
            margin-bottom: 1rem;
        }
        .scout-panel {
            padding: 0.95rem 1.05rem 1rem 1.05rem;
            border: 1px solid var(--scout-panel-border);
            border-radius: 18px;
            background: var(--scout-panel-bg);
            margin-bottom: 1rem;
        }
        .scout-panel-title {
            color: inherit;
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 0.8rem;
        }
        .scout-stats-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 1rem;
        }
        .scout-stat-label {
            color: inherit;
            opacity: 0.78;
            font-size: 0.95rem;
            font-weight: 600;
            margin-bottom: 0.45rem;
        }
        .scout-stat-value {
            color: inherit;
            font-size: 2rem;
            font-weight: 700;
            line-height: 1;
        }
        .scout-section-heading {
            color: #67b8ff;
            font-size: 1rem;
            font-weight: 800;
            margin: 0 0 1rem 0;
            padding-bottom: 0.6rem;
            border-bottom: 1px solid rgba(120, 130, 150, 0.28);
            letter-spacing: 0.01em;
        }
        .scout-article-title {
            color: inherit;
            font-size: clamp(1.7rem, 2.3vw, 2.5rem);
            font-weight: 800;
            line-height: 1.1;
            letter-spacing: -0.03em;
            margin: 0 0 1rem 0;
            text-wrap: balance;
        }
        .scout-stat-list {
            display: grid;
            gap: 0.55rem;
            max-width: 24rem;
            min-height: 18.5rem;
            padding-bottom: 0.45rem;
        }
        .scout-stat-row {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            align-items: center;
            column-gap: 0.85rem;
            padding: 0.1rem 0;
        }
        .scout-stat-row-label {
            font-size: 0.95rem;
            font-weight: 600;
            color: inherit;
            line-height: 1.25;
        }
        .scout-stat-row-value {
            min-width: 2rem;
            text-align: center;
            font-size: 1rem;
            font-weight: 700;
            color: #4f8f63;
            line-height: 1;
            background: rgba(120, 130, 150, 0.08);
            border-radius: 0.45rem;
            padding: 0.18rem 0.42rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            justify-self: end;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="scout-card">
            <div class="scout-title"><span class="scout-title-accent">S.C.O.U.T.</span> - Semi-assisted Case Opening and User Triage</div>
            <p class="scout-sub">
                Review failed cases one by one, open the article link in your browser,
                match PDF downloads back to the current case, and classify unresolved cases with
                structured decisions.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_loader() -> None:
    default_path = r"C:\Users\Luís Pinto Coelho\Desktop\resolver_tests\wiley\reports\wiley_failed_cases_2026-04-06_14-46-15.xlsx"
    with st.sidebar:
        with st.expander("Report source", expanded=st.session_state["scout_report_source_expanded"]):
            report_path_value = st.text_input("Failed-cases Excel path", value=default_path)
            if st.button("Load failed cases", use_container_width=True):
                try:
                    load_report(report_path_value)
                    st.session_state["scout_report_source_expanded"] = False
                    st.success("Failed-case report loaded.")
                    st.rerun()
                except Exception as exc:
                    st.session_state["scout_report_source_expanded"] = True
                    st.error(f"Could not load report: {exc}")


def render_sidebar(case: dict, total_cases: int) -> None:
    idx = st.session_state["scout_current_index"]
    decisions = st.session_state["scout_decisions"]
    existing = decisions.get(case["record_id"], {})

    with st.sidebar:
        st.header("Navigator")
        st.caption(f"Case {idx + 1} of {total_cases}")

        st.progress((idx + 1) / total_cases if total_cases else 0.0)

        col_prev, col_next = st.columns(2)
        with col_prev:
            if st.button("Previous", use_container_width=True, disabled=idx <= 0):
                st.session_state["scout_current_index"] = max(0, idx - 1)
                st.rerun()
        with col_next:
            if st.button("Next", use_container_width=True, disabled=idx >= total_cases - 1):
                st.session_state["scout_current_index"] = min(total_cases - 1, idx + 1)
                st.rerun()

        with st.expander("Advanced navigation", expanded=False):
            col_first, col_last = st.columns(2)
            with col_first:
                if st.button("First", use_container_width=True, disabled=idx <= 0):
                    st.session_state["scout_current_index"] = 0
                    st.rerun()
            with col_last:
                if st.button("Last", use_container_width=True, disabled=idx >= total_cases - 1):
                    st.session_state["scout_current_index"] = max(0, total_cases - 1)
                    st.rerun()

            first_pending_index = find_resume_index(st.session_state["scout_cases"], decisions)
            if st.button(
                "Go to first pending",
                use_container_width=True,
                disabled=first_pending_index == idx,
            ):
                st.session_state["scout_current_index"] = first_pending_index
                st.rerun()

            with st.form(key="scout_go_to_case_form", clear_on_submit=False):
                go_to_case = st.number_input(
                    "Go to case",
                    min_value=1,
                    max_value=max(1, total_cases),
                    value=idx + 1,
                    step=1,
                    format="%d",
                    key="scout_go_to_case",
                )
                go_to_case_submitted = st.form_submit_button("Go", use_container_width=True)

            if go_to_case_submitted and int(go_to_case) != idx + 1:
                st.session_state["scout_current_index"] = int(go_to_case) - 1
                st.rerun()

        if st.button("Open article link", use_container_width=True, key=f"open_article_sidebar_{case['record_id']}"):
            launch_url, _launch_url_kind = get_preferred_case_url(case)
            try:
                launch_scout_browser(launch_url, case)
                st.session_state["scout_browser_message"] = ""
            except Exception as exc:
                st.session_state["scout_browser_message"] = f"Could not open article link: {exc}"
            st.rerun()

        if st.button("Import PDF from Downloads", use_container_width=True, key=f"import_download_sidebar_{case['record_id']}"):
            try:
                saved_path = import_latest_downloaded_pdf(case)
                current_notes = st.session_state.get(f"notes_{case['record_id']}", existing.get("notes", ""))
                save_case_review(case, "downloaded_manual", current_notes, True)
                st.success(f"PDF moved to `{saved_path}`")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not import PDF from Downloads: {exc}")

        st.header("Decision")
        default_decision = existing.get("decision", "pending_review")
        decision_index = DECISION_OPTIONS.index(default_decision) if default_decision in DECISION_OPTIONS else 0
        decision = st.radio(
            "Decision",
            DECISION_OPTIONS,
            index=decision_index,
            key=f"decision_{case['record_id']}",
            label_visibility="collapsed",
        )
        notes = st.text_area(
            "Notes",
            value=existing.get("notes", ""),
            height=140,
            key=f"notes_{case['record_id']}",
        )
        sync_case_review_from_widgets(case, existing)



def render_case(case: dict) -> None:
    decisions = st.session_state["scout_decisions"]
    existing = decisions.get(case["record_id"], {})
    bridge_events = get_bridge_events_for_case(case["record_id"])
    launch_url, _launch_url_kind = get_preferred_case_url(case)
    progress_stats = build_progress_stats(st.session_state["scout_cases"], decisions)

    col_main, col_side = st.columns([3.2, 1.8], vertical_alignment="top")

    with col_main:
        with st.container(border=True):
            st.markdown('<div class="scout-section-heading">Article Information</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="scout-article-title">{case["title"] or "(Untitled case)"}</div>',
                unsafe_allow_html=True,
            )
            st.write(f"**Record ID:** `{case['record_id']}`")
            st.write(f"**DOI:** `{case['doi'] or '-'}`")
            st.write(f"**Original error:** `{case['error_type'] or '-'}`")
            st.write(f"**Error detail:** {case['error_message'] or '-'}")

            browser_message = st.session_state.get("scout_browser_message", "")
            if browser_message:
                st.info(browser_message)

            st.markdown('<div class="scout-section-heading">Links and Output</div>', unsafe_allow_html=True)
            st.write(f"**Source URL:** `{case['source_url'] or '-'}`")
            st.write(f"**DOI URL:** `{case['doi_url'] or '-'}`")
            st.write(f"**Expected output file:** `{case['output_file'] or '-'}`")

            output_path = Path(case["output_file"]) if case["output_file"] else None
            if output_path and output_path.exists():
                st.success(f"PDF already exists: `{output_path}`")
            elif output_path:
                st.info("Expected PDF file does not exist yet.")

    with col_side:
        if bridge_events:
            with st.container(border=True):
                st.markdown('<div class="scout-section-heading">Recent Downloads</div>', unsafe_allow_html=True)
                for event in bridge_events[-3:]:
                    status = event.get("status", "pending")
                    filename = Path(str(event.get("filename", "") or "")).name or "(unknown file)"
                    st.caption(f"`{status}` - `{filename}`")
                    if status == "matched" and event.get("saved_path"):
                        st.write(f"Saved to `{event['saved_path']}`")
                    if status == "ambiguous":
                        if st.button("Use this download for current case", use_container_width=True, key=f"assign_event_{event['event_index']}"):
                            try:
                                saved_path = assign_download_event_to_case(event["event_index"], case)
                                st.success(f"Download assigned to `{saved_path}`")
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Could not assign download: {exc}")

        if existing:
            with st.container(border=True):
                st.markdown('<div class="scout-section-heading">Saved Review</div>', unsafe_allow_html=True)
                st.write(f"Decision: `{existing.get('decision', '-')}`")
                st.write(f"Reviewed at: `{existing.get('reviewed_at', '-')}`")
                st.write(f"PDF saved: `{'yes' if existing.get('pdf_saved') else 'no'}`")

        with st.container(border=True):
            st.markdown('<div class="scout-section-heading">Review Stats</div>', unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class="scout-stat-list">
                    <div class="scout-stat-row">
                        <div class="scout-stat-row-label">Pending</div>
                        <div class="scout-stat-row-value">{progress_stats['pending']}</div>
                    </div>
                    <div class="scout-stat-row">
                        <div class="scout-stat-row-label">Downloaded</div>
                        <div class="scout-stat-row-value">{progress_stats['downloaded']}</div>
                    </div>
                    <div class="scout-stat-row">
                        <div class="scout-stat-row-label">Paywalled</div>
                        <div class="scout-stat-row-value">{progress_stats['paywalled']}</div>
                    </div>
                    <div class="scout-stat-row">
                        <div class="scout-stat-row-label">Unavailable / wrong link</div>
                        <div class="scout-stat-row-value">{progress_stats['unavailable']}</div>
                    </div>
                    <div class="scout-stat-row">
                        <div class="scout-stat-row-label">Other completed</div>
                        <div class="scout-stat-row-value">{progress_stats['other_done']}</div>
                    </div>
                    <div class="scout-stat-row">
                        <div class="scout-stat-row-label">PDFs saved</div>
                        <div class="scout-stat-row-value">{progress_stats['pdf_saved']}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_summary() -> None:
    decisions = st.session_state["scout_decisions"]
    cases = st.session_state["scout_cases"]
    total = len(cases)
    reviewed = sum(1 for case in cases if case["record_id"] in decisions)
    downloaded = sum(1 for value in decisions.values() if value.get("decision") == "downloaded_manual")

    st.markdown(
        f"""
        <div class="scout-stats">
            <div class="scout-stats-grid">
                <div>
                    <div class="scout-stat-label">Cases</div>
                    <div class="scout-stat-value">{total}</div>
                </div>
                <div>
                    <div class="scout-stat-label">Reviewed</div>
                    <div class="scout-stat-value">{reviewed}</div>
                </div>
                <div>
                    <div class="scout-stat-label">Manual downloads</div>
                    <div class="scout-stat-value">{downloaded}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def should_auto_refresh_case(case: dict) -> tuple[bool, int]:
    output_file = str(case.get("output_file", "") or "").strip()
    if output_file and Path(output_file).exists():
        return False, 0

    active_info = get_active_case_info(case["record_id"])
    if not active_info:
        return False, 0

    remaining = int(max(0, float(active_info.get("watch_until") or 0) - time()))
    if remaining <= 0:
        return False, 0

    return True, remaining


def render_controlled_auto_refresh(case: dict) -> None:
    should_refresh, remaining = should_auto_refresh_case(case)
    if not should_refresh:
        return

    st.caption(f"Watching for a matching PDF download. Auto-check active for about {remaining}s more.")
    components.html(
        """
        <script>
        const refreshMs = 2500;
        const tick = () => {
            try {
                const parentWindow = window.parent;
                if (parentWindow && parentWindow.location && !parentWindow.document.hidden) {
                    parentWindow.location.reload();
                }
            } catch (e) {
                console.debug("Scout auto-refresh skipped", e);
            }
        };
        setTimeout(tick, refreshMs);
        </script>
        """,
        height=0,
        width=0,
    )


def main() -> None:
    set_page()
    init_state()
    start_download_bridge_server()
    prune_expired_active_cases()
    render_header()
    render_loader()

    if not st.session_state["scout_loaded"]:
        st.info("Load a failed-case Excel report to start reviewing cases.")
        return

    cases = st.session_state["scout_cases"]
    process_download_bridge_events(cases)
    auto_saved_case, auto_saved_path = try_auto_import_downloads(cases)
    if auto_saved_path is not None and auto_saved_case is not None:
        st.session_state["scout_browser_message"] = (
            f"S.C.O.U.T. detected a new PDF download for `{auto_saved_case['record_id']}` and saved it to `{auto_saved_path}`."
        )
        st.rerun()

    case = get_current_case()
    if case is None:
        st.warning("No cases available in the loaded report.")
        return

    render_sidebar(case, len(cases))
    render_summary()
    render_case(case)
    render_controlled_auto_refresh(case)


if __name__ == "__main__":
    main()
