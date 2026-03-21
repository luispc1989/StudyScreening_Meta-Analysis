# ui/streamlit_app.py
from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from app.config import MAX_ROWS_TO_PROCESS, PDF_BASE_DIR, SHEET_NAME, build_output_workbook_path, resolve_workbook_path
from app.excel_io import build_col_map, collect_records, load_workbook_and_sheet, safe_save_workbook, validate_required_columns
from app.pipeline import run_full_pipeline
from ui.components import ensure_streamlit_state, make_streamlit_reporter, render_status_panels, reset_run_state, append_log


st.set_page_config(page_title="PDF Downloader Tool", layout="wide")


def save_uploaded_file_to_temp(uploaded_file) -> Path:
    """
    Save uploaded workbook to a temporary .xlsx file and return its path.
    """
    suffix = Path(uploaded_file.name).suffix or ".xlsx"
    temp_dir = Path(tempfile.gettempdir())
    temp_path = temp_dir / uploaded_file.name

    temp_path.write_bytes(uploaded_file.getbuffer())
    return temp_path


def main() -> None:
    ensure_streamlit_state()

    st.title("PDF Downloader Tool")
    st.write("Run the same pipeline through a Streamlit interface.")

    with st.sidebar:
        st.header("Input workbook")
        mode = st.radio(
            "Workbook source",
            ["Automatic workbook", "Upload workbook"],
            index=0,
        )

        uploaded_file = None
        if mode == "Upload workbook":
            uploaded_file = st.file_uploader(
                "Upload .xlsx workbook",
                type=["xlsx"],
            )

        st.header("Actions")
        run_clicked = st.button("Run pipeline", use_container_width=True)
        reset_clicked = st.button("Reset UI state", use_container_width=True)

    if reset_clicked:
        reset_run_state()
        st.rerun()

    workbook_path = None
    output_workbook_path = None

    if mode == "Automatic workbook":
        try:
            workbook_path = resolve_workbook_path()
            output_workbook_path = build_output_workbook_path(workbook_path)
            st.info(f"Using workbook: `{workbook_path}`")
        except Exception as exc:
            st.error(f"Could not resolve workbook automatically: {exc}")

    elif mode == "Upload workbook":
        if uploaded_file is not None:
            workbook_path = save_uploaded_file_to_temp(uploaded_file)
            output_workbook_path = workbook_path.with_name(f"{workbook_path.stem}_pdf_downloaded.xlsx")
            st.info(f"Using uploaded workbook: `{workbook_path}`")
        else:
            st.warning("Upload a workbook to continue.")

    if run_clicked:
        if workbook_path is None:
            st.error("No valid workbook is available.")
        else:
            reset_run_state()
            st.session_state["run_status"] = "running"

            PDF_BASE_DIR.mkdir(parents=True, exist_ok=True)

            try:
                append_log(f"Opening workbook: {workbook_path}")

                wb, ws = load_workbook_and_sheet(workbook_path, SHEET_NAME)
                col_map = build_col_map(ws)
                validate_required_columns(col_map, SHEET_NAME)

                records = collect_records(ws, col_map, MAX_ROWS_TO_PROCESS)
                if not records:
                    raise ValueError("No records found to process.")

                append_log(f"Records loaded: {len(records)}")

                reporter = make_streamlit_reporter()

                final_summary = run_full_pipeline(
                    wb=wb,
                    ws=ws,
                    col_map=col_map,
                    records=records,
                    output_workbook_path=output_workbook_path,
                    reporter=reporter,
                )

                st.session_state["final_summary"] = final_summary
                st.session_state["run_status"] = "finished"

                append_log("Run completed successfully.")

            except KeyboardInterrupt:
                st.session_state["run_status"] = "interrupted"
                append_log("Run interrupted by user.")

                try:
                    ok = safe_save_workbook(wb, output_workbook_path)
                    append_log(f"Emergency save completed: {ok}")
                except Exception as save_exc:
                    append_log(f"Emergency save failed: {save_exc}")

            except Exception as exc:
                st.session_state["run_status"] = "error"
                st.session_state["run_error"] = str(exc)
                append_log(f"Run failed: {exc}")

                try:
                    ok = safe_save_workbook(wb, output_workbook_path)
                    append_log(f"Partial save completed: {ok}")
                except Exception as save_exc:
                    append_log(f"Partial save failed: {save_exc}")

    status = st.session_state.get("run_status", "idle")
    if status == "running":
        st.warning("Pipeline is running.")
    elif status == "finished":
        st.success("Pipeline finished.")
    elif status == "error":
        st.error(f"Pipeline failed: {st.session_state.get('run_error', '')}")
    elif status == "interrupted":
        st.warning("Pipeline interrupted.")

    render_status_panels()

    final_summary = st.session_state.get("final_summary")
    if final_summary:
        output_path = Path(final_summary["output_workbook_path"])
        if output_path.exists():
            with open(output_path, "rb") as f:
                st.download_button(
                    label="Download output workbook",
                    data=f.read(),
                    file_name=output_path.name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )


if __name__ == "__main__":
    main()