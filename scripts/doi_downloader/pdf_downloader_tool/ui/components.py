from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List, Optional

import streamlit as st

from app.models import SessionState
from app.utils import format_seconds


def ensure_streamlit_state() -> None:
    """
    Ensure the required Streamlit session_state keys exist.
    """
    defaults = {
        "app_session": None,
        "logs": [],
        "phase0_payload": None,
        "phase1_payload": None,
        "phase2_payload": None,
        "diagnostic_payload": None,
        "final_summary": None,
        "last_phase1_results_by_row": None,
        "last_phase1_summary": None,
        "last_phase2_summary": None,
        "last_phase0_summary": None,
        "last_diagnostic_summary": None,
        "save_events": [],
        "run_status": "idle",
        "run_error": "",
        "last_report_path": "",
        "last_output_path": "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_app_session() -> Optional[SessionState]:
    ensure_streamlit_state()
    return st.session_state.get("app_session")


def set_app_session(session: Optional[SessionState]) -> None:
    ensure_streamlit_state()
    st.session_state["app_session"] = session


def append_log(message: str) -> None:
    """
    Append one log line to session state.
    """
    ensure_streamlit_state()
    timestamp = time.strftime("%H:%M:%S")
    st.session_state["logs"].append(f"[{timestamp}] {message}")


def build_phase0_lines(payload: Dict) -> List[str]:
    processed = payload["processed"]
    total = payload["total"]
    start_time = payload["start_time"]

    total_rows_read = payload.get("total_rows_read", 0)
    total_existing_doi = payload.get("total_existing_doi", 0)
    total_missing_doi = payload.get("total_missing_doi", 0)
    total_eligible = payload.get("total_eligible", 0)
    total_skipped_missing_title = payload.get("total_skipped_missing_title", 0)
    total_skipped_already_downloaded = payload.get("total_skipped_already_downloaded", 0)
    total_enriched = payload.get("total_enriched", 0)
    total_unresolved = payload.get("total_unresolved", 0)
    total_errors = payload.get("total_errors", 0)

    last_record_id = payload.get("last_record_id", "")
    last_title = payload.get("last_title", "")
    last_status = payload.get("last_status", "")
    last_doi = payload.get("last_doi", "")
    last_confidence = payload.get("last_confidence", "")
    report_path = payload.get("report_path", "")

    remaining_count = max(0, total - processed)
    elapsed = time.time() - start_time

    if processed > 0:
        estimated_total = (elapsed / processed) * total
        estimated_remaining = max(0.0, estimated_total - elapsed)
    else:
        estimated_total = 0.0
        estimated_remaining = 0.0

    enrichment_rate = (total_enriched / processed * 100.0) if processed > 0 else 0.0

    lines = [
        "PHASE 0 - DOI ENRICHMENT",
        f"Rows read               : {total_rows_read}",
        f"Existing DOI            : {total_existing_doi}",
        f"Missing DOI             : {total_missing_doi}",
        f"Eligible                : {total_eligible}",
        f"Skipped no title        : {total_skipped_missing_title}",
        f"Skipped already PDF     : {total_skipped_already_downloaded}",
        f"Processed               : {processed}",
        f"Remaining               : {remaining_count}",
        f"Enriched                : {total_enriched}",
        f"Unresolved              : {total_unresolved}",
        f"Errors                  : {total_errors}",
        f"Enrichment rate         : {enrichment_rate:6.2f}%",
        f"Elapsed                 : {format_seconds(elapsed)}",
        f"Estimated total         : {format_seconds(estimated_total)}",
        f"Estimated remaining     : {format_seconds(estimated_remaining)}",
        f"Last record             : {last_record_id or '-'}",
        f"Last title              : {last_title or '-'}",
        f"Last status             : {last_status or '-'}",
        f"Last DOI                : {last_doi or '-'}",
        f"Last confidence         : {last_confidence or '-'}",
    ]

    if report_path:
        lines.append(f"Report path             : {report_path}")

    return lines


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


def build_diagnostic_lines(payload: Dict) -> List[str]:
    processed = payload["processed"]
    total = payload["total"]
    workers = payload["workers"]
    start_time = payload["start_time"]
    last_record_id = payload["last_record_id"]
    last_status = payload["last_status"]
    title = payload.get("title", "DIAGNOSTIC")
    report_path = payload.get("report_path", "")
    stopped_early = payload.get("stopped_early", False)

    remaining_count = max(0, total - processed)
    elapsed = time.time() - start_time

    if processed > 0:
        estimated_total = (elapsed / processed) * total
        estimated_remaining = max(0.0, estimated_total - elapsed)
    else:
        estimated_total = 0.0
        estimated_remaining = 0.0

    return [
        f"{title}",
        f"Processed               : {processed}",
        f"Remaining               : {remaining_count}",
        f"Total                   : {total}",
        f"Workers                 : {workers}",
        f"Elapsed                 : {format_seconds(elapsed)}",
        f"Estimated total         : {format_seconds(estimated_total)}",
        f"Estimated remaining     : {format_seconds(estimated_remaining)}",
        f"Last record             : {last_record_id or '-'}",
        f"Last status             : {last_status or '-'}",
        f"Stopped early           : {'Yes' if stopped_early else 'No'}",
        f"Report path             : {report_path or '-'}",
    ]


def render_panel(title: str, lines: List[str] | None, empty_message: str) -> None:
    st.markdown(f"**{title}**")
    if lines:
        st.code("\n".join(lines), language="text")
    else:
        st.info(empty_message)


def render_live_panels(placeholders: Optional[Dict[str, object]] = None) -> None:
    """
    Render a compact execution monitor only while an action is running.
    """
    if placeholders is None:
        return

    root = placeholders.get("root")
    if root is None:
        return

    ensure_streamlit_state()

    phase0_payload = st.session_state.get("phase0_payload")
    phase1_payload = st.session_state.get("phase1_payload")
    phase2_payload = st.session_state.get("phase2_payload")
    diagnostic_payload = st.session_state.get("diagnostic_payload")
    logs = st.session_state.get("logs", [])

    with root.container():
        st.subheader("Execution monitor")

        col1, col2 = st.columns(2)
        with col1:
            render_panel(
                "Phase 0",
                build_phase0_lines(phase0_payload) if phase0_payload else None,
                "Phase 0 not started.",
            )
        with col2:
            render_panel(
                "Diagnostic",
                build_diagnostic_lines(diagnostic_payload) if diagnostic_payload else None,
                "Diagnostic not started.",
            )

        col3, col4 = st.columns(2)
        with col3:
            render_panel(
                "Phase 1",
                build_phase1_lines(phase1_payload) if phase1_payload else None,
                "Phase 1 not started.",
            )
        with col4:
            render_panel(
                "Phase 2",
                build_phase2_lines(phase2_payload) if phase2_payload else None,
                "Phase 2 not started.",
            )

        st.markdown("**Live logs**")
        st.text_area(
            "Live execution log",
            value="\n".join(logs),
            height=180,
            key="live_logs_text_area",
            label_visibility="collapsed",
        )


def clear_live_placeholders(placeholders: Optional[Dict[str, object]]) -> None:
    if placeholders is None:
        return

    root = placeholders.get("root")
    if root is not None:
        root.empty()


def make_streamlit_reporter(placeholders: Optional[Dict[str, object]] = None):
    """
    Return a reporter callback compatible with app.pipeline.emit(...).
    """
    ensure_streamlit_state()

    def reporter(event_name: str, payload: dict) -> None:
        if event_name in {"phase0_start", "phase0_update", "phase0_end"}:
            st.session_state["phase0_payload"] = payload

            if event_name == "phase0_start":
                append_log("Phase 0 started.")
            elif event_name == "phase0_end":
                st.session_state["last_phase0_summary"] = payload
                if payload.get("report_path"):
                    st.session_state["last_report_path"] = payload["report_path"]
                    append_log(f"Phase 0 report saved: {payload['report_path']}")
                append_log("Phase 0 finished.")

        elif event_name in {"phase1_start", "phase1_update", "phase1_end"}:
            st.session_state["phase1_payload"] = payload

            if event_name == "phase1_start":
                append_log("Phase 1 started.")
            elif event_name == "phase1_end":
                st.session_state["last_phase1_summary"] = payload
                append_log("Phase 1 finished.")

        elif event_name in {"phase2_start", "phase2_update", "phase2_end"}:
            st.session_state["phase2_payload"] = payload

            if event_name == "phase2_start":
                append_log("Phase 2 started.")
            elif event_name == "phase2_end":
                st.session_state["last_phase2_summary"] = payload
                append_log("Phase 2 finished.")

        elif event_name in {"diagnostic_start", "diagnostic_update", "diagnostic_end"}:
            st.session_state["diagnostic_payload"] = payload

            if event_name == "diagnostic_start":
                append_log(f"Diagnostic started: {payload.get('title', 'DIAGNOSTIC')}")
            elif event_name == "diagnostic_end":
                st.session_state["last_diagnostic_summary"] = payload
                if payload.get("report_path"):
                    st.session_state["last_report_path"] = payload["report_path"]
                    append_log(f"Diagnostic report saved: {payload['report_path']}")
                append_log("Diagnostic finished.")

        elif event_name == "save":
            st.session_state["save_events"].append(payload)
            append_log(
                f"Workbook save event | phase={payload.get('phase')} | ok={payload.get('ok')} | path={payload.get('path', '')}"
            )

        elif event_name == "finish":
            st.session_state["final_summary"] = payload
            if payload.get("output_workbook_path"):
                st.session_state["last_output_path"] = payload["output_workbook_path"]
            append_log("Pipeline finished.")

        render_live_panels(placeholders)

    return reporter


def render_session_summary() -> None:
    ensure_streamlit_state()
    session = get_app_session()

    st.subheader("Session")
    if session is None:
        st.info("No workbook session loaded.")
        return

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Workbook loaded", "Yes" if session.is_workbook_loaded else "No")
    with c2:
        st.metric("Current phase", session.current_phase or "-")
    with c3:
        st.metric("Records", len(session.records))
    with c4:
        st.metric("Retry tasks", len(session.retry_tasks))

    st.write(f"**Workbook path:** `{session.workbook_path}`")
    st.write(f"**Sheet:** `{session.sheet_name}`")


def render_phase_snapshots() -> None:
    phase0_payload = st.session_state.get("phase0_payload")
    phase1_payload = st.session_state.get("phase1_payload")
    phase2_payload = st.session_state.get("phase2_payload")
    diagnostic_payload = st.session_state.get("diagnostic_payload")

    st.subheader("Execution snapshots")

    col1, col2 = st.columns(2)
    with col1:
        render_panel(
            "Phase 0",
            build_phase0_lines(phase0_payload) if phase0_payload else None,
            "Phase 0 not started yet.",
        )
    with col2:
        render_panel(
            "Diagnostic",
            build_diagnostic_lines(diagnostic_payload) if diagnostic_payload else None,
            "Diagnostic not started yet.",
        )

    col3, col4 = st.columns(2)
    with col3:
        render_panel(
            "Phase 1",
            build_phase1_lines(phase1_payload) if phase1_payload else None,
            "Phase 1 not started yet.",
        )
    with col4:
        render_panel(
            "Phase 2",
            build_phase2_lines(phase2_payload) if phase2_payload else None,
            "Phase 2 not started yet.",
        )


def render_logs_block() -> None:
    logs = st.session_state.get("logs", [])

    st.subheader("Logs")
    st.text_area(
        "Execution log",
        value="\n".join(logs),
        height=220,
        key="main_logs_text_area",
        label_visibility="collapsed",
    )


def render_stored_summaries() -> None:
    session = get_app_session()
    if session is None:
        return

    with st.expander("Stored summaries", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Phase 0**")
            p0 = session.phase0_summary
            st.write(f"Enriched: {p0.total_enriched}")
            st.write(f"Unresolved: {p0.total_unresolved}")
            st.write(f"Errors: {p0.total_errors}")

        with col2:
            st.markdown("**Phase 1**")
            p1 = session.phase1_summary
            st.write(f"Considered: {p1.total_records_considered}")
            st.write(f"Downloaded now: {p1.total_downloaded_now}")
            st.write(f"Failed: {p1.total_failed}")

        with col3:
            st.markdown("**Phase 2**")
            p2 = session.phase2_summary
            st.write(f"Retry candidates: {p2.total_retry_candidates}")
            st.write(f"Recovered now: {p2.total_recovered_now}")
            st.write(f"Failed: {p2.total_failed}")


def render_generated_outputs() -> None:
    session = get_app_session()
    if session is None:
        return

    with st.expander("Generated outputs", expanded=False):
        if session.final_workbook_path:
            st.write(f"**Final workbook:** `{session.final_workbook_path}`")
        else:
            st.write("**Final workbook:** -")

        if session.temp_workbook_path:
            st.write(f"**Last checkpoint:** `{session.temp_workbook_path}`")
        else:
            st.write("**Last checkpoint:** -")

        if session.generated_report_paths:
            st.write("**Reports:**")
            for report_path in session.generated_report_paths[-10:]:
                st.write(f"- `{report_path}`")
        else:
            st.write("**Reports:** -")

        if session.diagnostics_history:
            st.write("**Diagnostics history:**")
            for item in session.diagnostics_history[-10:]:
                st.write(
                    f"- {item.diagnostic_label}: diagnosed={item.total_rows_diagnosed}, "
                    f"downloaded={item.total_downloaded}, errors={item.total_errors}"
                )
        else:
            st.write("**Diagnostics history:** -")


def render_final_summary() -> None:
    final_summary = st.session_state.get("final_summary")
    if not final_summary:
        return

    st.subheader("Final summary")
    phase1 = final_summary.get("phase1", {})
    phase2 = final_summary.get("phase2", {})

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("P1 processed", phase1.get("processed", 0))
    with c2:
        st.metric("PDFs available", phase2.get("pdfs_available_global", 0))
    with c3:
        st.metric("Downloaded now", phase2.get("downloaded_now_total", 0))
    with c4:
        st.metric("Recovered in phase 2", phase2.get("recovered_this_phase", 0))

    st.write(f"**Output workbook:** `{final_summary.get('output_workbook_path', '')}`")


def render_status_panels() -> None:
    ensure_streamlit_state()
    render_session_summary()
    st.divider()
    render_phase_snapshots()
    st.divider()
    render_logs_block()
    render_final_summary()
    render_stored_summaries()
    render_generated_outputs()


def reset_run_state(clear_session: bool = False) -> None:
    """
    Reset UI execution state.
    """
    st.session_state["logs"] = []
    st.session_state["phase0_payload"] = None
    st.session_state["phase1_payload"] = None
    st.session_state["phase2_payload"] = None
    st.session_state["diagnostic_payload"] = None
    st.session_state["final_summary"] = None
    st.session_state["last_phase1_results_by_row"] = None
    st.session_state["last_phase1_summary"] = None
    st.session_state["last_phase2_summary"] = None
    st.session_state["last_phase0_summary"] = None
    st.session_state["last_diagnostic_summary"] = None
    st.session_state["save_events"] = []
    st.session_state["run_status"] = "idle"
    st.session_state["run_error"] = ""
    st.session_state["last_report_path"] = ""
    st.session_state["last_output_path"] = ""

    if clear_session:
        st.session_state["app_session"] = None


def render_path_download_button(path_value: Optional[Path | str], label: str, key: str) -> None:
    """
    Render one download button if the path exists.
    """
    if not path_value:
        return

    path = Path(path_value)
    if not path.exists() or not path.is_file():
        return

    mime = "application/octet-stream"
    if path.suffix.lower() == ".xlsx":
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    with open(path, "rb") as f:
        st.download_button(
            label=label,
            data=f.read(),
            file_name=path.name,
            mime=mime,
            key=key,
        )