# ui/components.py
from __future__ import annotations

import time
from typing import Dict, List

import streamlit as st

from app.utils import format_seconds


def ensure_streamlit_state() -> None:
    """
    Ensure the required session_state keys exist.
    """
    defaults = {
        "logs": [],
        "phase1_payload": None,
        "phase2_payload": None,
        "final_summary": None,
        "save_events": [],
        "run_status": "idle",
        "run_error": "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def append_log(message: str) -> None:
    """
    Append one log line to session state.
    """
    ensure_streamlit_state()
    timestamp = time.strftime("%H:%M:%S")
    st.session_state["logs"].append(f"[{timestamp}] {message}")


def build_phase1_lines(payload: Dict) -> List[str]:
    processed = payload["processed"]
    total = payload["total"]
    workers = payload["workers"]
    start_time = payload["start_time"]
    last_record_id = payload["last_record_id"]
    last_status = payload["last_status"]
    pdfs_available_global = payload["pdfs_available_global"]
    downloaded_now_total = payload["downloaded_now_total"]

    remaining_count = max(0, total - processed)
    failures_count = max(0, processed - pdfs_available_global)
    elapsed = time.time() - start_time

    if processed > 0:
        estimated_total = (elapsed / processed) * total
        estimated_remaining = max(0.0, estimated_total - elapsed)
    else:
        estimated_total = 0.0
        estimated_remaining = 0.0

    success_rate_global = (pdfs_available_global / total * 100) if total > 0 else 0.0

    return [
        "PHASE 1 - BASE DOWNLOAD",
        f"Processed               : {processed}",
        f"Remaining               : {remaining_count}",
        f"Total                   : {total}",
        f"Workers                 : {workers}",
        f"PDFs available          : {pdfs_available_global}",
        f"Downloaded now          : {downloaded_now_total}",
        f"Failures                : {failures_count}",
        f"Global success rate     : {success_rate_global:6.2f}%",
        f"Elapsed                 : {format_seconds(elapsed)}",
        f"Estimated total         : {format_seconds(estimated_total)}",
        f"Estimated remaining     : {format_seconds(estimated_remaining)}",
        f"Last record             : {last_record_id or '-'}",
        f"Last status             : {last_status or '-'}",
    ]


def build_phase2_lines(payload: Dict) -> List[str]:
    retry_processed = payload["retry_processed"]
    retry_total = payload["retry_total"]
    phase2_start_time = payload["phase2_start_time"]
    resolver_name = payload["resolver_name"]
    last_record_id = payload["last_record_id"]
    last_doi = payload["last_doi"]
    last_status = payload["last_status"]
    pdfs_available_global = payload["pdfs_available_global"]
    downloaded_now_total = payload["downloaded_now_total"]
    recovered_this_phase = payload["recovered_this_phase"]
    total_records = payload["total_records"]

    retry_remaining = max(0, retry_total - retry_processed)
    phase2_still_without_pdf = max(0, retry_processed - recovered_this_phase)
    elapsed = time.time() - phase2_start_time

    if retry_processed > 0:
        estimated_total = (elapsed / retry_processed) * retry_total
        estimated_remaining = max(0.0, estimated_total - elapsed)
    else:
        estimated_total = 0.0
        estimated_remaining = 0.0

    success_rate_global = (pdfs_available_global / total_records * 100) if total_records > 0 else 0.0

    return [
        "PHASE 2 - SPECIALIZED RETRY",
        f"Resolver                : {resolver_name or '-'}",
        f"Retry total             : {retry_total}",
        f"Processed               : {retry_processed}",
        f"Remaining               : {retry_remaining}",
        f"PDFs available          : {pdfs_available_global}",
        f"Downloaded now          : {downloaded_now_total}",
        f"Recovered this phase    : {recovered_this_phase}",
        f"Still without PDF       : {phase2_still_without_pdf}",
        f"Global success rate     : {success_rate_global:6.2f}%",
        f"Elapsed                 : {format_seconds(elapsed)}",
        f"Estimated total         : {format_seconds(estimated_total)}",
        f"Estimated remaining     : {format_seconds(estimated_remaining)}",
        f"Last record             : {last_record_id or '-'}",
        f"Last DOI                : {last_doi or '-'}",
        f"Last status             : {last_status or '-'}",
    ]


def make_streamlit_reporter():
    """
    Return a reporter callback compatible with app.pipeline.emit(...).
    """
    ensure_streamlit_state()

    def reporter(event_name: str, payload: dict) -> None:
        if event_name in {"phase1_start", "phase1_update", "phase1_end"}:
            st.session_state["phase1_payload"] = payload

            if event_name == "phase1_start":
                append_log("Phase 1 started.")
            elif event_name == "phase1_end":
                append_log("Phase 1 finished.")

        elif event_name in {"phase2_start", "phase2_update", "phase2_end"}:
            st.session_state["phase2_payload"] = payload

            if event_name == "phase2_start":
                append_log("Phase 2 started.")
            elif event_name == "phase2_end":
                append_log("Phase 2 finished.")

        elif event_name == "save":
            st.session_state["save_events"].append(payload)
            append_log(
                f"Workbook save event | phase={payload.get('phase')} | ok={payload.get('ok')}"
            )

        elif event_name == "finish":
            st.session_state["final_summary"] = payload
            append_log("Pipeline finished.")

    return reporter


def render_status_panels() -> None:
    """
    Render phase status blocks and summary information.
    """
    ensure_streamlit_state()

    phase1_payload = st.session_state.get("phase1_payload")
    phase2_payload = st.session_state.get("phase2_payload")
    final_summary = st.session_state.get("final_summary")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Phase 1")
        if phase1_payload:
            st.code("\n".join(build_phase1_lines(phase1_payload)), language="text")
        else:
            st.info("Phase 1 not started yet.")

    with col2:
        st.subheader("Phase 2")
        if phase2_payload:
            st.code("\n".join(build_phase2_lines(phase2_payload)), language="text")
        else:
            st.info("Phase 2 not started yet.")

    st.subheader("Logs")
    logs = st.session_state.get("logs", [])
    st.text_area(
        "Execution log",
        value="\n".join(logs),
        height=250,
        label_visibility="collapsed",
    )

    if final_summary:
        st.subheader("Final summary")
        phase2 = final_summary["phase2"]

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("PDFs available", phase2["pdfs_available_global"])
        with c2:
            st.metric("Downloaded now", phase2["downloaded_now_total"])
        with c3:
            st.metric("Recovered in phase 2", phase2["recovered_this_phase"])

        st.write(f"**Output workbook:** `{final_summary['output_workbook_path']}`")


def reset_run_state() -> None:
    """
    Reset state before a new run.
    """
    st.session_state["logs"] = []
    st.session_state["phase1_payload"] = None
    st.session_state["phase2_payload"] = None
    st.session_state["final_summary"] = None
    st.session_state["save_events"] = []
    st.session_state["run_status"] = "idle"
    st.session_state["run_error"] = ""