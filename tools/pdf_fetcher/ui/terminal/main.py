from __future__ import annotations

import importlib
import queue
import sys
import threading
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pdf_fetcher.core.config import (
    ACTIVE_PROJECT_ROOT,
    PDF_BASE_DIR,
    SHEET_NAME,
    build_timestamp,
    ensure_project_directories,
    resolve_workbook_path,
)
from tools.pdf_fetcher.core.excel_io import (
    current_workbook_has_phase1_data,
    initialize_session_state,
    reconstruct_phase1_results_from_workbook,
    reload_session_from_current,
    save_current_workbook,
    save_final_workbook,
    save_session_checkpoint,
)
from tools.pdf_fetcher.core.pipeline import (
    run_diagnostic_for_session,
    run_phase0_doi_enrichment_for_session,
    run_phase1_for_session,
    run_phase2_for_session,
)
from tools.pdf_fetcher.ui.terminal.dashboard import TerminalDashboard


_input_queue: queue.Queue[str] = queue.Queue()


def _start_stdin_reader() -> None:
    def _reader() -> None:
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    _input_queue.put("")
                    break
                _input_queue.put(line.strip())
            except Exception:
                break

    thread = threading.Thread(target=_reader, daemon=True, name="stdin-reader")
    thread.start()


def _get_line(prompt: str = "") -> str:
    if prompt:
        sys.stdout.write(prompt)
        sys.stdout.flush()
    return _input_queue.get()


class UserRequestedQuit(Exception):
    pass


def _run_phase_with_controls(
    dashboard: TerminalDashboard,
    phase_fn,
    **phase_kwargs,
):
    stop_event = threading.Event()
    stop_reason: list[str | None] = [None]
    result_holder: list = [None, None]
    phase_done = threading.Event()
    valid_controls = {"p": "pause", "v": "back", "s": "quit"}

    def _phase_thread() -> None:
        try:
            result_holder[0] = phase_fn(stop_event=stop_event, **phase_kwargs)
        except Exception as exc:
            result_holder[1] = exc
        finally:
            phase_done.set()

    dashboard.show_controls_bar = True
    thread = threading.Thread(target=_phase_thread, daemon=True)
    thread.start()

    while not phase_done.is_set():
        try:
            line = _input_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        key = line.lower()
        if key in valid_controls:
            stop_reason[0] = valid_controls[key]
            stop_event.set()
            dashboard.show_message(
                "STOP REQUEST RECEIVED",
                [
                    "Your command was received.",
                    "Waiting for the current lookup step to finish safely...",
                ],
            )
            thread.join()
            break
    else:
        thread.join()

    dashboard.show_controls_bar = False

    if result_holder[1] is not None:
        raise result_holder[1]

    return result_holder[0], stop_reason[0]


def _quit_app_with_checkpoint(session_state, dashboard: TerminalDashboard) -> None:
    checkpoint_path = save_session_checkpoint(
        session_state=session_state,
        label="user_quit",
        timestamp=session_state.timestamp or None,
    )
    if checkpoint_path:
        dashboard.show_message(
            "CHECKPOINT",
            [
                "Checkpoint saved before exiting.",
                f"File                   : {checkpoint_path}",
            ],
        )
    raise UserRequestedQuit("User chose to exit the app.")


def _handle_pause_menu(session_state, dashboard: TerminalDashboard) -> str:
    choice = dashboard.show_pause_menu()

    if choice == "1":
        return "continue"

    if choice == "2":
        return "back"

    if choice == "3":
        _quit_app_with_checkpoint(session_state, dashboard)

    return "back"


def _handle_phase_stop_reason(
    session_state,
    dashboard: TerminalDashboard,
    stop_reason: str | None,
) -> str:
    if stop_reason is None:
        return "finished"

    if stop_reason == "pause":
        return _handle_pause_menu(session_state, dashboard)

    if stop_reason == "back":
        return "back"

    if stop_reason == "quit":
        _quit_app_with_checkpoint(session_state, dashboard)

    return "back"


def wait_for_enter(prompt: str = "Press Enter to continue...") -> None:
    _get_line(prompt)


def show_message_and_wait(
    dashboard: TerminalDashboard,
    title: str,
    lines: list[str],
) -> None:
    dashboard.show_message(title, lines)
    wait_for_enter()


