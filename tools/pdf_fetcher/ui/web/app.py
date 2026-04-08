from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

TOOL_ROOT = Path(__file__).resolve().parents[2]

ASSETS_DIR = TOOL_ROOT / "assets"


def find_first_existing_asset(candidates: list[str]) -> Path | None:
    for name in candidates:
        path = ASSETS_DIR / name
        if path.exists():
            return path

    if ASSETS_DIR.exists():
        for path in ASSETS_DIR.iterdir():
            if path.is_file() and path.suffix.lower() == ".png":
                return path

    return None


def find_first_existing_ico(candidates: list[str]) -> Path | None:
    for name in candidates:
        path = ASSETS_DIR / name
        if path.exists():
            return path

    if ASSETS_DIR.exists():
        for path in ASSETS_DIR.iterdir():
            if path.is_file() and path.suffix.lower() == ".ico":
                return path

    return None


LOGO_PATH = find_first_existing_asset(
    [
        "pdf_fetcher_logo.png",
        "PDF Fetcher logo.png",
        "PDF_Fetcher_logo.png",
        "PDF Fetcher Download.png",
    ]
)

FAVICON_PATH = find_first_existing_ico(
    [
        "pdf_fetcher_favicon.ico",
        "PDF_Fetcher_logo_ico.ico",
        "PDF_Fetcher_from_uploaded.ico",
        "PDF Fetcher logo.ico",
    ]
)

import streamlit as st

page_icon_value = str(FAVICON_PATH) if FAVICON_PATH is not None else "📄"

st.set_page_config(
    page_title="PDF FETCHER - Study Screening Toolkit",
    page_icon=page_icon_value,
    layout="wide",
)

from tools.pdf_fetcher.core.config import (
    ACTIVE_PROJECT_ROOT,
    DEFAULT_PROJECT_NAME,
    ENABLE_DIAGNOSTICS,
    ENABLE_DOI_ENRICHMENT,
    INPUT_EXCEL_DIR,
    SHEET_NAME,
    TOOL_ROOT_DIR,
    build_current_workbook_path,
    build_input_workbook_path,
    resolve_workbook_path,
)
from tools.pdf_fetcher.core.excel_io import (
    initialize_session_state,
    save_final_workbook,
    save_session_checkpoint,
)
from tools.pdf_fetcher.core.pipeline import (
    run_diagnostic_for_session,
    run_full_pipeline_for_session,
    run_phase0_doi_enrichment_for_session,
    run_phase1_for_session,
    run_phase2_for_session,
)
from tools.pdf_fetcher.ui.web.components import (
    append_log,
    clear_live_placeholders,
    ensure_streamlit_state,
    get_app_session,
    make_streamlit_reporter,
    render_path_download_button,
    render_status_panels,
    reset_run_state,
    set_app_session,
)


def inject_custom_css() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.1rem;
            padding-bottom: 2rem;
        }

        .pf-header-wrap {
            margin-bottom: 1.2rem;
            padding: 1rem 1.1rem 1rem 1.1rem;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            background:
                linear-gradient(135deg, rgba(255,75,75,0.08), rgba(255,255,255,0.02));
        }

        .pf-title {
            margin: 0;
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.05;
        }

        .pf-subtitle {
            margin: 0.25rem 0 0 0;
            color: #9aa4b2;
            font-size: 0.98rem;
        }

        .pf-badge {
            display: inline-block;
            margin-top: 0.7rem;
            padding: 0.34rem 0.72rem;
            border-radius: 999px;
            background: rgba(255, 75, 75, 0.12);
            border: 1px solid rgba(255, 75, 75, 0.30);
            color: #ff5c5c;
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.02em;
        }

        .pf-small-note {
            color: #8d98a5;
            font-size: 0.9rem;
            margin-top: 0.7rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_app_header() -> None:
    col_logo, col_text = st.columns([1.15, 4.85], vertical_alignment="center")

    with col_logo:
        if LOGO_PATH is not None and LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=240)

    with col_text:
        header_html = """
<div class="pf-header-wrap">
    <h1 class="pf-title">PDF Fetcher</h1>
    <p class="pf-subtitle">A module of the Study Screening Toolkit</p>
    <div class="pf-badge">DOI enrichment • PDF download • Download Diagnostics</div>
    <div class="pf-small-note">
        Built to support DOI resolution, PDF acquisition, and diagnostic reporting.
    </div>
</div>
""".strip()

        st.markdown(header_html, unsafe_allow_html=True)


def save_uploaded_file_to_project(uploaded_file) -> Path:
    """
    Save the uploaded workbook into the active project input folder and return its path.
    """
    source_name = uploaded_file.name or "input_workbook.xlsx"
    input_path = build_input_workbook_path(source_name)

    input_path.write_bytes(uploaded_file.getbuffer())
    return input_path


def create_live_placeholders() -> dict:
    """
    Create a single root placeholder for the temporary live monitor.
    """
    return {"root": st.empty()}