def show_startup_notice(dashboard: TerminalDashboard) -> None:
    show_message_and_wait(
        dashboard,
        "STARTUP NOTICE",
        [
            "If you have access to an academic VPN or institutional network,",
            "connect to it before starting the tool for better PDF retrieval results.",
            "",
            "This can improve access to publisher platforms and bibliographic resources.",
        ],
    )


def _diagnostic_wrapper(
    session_state,
    diagnostic_label: str,
    reporter,
    stop_event=None,
):
    return run_diagnostic_for_session(
        session_state=session_state,
        diagnostic_label=diagnostic_label,
        reporter=reporter,
        stop_event=stop_event,
    )


def run_diagnostic_with_controls(
    session_state,
    dashboard: TerminalDashboard,
    diagnostic_label: str,
    title_after_finish: str,
) -> None:
    while True:
        dashboard.reset_dynamic_blocks()

        diagnostic_summary, stop_reason = _run_phase_with_controls(
            dashboard=dashboard,
            phase_fn=_diagnostic_wrapper,
            session_state=session_state,
            diagnostic_label=diagnostic_label,
            reporter=dashboard.handle_event,
        )

        decision = _handle_phase_stop_reason(session_state, dashboard, stop_reason)

        if decision == "continue":
            continue

        if decision == "back":
            return

        report_path = ""
        if isinstance(diagnostic_summary, dict):
            report_path = str(diagnostic_summary.get("report_path") or "")

        lines = [f"{diagnostic_label.capitalize()} completed."]
        if report_path:
            lines.append(f"Report saved            : {report_path}")

        show_message_and_wait(dashboard, title_after_finish, lines)
        return


def run_initial_diagnostic(session_state, dashboard: TerminalDashboard) -> None:
    run_diagnostic_with_controls(
        session_state=session_state,
        dashboard=dashboard,
        diagnostic_label="initial diagnostic",
        title_after_finish="INITIAL DIAGNOSTIC",
    )


def run_diagnostic_after_phase(
    session_state,
    dashboard: TerminalDashboard,
    diagnostic_label: str,
) -> None:
    run_diagnostic_with_controls(
        session_state=session_state,
        dashboard=dashboard,
        diagnostic_label=diagnostic_label,
        title_after_finish="DIAGNOSTIC",
    )


def generate_phase0_report_from_cache(session_state) -> str:
    module = importlib.import_module("tools.pdf_fetcher.core.doi_enrichment")
    generate_fn = getattr(module, "generate_phase0_report_from_cache", None)

    if not callable(generate_fn):
        raise RuntimeError(
            "tools.pdf_fetcher.core.doi_enrichment does not expose 'generate_phase0_report_from_cache'."
        )

    return str(generate_fn(session_state) or "")


def save_current_after_phase(session_state, dashboard: TerminalDashboard, phase_label: str) -> None:
    current_path = save_current_workbook(session_state)
    if current_path:
        reloaded_session = reload_session_from_current(session_state)
        session_state.workbook_path = reloaded_session.workbook_path
        session_state.workbook = reloaded_session.workbook
        session_state.worksheet = reloaded_session.worksheet
        session_state.col_map = reloaded_session.col_map
        session_state.records = reloaded_session.records
        session_state.current_workbook_path = reloaded_session.current_workbook_path
        dashboard.show_message(
            phase_label,
            [
                "Current workbook updated.",
                "Next phase will start from the current workbook.",
                f"File                   : {current_path}",
            ],
        )
        wait_for_enter()
    else:
        dashboard.show_message(
            phase_label,
            ["Could not update the current workbook."],
        )
        wait_for_enter()


def _phase0_wrapper(session_state, stop_event=None):
    return run_phase0_doi_enrichment_for_session(
        session_state=session_state,
        reporter=session_state._dashboard_reporter,
        generate_report=False,
        stop_event=stop_event,
    )


def run_phase0_menu_loop(session_state, dashboard: TerminalDashboard) -> str:
    phase0_result = None

    while True:
        if phase0_result is None:
            dashboard.reset_dynamic_blocks()
            session_state._dashboard_reporter = dashboard.handle_event

            phase0_result, stop_reason = _run_phase_with_controls(
                dashboard=dashboard,
                phase_fn=_phase0_wrapper,
                session_state=session_state,
            )

            decision = _handle_phase_stop_reason(session_state, dashboard, stop_reason)

            if decision == "continue":
                phase0_result = None
                continue

            if decision == "back":
                return "initial"

            save_current_after_phase(session_state, dashboard, "PHASE 0 - DOI ENRICHMENT")

        choice = dashboard.show_phase0_summary_menu()

        if choice == "1":
            phase0_result = None
            continue

        if choice == "2":
            report_path = generate_phase0_report_from_cache(session_state)
            lines = ["Phase 0 report completed."]
            if report_path:
                lines.append(f"Report saved            : {report_path}")
            show_message_and_wait(dashboard, "PHASE 0 - DOI ENRICHMENT", lines)
            continue

        if choice == "3":
            navigation = run_phase1_menu_loop(
                session_state=session_state,
                dashboard=dashboard,
                previous_menu="phase0",
            )
            if navigation == "phase0":
                continue
            if navigation == "initial":
                return "initial"
            continue

        if choice == "4":
            run_diagnostic_after_phase(
                session_state,
                dashboard,
                "phase 0 diagnostic",
            )
            continue

        if choice == "5":
            return "initial"

def run_phase1_menu_loop(
    session_state,
    dashboard: TerminalDashboard,
    previous_menu: str = "initial",
) -> str:
    phase1_results_by_row = None
    phase1_summary = None

    while True:
        if phase1_results_by_row is None or phase1_summary is None:
            dashboard.reset_dynamic_blocks()

            result, stop_reason = _run_phase_with_controls(
                dashboard=dashboard,
                phase_fn=run_phase1_for_session,
                session_state=session_state,
                reporter=dashboard.handle_event,
            )
            phase1_results_by_row, phase1_summary = result

            decision = _handle_phase_stop_reason(session_state, dashboard, stop_reason)

            if decision == "continue":
                phase1_results_by_row = None
                phase1_summary = None
                continue

            if decision == "back":
                return previous_menu

            save_current_after_phase(session_state, dashboard, "PHASE 1 - PDF BASIC DOWNLOAD")

        choice = dashboard.show_phase1_summary_menu()

        if choice == "1":
            phase1_results_by_row = None
            phase1_summary = None
            continue

        if choice == "2":
            navigation = run_phase2_menu_loop(
                session_state=session_state,
                dashboard=dashboard,
                phase1_results_by_row=phase1_results_by_row,
                phase1_summary=phase1_summary,
                previous_menu="phase1",
            )
            if navigation == "phase1":
                continue
            if navigation == "initial":
                return "initial"
            if navigation == "phase0":
                return "phase0"
            continue

        if choice == "3":
            run_diagnostic_after_phase(
                session_state,
                dashboard,
                "phase 1 diagnostic",
            )
            continue

        if choice == "4":
            return "phase0"

        if choice == "5":
            return "initial"

def run_phase2_menu_loop(
    session_state,
    dashboard: TerminalDashboard,
    phase1_results_by_row,
    phase1_summary,
    previous_menu: str = "phase1",
) -> str:
    phase2_summary = None

    while True:
        if phase2_summary is None:
            dashboard.reset_dynamic_blocks()

            phase2_summary, stop_reason = _run_phase_with_controls(
                dashboard=dashboard,
                phase_fn=run_phase2_for_session,
                session_state=session_state,
                phase1_results_by_row=phase1_results_by_row,
                phase1_summary=phase1_summary,
                reporter=dashboard.handle_event,
            )

            decision = _handle_phase_stop_reason(session_state, dashboard, stop_reason)

            if decision == "continue":
                phase2_summary = None
                continue

            if decision == "back":
                return previous_menu

            save_current_after_phase(session_state, dashboard, "PHASE 2 - PDF SPECIALIZED DOWNLOAD")

        choice = dashboard.show_phase2_summary_menu()

        if choice == "1":
            phase2_summary = None
            continue

        if choice == "2":
            final_path = save_final_workbook(
                session_state=session_state,
                timestamp=session_state.timestamp or None,
            )

            lines = []
            if final_path:
                lines.append(f"Final workbook saved    : {final_path}")
            else:
                lines.append("Could not save the final workbook.")

            phase2_data = phase2_summary or {}
            lines.append(
                f"PDFs available          : {phase2_data.get('pdfs_available_global', 0)}"
            )
            lines.append(
                f"PDFs downloaded now     : {phase2_data.get('downloaded_now_total', 0)}"
            )
            lines.append(f"PDF folder              : {PDF_BASE_DIR}")

            show_message_and_wait(
                dashboard,
                "PHASE 2 - PDF SPECIALIZED DOWNLOAD",
                lines,
            )
            continue

        if choice == "3":
            run_diagnostic_after_phase(
                session_state,
                dashboard,
                "phase 2 diagnostic",
            )
            continue

        if choice == "4":
            return "phase1"

        if choice == "5":
            return "initial"

        if choice == "6":
            stats_choice = dashboard.show_phase2_resolver_stats_menu()
            if stats_choice == "1":
                continue