def initialize_session_from_path(workbook_path: Path) -> None:
    """
    Initialize project SessionState from a workbook path.
    """
    reset_run_state(clear_session=False)

    session = initialize_session_state(
        workbook_path=workbook_path,
        sheet_name=SHEET_NAME,
    )
    set_app_session(session)

    append_log(f"Workbook session initialized: {workbook_path}")
    append_log(f"Records loaded: {len(session.records)}")


def require_loaded_session() -> bool:
    """
    Return True if a valid workbook session is available.
    """
    session = get_app_session()
    if session is None or not session.is_workbook_loaded:
        st.error("No workbook session is loaded.")
        return False
    return True


def run_action_with_handling(action_name: str, action_callable) -> None:
    """
    Run one action with common error handling and a temporary live monitor.
    """
    if not require_loaded_session():
        return

    st.session_state["run_status"] = "running"
    st.session_state["run_error"] = ""

    placeholders = create_live_placeholders()
    reporter = make_streamlit_reporter(placeholders)

    try:
        append_log(f"Starting action: {action_name}")
        action_callable(reporter)
        st.session_state["run_status"] = "finished"
        append_log(f"Action completed: {action_name}")

    except KeyboardInterrupt:
        st.session_state["run_status"] = "interrupted"
        append_log(f"Action interrupted: {action_name}")

    except Exception as exc:
        st.session_state["run_status"] = "error"
        st.session_state["run_error"] = str(exc)
        append_log(f"Action failed: {action_name} | {exc}")

    finally:
        clear_live_placeholders(placeholders)


def run_phase0(generate_report: bool) -> None:
    session = get_app_session()
    if session is None:
        st.error("No workbook session is loaded.")
        return

    def _runner(reporter):
        summary = run_phase0_doi_enrichment_for_session(
            session_state=session,
            reporter=reporter,
            generate_report=generate_report,
        )
        st.session_state["last_phase0_summary"] = summary

    run_action_with_handling("phase0", _runner)


def run_phase1() -> None:
    session = get_app_session()
    if session is None:
        st.error("No workbook session is loaded.")
        return

    def _runner(reporter):
        phase1_results_by_row, phase1_summary = run_phase1_for_session(
            session_state=session,
            reporter=reporter,
        )
        st.session_state["last_phase1_results_by_row"] = phase1_results_by_row
        st.session_state["last_phase1_summary"] = phase1_summary

    run_action_with_handling("phase1", _runner)


def run_phase2() -> None:
    session = get_app_session()
    if session is None:
        st.error("No workbook session is loaded.")
        return

    phase1_results_by_row = st.session_state.get("last_phase1_results_by_row")
    phase1_summary = st.session_state.get("last_phase1_summary")

    if not phase1_results_by_row or not phase1_summary:
        st.error("Phase 2 requires Phase 1 results from the current session.")
        return

    def _runner(reporter):
        phase2_summary = run_phase2_for_session(
            session_state=session,
            phase1_results_by_row=phase1_results_by_row,
            phase1_summary=phase1_summary,
            reporter=reporter,
        )
        st.session_state["last_phase2_summary"] = phase2_summary

    run_action_with_handling("phase2", _runner)


def run_pipeline_full() -> None:
    session = get_app_session()
    if session is None:
        st.error("No workbook session is loaded.")
        return

    def _runner(reporter):
        final_summary = run_full_pipeline_for_session(
            session_state=session,
            reporter=reporter,
            save_final=True,
        )
        st.session_state["final_summary"] = final_summary
        st.session_state["last_output_path"] = final_summary.get("output_workbook_path", "")

    run_action_with_handling("full_pipeline", _runner)


def run_diagnostic(diagnostic_label: str) -> None:
    session = get_app_session()
    if session is None:
        st.error("No workbook session is loaded.")
        return

    def _runner(reporter):
        summary = run_diagnostic_for_session(
            session_state=session,
            diagnostic_label=diagnostic_label,
            reporter=reporter,
        )
        st.session_state["last_diagnostic_summary"] = summary
        st.session_state["last_report_path"] = summary.get("report_path", "")

    run_action_with_handling(f"diagnostic:{diagnostic_label}", _runner)


def save_checkpoint_now() -> None:
    if not require_loaded_session():
        return

    session = get_app_session()
    assert session is not None

    try:
        checkpoint_path = save_session_checkpoint(
            session_state=session,
            label="manual_checkpoint",
            timestamp=session.timestamp or None,
        )
        if checkpoint_path is None:
            st.error("Could not save checkpoint.")
            append_log("Manual checkpoint failed.")
        else:
            append_log(f"Manual checkpoint saved: {checkpoint_path}")
    except Exception as exc:
        st.error(f"Checkpoint failed: {exc}")
        append_log(f"Manual checkpoint failed: {exc}")


def save_final_now() -> None:
    if not require_loaded_session():
        return

    session = get_app_session()
    assert session is not None

    try:
        final_path = save_final_workbook(
            session_state=session,
            timestamp=session.timestamp or None,
        )
        if final_path is None:
            st.error("Could not save final workbook.")
            append_log("Manual final save failed.")
        else:
            st.session_state["last_output_path"] = str(final_path)
            append_log(f"Manual final workbook saved: {final_path}")
    except Exception as exc:
        st.error(f"Final save failed: {exc}")
        append_log(f"Manual final save failed: {exc}")


def render_top_status() -> None:
    status = st.session_state.get("run_status", "idle")

    if status == "running":
        st.warning("Action in progress.")
    elif status == "error":
        st.error(f"Last action failed: {st.session_state.get('run_error', '')}")
    elif status == "interrupted":
        st.warning("Last action was interrupted.")


def main() -> None:
    ensure_streamlit_state()
    inject_custom_css()
    render_app_header()

    with st.sidebar:
        st.header("Workbook source")
        st.caption(f"Project: `{DEFAULT_PROJECT_NAME}`")
        st.caption(f"Project folder: `{ACTIVE_PROJECT_ROOT}`")
        st.caption(f"Tool folder: `{TOOL_ROOT_DIR}`")

        mode = st.radio(
            "Source",
            ["Use project workbook", "Upload workbook into project"],
            index=0,
        )

        uploaded_file = None
        workbook_path: Path | None = None

        if mode == "Use project workbook":
            try:
                workbook_path = resolve_workbook_path()
                st.info(f"Resolved workbook: `{workbook_path}`")
            except Exception as exc:
                st.error(f"Could not resolve workbook from project folders: {exc}")
                st.caption(f"Input folder: `{INPUT_EXCEL_DIR}`")

        else:
            uploaded_file = st.file_uploader("Upload .xlsx workbook", type=["xlsx"])
            if uploaded_file is not None:
                workbook_path = save_uploaded_file_to_project(uploaded_file)
                st.info(f"Uploaded workbook saved to project: `{workbook_path}`")

        st.header("Session")
        load_clicked = st.button("Load workbook session", use_container_width=True)
        reset_ui_clicked = st.button("Reset UI state", use_container_width=True)
        reset_all_clicked = st.button("Reset UI + session", use_container_width=True)

        st.header("Phase actions")
        phase0_report = st.checkbox("Generate Phase 0 report", value=False)
        phase0_clicked = st.button(
            "Run Phase 0",
            use_container_width=True,
            disabled=not ENABLE_DOI_ENRICHMENT,
        )
        phase1_clicked = st.button("Run Phase 1", use_container_width=True)
        phase2_clicked = st.button("Run Phase 2", use_container_width=True)
        pipeline_clicked = st.button("Run Full Pipeline", use_container_width=True)

        st.header("Diagnostics")
        diagnostic_label = st.selectbox(
            "Diagnostic label",
            [
                "diagnóstico inicial",
                "diagnóstico fase 0",
                "diagnóstico fase 1",
                "diagnóstico fase 2",
            ],
            index=0,
            disabled=not ENABLE_DIAGNOSTICS,
        )
        diagnostic_clicked = st.button(
            "Run Diagnostic",
            use_container_width=True,
            disabled=not ENABLE_DIAGNOSTICS,
        )

        st.header("Manual saves")
        checkpoint_clicked = st.button("Save checkpoint", use_container_width=True)
        final_save_clicked = st.button("Save final workbook", use_container_width=True)

    if reset_ui_clicked:
        reset_run_state(clear_session=False)
        st.rerun()

    if reset_all_clicked:
        reset_run_state(clear_session=True)
        st.rerun()

    if load_clicked:
        if workbook_path is None:
            st.error("No valid workbook is available.")
        else:
            try:
                initialize_session_from_path(workbook_path)
                append_log("Workbook session loaded.")
            except Exception as exc:
                st.error(f"Could not initialize workbook session: {exc}")
                append_log(f"Session initialization failed: {exc}")

    if phase0_clicked:
        run_phase0(generate_report=phase0_report)

    if phase1_clicked:
        run_phase1()

    if phase2_clicked:
        run_phase2()

    if pipeline_clicked:
        run_pipeline_full()

    if diagnostic_clicked:
        run_diagnostic(diagnostic_label)

    if checkpoint_clicked:
        save_checkpoint_now()

    if final_save_clicked:
        save_final_now()

    render_top_status()
    render_status_panels()

    session = get_app_session()
    st.subheader("Downloads")

    if session is not None:
        render_path_download_button(
            session.final_workbook_path,
            "Download final workbook",
            key="download_final_workbook",
        )
        render_path_download_button(
            session.temp_workbook_path,
            "Download last checkpoint",
            key="download_checkpoint",
        )

        if session.generated_report_paths:
            for idx, report_path in enumerate(session.generated_report_paths[-10:], start=1):
                render_path_download_button(
                    report_path,
                    f"Download report {idx}",
                    key=f"download_report_{idx}",
                )

    last_report_path = st.session_state.get("last_report_path", "")
    if last_report_path:
        render_path_download_button(
            last_report_path,
            "Download latest report",
            key="download_latest_report",
        )

    last_output_path = st.session_state.get("last_output_path", "")
    if last_output_path:
        render_path_download_button(
            last_output_path,
            "Download latest output workbook",
            key="download_latest_output",
        )


if __name__ == "__main__":
    main()