def run_navigation_from(
    session_state,
    dashboard: TerminalDashboard,
    start_phase: str,
) -> None:
    current = start_phase

    while True:
        if current == "phase0":
            next_target = run_phase0_menu_loop(
                session_state=session_state,
                dashboard=dashboard,
            )
        elif current == "phase1":
            next_target = run_phase1_menu_loop(
                session_state=session_state,
                dashboard=dashboard,
                previous_menu="initial",
            )
        else:
            return

        if next_target == "initial":
            return

        if next_target == "phase0":
            current = "phase0"
            continue

        if next_target == "phase1":
            current = "phase1"
            continue

        return


def main() -> None:
    _start_stdin_reader()

    dashboard = TerminalDashboard(input_fn=_get_line)
    dashboard.init_terminal_mode()
    show_startup_notice(dashboard)

    ensure_project_directories()
    workbook_path = resolve_workbook_path()
    PDF_BASE_DIR.mkdir(parents=True, exist_ok=True)

    session_state = initialize_session_state(
        workbook_path=workbook_path,
        sheet_name=SHEET_NAME,
    )
    session_state.timestamp = build_timestamp()
    session_state._dashboard_reporter = dashboard.handle_event

    if not session_state.records:
        raise ValueError("No records found to process.")

    try:
        while True:
            allow_phase2_start = current_workbook_has_phase1_data(session_state.sheet_name or SHEET_NAME)
            choice = dashboard.show_initial_menu(allow_phase2_start=allow_phase2_start)

            if choice == "1":
                run_navigation_from(
                    session_state=session_state,
                    dashboard=dashboard,
                    start_phase="phase0",
                )
                continue

            if choice == "2":
                run_navigation_from(
                    session_state=session_state,
                    dashboard=dashboard,
                    start_phase="phase1",
                )
                continue

            if allow_phase2_start and choice == "3":
                reloaded_session = reload_session_from_current(session_state)
                session_state.workbook_path = reloaded_session.workbook_path
                session_state.workbook = reloaded_session.workbook
                session_state.worksheet = reloaded_session.worksheet
                session_state.col_map = reloaded_session.col_map
                session_state.records = reloaded_session.records
                session_state.current_workbook_path = reloaded_session.current_workbook_path

                phase1_results_by_row, phase1_summary = reconstruct_phase1_results_from_workbook(session_state)
                run_phase2_menu_loop(
                    session_state=session_state,
                    dashboard=dashboard,
                    phase1_results_by_row=phase1_results_by_row,
                    phase1_summary=phase1_summary,
                    previous_menu="initial",
                )
                continue

            if (allow_phase2_start and choice == "4") or (not allow_phase2_start and choice == "3"):
                run_initial_diagnostic(
                    session_state=session_state,
                    dashboard=dashboard,
                )
                continue

            if (allow_phase2_start and choice == "5") or (not allow_phase2_start and choice == "4"):
                raise SystemExit(0)

    except UserRequestedQuit:
        raise SystemExit(0)

    except KeyboardInterrupt:
        dashboard.show_message(
            "INTERRUPTION",
            [
                "Interruption requested by the user.",
                "Saving temporary checkpoint...",
            ],
        )

        checkpoint_path = save_session_checkpoint(
            session_state=session_state,
            label="interrupted",
            timestamp=session_state.timestamp or None,
        )

        if checkpoint_path:
            dashboard.show_message(
                "CHECKPOINT",
                [
                    "Checkpoint saved successfully.",
                    f"File                   : {checkpoint_path}",
                ],
            )
        else:
            dashboard.show_message(
                "CHECKPOINT",
                ["Could not save the checkpoint."],
            )

    except Exception as exc:
        checkpoint_path = save_session_checkpoint(
            session_state=session_state,
            label="error",
            timestamp=session_state.timestamp or None,
        )

        lines = [f"Error: {exc}"]
        lines.append(f"Active project          : {ACTIVE_PROJECT_ROOT}")
        if checkpoint_path:
            lines.append(f"Checkpoint saved        : {checkpoint_path}")
        else:
            lines.append("Could not save the checkpoint after the error.")

        dashboard.show_message("ERROR", lines)
        raise


if __name__ == "__main__":
    main()
