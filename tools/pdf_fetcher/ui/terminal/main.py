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
    ENABLE_SCI_HUB_RESOLVER,
    PDF_BASE_DIR,
    SHEET_NAME,
    build_timestamp,
    build_current_workbook_path_for_phase,
    ensure_project_directories,
    latest_phase_current_workbook_path,
    normalize_phase_name,
    resolve_workbook_path,
    resolve_workbook_path_for_stage,
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
    build_retry_tasks,
    run_diagnostic_for_session,
    run_phase0_doi_enrichment_for_session,
    run_phase1_for_session,
    run_phase2_for_session,
)
from tools.pdf_fetcher.core.resolver_detector import should_retry_in_phase2
from tools.pdf_fetcher.scout.launcher import export_scout_cases_report, launch_scout_with_report
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
            dashboard.suppress_live_updates = True
            dashboard.show_message(
                "STOP REQUEST RECEIVED",
                [
                    "Your command was received.",
                    "Waiting for the current lookup step to finish safely...",
                ],
            )
            while not phase_done.wait(timeout=0.1):
                pass
            break
    else:
        while not phase_done.wait(timeout=0.1):
            pass

    dashboard.show_controls_bar = False
    dashboard.suppress_live_updates = False

    if result_holder[1] is not None:
        raise result_holder[1]

    return result_holder[0], stop_reason[0]


def _quit_app_with_checkpoint(session_state, dashboard: TerminalDashboard) -> None:
    checkpoint_path = save_session_checkpoint(
        session_state=session_state,
        label="user_quit",
        timestamp=session_state.timestamp or None,
        fast=True,
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


def choose_startup_session_mode(dashboard: TerminalDashboard) -> str:
    has_saved_phase_workbooks = latest_phase_current_workbook_path() is not None
    choice = dashboard.show_startup_session_mode_menu(has_saved_phase_workbooks)
    return "new" if choice == "1" else "continue"


def _apply_session_reload(session_state, reloaded_session) -> None:
    session_state.workbook_path = reloaded_session.workbook_path
    session_state.project_root = reloaded_session.project_root
    session_state.tool_root = reloaded_session.tool_root
    session_state.workbook = reloaded_session.workbook
    session_state.worksheet = reloaded_session.worksheet
    session_state.col_map = reloaded_session.col_map
    session_state.records = reloaded_session.records
    session_state.retry_tasks = reloaded_session.retry_tasks
    session_state.current_phase = reloaded_session.current_phase
    session_state.phase0_summary = reloaded_session.phase0_summary
    session_state.phase1_summary = reloaded_session.phase1_summary
    session_state.phase2_summary = reloaded_session.phase2_summary
    session_state.diagnostics_history = reloaded_session.diagnostics_history
    session_state.generated_report_paths = reloaded_session.generated_report_paths
    session_state.final_workbook_path = reloaded_session.final_workbook_path
    session_state.temp_workbook_path = reloaded_session.temp_workbook_path
    session_state.current_workbook_path = reloaded_session.current_workbook_path
    session_state.history_workbook_path = reloaded_session.history_workbook_path
    session_state.timestamp = reloaded_session.timestamp
    session_state._dashboard_reporter = getattr(reloaded_session, "_dashboard_reporter", None)


def _reload_session_from_stage(session_state, stage: str) -> None:
    workbook_path = _resolve_stage_workbook_path(stage, getattr(session_state, "startup_session_mode", "new"))
    reloaded = initialize_session_state(
        workbook_path=workbook_path,
        sheet_name=session_state.sheet_name or SHEET_NAME,
    )
    reloaded.timestamp = session_state.timestamp
    reloaded._dashboard_reporter = getattr(session_state, "_dashboard_reporter", None)
    _apply_session_reload(session_state, reloaded)


def _resolve_stage_workbook_path(stage: str, startup_session_mode: str) -> Path:
    normalized = normalize_phase_name(stage)
    raw_stage = str(stage or "").strip().lower()
    continue_previous = startup_session_mode == "continue"

    if raw_stage == "scout":
        return resolve_workbook_path_for_stage("scout")

    if continue_previous and normalized in {"phase0", "phase1", "phase2"}:
        existing_path = build_current_workbook_path_for_phase(normalized)
        if existing_path.exists():
            return existing_path

    return resolve_workbook_path_for_stage(stage)


def launch_scout_from_terminal(session_state, dashboard: TerminalDashboard, mode: str) -> None:
    label = "pending downloads" if mode == "pending_downloads" else "load fail test cases"

    try:
        report_path = export_scout_cases_report(
            session_state=session_state,
            mode=mode,
            timestamp=None,
        )
        scout_url = launch_scout_with_report(report_path)
        show_message_and_wait(
            dashboard,
            "S.C.O.U.T.",
            [
                f"S.C.O.U.T. launched for {label}.",
                f"Case report             : {report_path}",
                f"Browser URL             : {scout_url}",
            ],
        )
    except Exception as exc:
        show_message_and_wait(
            dashboard,
            "S.C.O.U.T.",
            [
                f"Could not launch S.C.O.U.T.: {exc}",
            ],
        )


def run_scout_menu_loop(session_state, dashboard: TerminalDashboard) -> None:
    while True:
        choice = dashboard.show_scout_menu()

        if choice == "1":
            launch_scout_from_terminal(
                session_state=session_state,
                dashboard=dashboard,
                mode="pending_downloads",
            )
            continue

        if choice == "2":
            return


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
    dashboard.show_message(
        phase_label,
        [
            "Updating current workbook...",
            "Saving the latest phase state before returning to the menu.",
        ],
    )
    current_path = save_current_workbook(session_state)
    if current_path:
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


def sync_current_before_transition(
    session_state,
    dashboard: TerminalDashboard,
    transition_label: str,
) -> bool:
    dashboard.show_message(
        transition_label,
        [
            "Preparing next phase...",
            "Saving the current workbook before opening the next phase menu.",
        ],
    )
    current_path = save_current_workbook(session_state)
    if not current_path:
        show_message_and_wait(
            dashboard,
            transition_label,
            ["Could not update the current workbook before transition."],
        )
        return False

    return True


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
            if not sync_current_before_transition(
                session_state=session_state,
                dashboard=dashboard,
                transition_label="PHASE 0 -> PHASE 1",
            ):
                continue
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
            if not sync_current_before_transition(
                session_state=session_state,
                dashboard=dashboard,
                transition_label="PHASE 1 -> PHASE 2",
            ):
                continue
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
    phase2_mode: str | None = None
    selected_resolver: str | None = None

    while True:
        if phase2_mode is None:
            resolver_counts = _build_phase2_resolver_counts(
                session_state,
                phase1_results_by_row,
            )
            choice = dashboard.show_phase2_run_mode_menu(resolver_counts)

            if choice == "1":
                phase2_mode = "automatic"
                selected_resolver = None
            elif choice == "2":
                if not resolver_counts:
                    show_message_and_wait(
                        dashboard,
                        "PHASE 2 - CHOOSE RESOLVER",
                        ["No resolver candidates are available right now."],
                    )
                    continue

                resolver_names = list(resolver_counts)
                resolver_choice = dashboard.show_phase2_resolver_choice_menu(resolver_counts)
                back_choice = str(len(resolver_names) + 1)
                if resolver_choice == back_choice:
                    continue

                selected_resolver = resolver_names[int(resolver_choice) - 1]
                phase2_mode = "manual"
            else:
                return previous_menu

        if phase2_summary is None:
            dashboard.reset_dynamic_blocks()
            phase2_pass_summaries: list[dict] = []
            running_phase1_summary = dict(phase1_summary)

            def _combine_phase2_summaries(summaries: list[dict]) -> dict:
                if not summaries:
                    return {}
                first = summaries[0]
                last = summaries[-1]

                def _sum_counter(key: str) -> dict:
                    combined: dict[str, int] = {}
                    for summary in summaries:
                        for name, value in (summary.get(key, {}) or {}).items():
                            combined[name] = combined.get(name, 0) + int(value)
                    return combined

                return {
                    "phase2_pool_total": sum(int(s.get("phase2_pool_total", 0)) for s in summaries),
                    "retry_processed": sum(int(s.get("retry_processed", 0)) for s in summaries),
                    "retry_total": sum(int(s.get("retry_total", 0)) for s in summaries),
                    "unassigned_total": sum(int(s.get("unassigned_total", 0)) for s in summaries),
                    "phase2_start_time": first.get("phase2_start_time"),
                    "resolver_name": last.get("resolver_name", ""),
                    "last_record_id": last.get("last_record_id", ""),
                    "last_doi": last.get("last_doi", ""),
                    "last_status": last.get("last_status", ""),
                    "last_detail": last.get("last_detail", ""),
                    "pdfs_available_global": last.get("pdfs_available_global", 0),
                    "pdfs_in_folder": last.get("pdfs_in_folder", 0),
                    "downloaded_now_total": last.get("downloaded_now_total", 0),
                    "recovered_this_phase": sum(int(s.get("recovered_this_phase", 0)) for s in summaries),
                    "total_records": last.get("total_records", 0),
                    "stopped_early": any(bool(s.get("stopped_early", False)) for s in summaries),
                    "resolver_attempts": _sum_counter("resolver_attempts"),
                    "resolver_recovered": _sum_counter("resolver_recovered"),
                    "resolver_duplicates": _sum_counter("resolver_duplicates"),
                    "resolver_failed": _sum_counter("resolver_failed"),
                    "resolver_totals": _sum_counter("resolver_totals"),
                    "resolver_processed": _sum_counter("resolver_processed"),
                }

            if phase2_mode == "automatic":
                phase2_pass_plan = [
                    ("specialized", None, 0.0),
                    ("sci_hub_pass_1", "sci_hub", 0.0),
                    ("sci_hub_pass_2", "sci_hub_retry", 5.0),
                ]
            else:
                phase2_pass_plan = [("manual", selected_resolver, 0.0)]

            restart_run = False
            for _pass_name, _selected_resolver, _delay_seconds in phase2_pass_plan:
                sub_summary, stop_reason = _run_phase_with_controls(
                    dashboard=dashboard,
                    phase_fn=run_phase2_for_session,
                    session_state=session_state,
                    phase1_results_by_row=phase1_results_by_row,
                    phase1_summary=running_phase1_summary,
                    reporter=dashboard.handle_event,
                    selected_resolver=_selected_resolver,
                    inter_task_delay_seconds=_delay_seconds,
                )

                if sub_summary:
                    phase2_pass_summaries.append(sub_summary)
                    running_phase1_summary = {
                        **running_phase1_summary,
                        "pdfs_available_global": sub_summary.get("pdfs_available_global", running_phase1_summary.get("pdfs_available_global", 0)),
                        "downloaded_now_total": sub_summary.get("downloaded_now_total", running_phase1_summary.get("downloaded_now_total", 0)),
                    }

                decision = _handle_phase_stop_reason(session_state, dashboard, stop_reason)

                if decision == "continue":
                    phase2_summary = None
                    restart_run = True
                    break

                if decision == "back":
                    return previous_menu

            if restart_run:
                continue

            phase2_summary = _combine_phase2_summaries(phase2_pass_summaries)
            save_current_after_phase(session_state, dashboard, "PHASE 2 - PDF SPECIALIZED DOWNLOAD")

        if phase2_mode == "manual" and selected_resolver:
            choice = dashboard.show_phase2_manual_summary_menu(selected_resolver)
        else:
            choice = dashboard.show_phase2_summary_menu()

        if choice == "1":
            phase2_summary = None
            continue

        if phase2_mode == "manual" and choice == "2":
            phase2_summary = None
            phase2_mode = None
            selected_resolver = None
            continue

        if (phase2_mode == "manual" and choice == "3") or (phase2_mode != "manual" and choice == "2"):
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

        if (phase2_mode == "manual" and choice == "4") or (phase2_mode != "manual" and choice == "3"):
            run_diagnostic_after_phase(
                session_state,
                dashboard,
                "phase 2 diagnostic",
            )
            continue

        if (phase2_mode == "manual" and choice == "5") or (phase2_mode != "manual" and choice == "4"):
            return "phase1"

        if (phase2_mode == "manual" and choice == "6") or (phase2_mode != "manual" and choice == "5"):
            return "initial"

        if (phase2_mode == "manual" and choice == "7") or (phase2_mode != "manual" and choice == "6"):
            stats_choice = dashboard.show_phase2_resolver_stats_menu()
            if stats_choice == "1":
                continue


def _build_phase2_resolver_counts(session_state, phase1_results_by_row) -> dict[str, int]:
    retry_tasks = build_retry_tasks(session_state.records, phase1_results_by_row)
    counter: dict[str, int] = {}

    for task in retry_tasks:
        if task.resolver_names:
            resolver_name = task.resolver_names[0]
            counter[resolver_name] = counter.get(resolver_name, 0) + 1

    if ENABLE_SCI_HUB_RESOLVER:
        sci_hub_total = 0
        for result in phase1_results_by_row.values():
            if should_retry_in_phase2(result):
                sci_hub_total += 1
        if sci_hub_total > 0:
            counter["sci_hub"] = sci_hub_total

    return counter


def run_navigation_from(
    session_state,
    dashboard: TerminalDashboard,
    start_phase: str,
) -> None:
    _reload_session_from_stage(session_state, start_phase)
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
    startup_session_mode = choose_startup_session_mode(dashboard)

    ensure_project_directories()
    workbook_path = resolve_workbook_path() if startup_session_mode == "new" else _resolve_stage_workbook_path("phase0", startup_session_mode)
    PDF_BASE_DIR.mkdir(parents=True, exist_ok=True)

    dashboard.show_message(
        "LOADING SESSION",
        [
            f"Mode                   : {'Start new run' if startup_session_mode == 'new' else 'Continue previous run'}",
            f"Workbook               : {workbook_path}",
            "Loading workbook and building the session state...",
        ],
    )

    session_state = initialize_session_state(
        workbook_path=workbook_path,
        sheet_name=SHEET_NAME,
    )
    session_state.startup_session_mode = startup_session_mode
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
                try:
                    _reload_session_from_stage(session_state, "phase2")
                except Exception as exc:
                    show_message_and_wait(
                        dashboard,
                        "INITIAL -> PHASE 2",
                        [str(exc)],
                    )
                    continue

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
                try:
                    _reload_session_from_stage(session_state, "scout")
                except Exception as exc:
                    show_message_and_wait(
                        dashboard,
                        "PHASE 2 -> S.C.O.U.T.",
                        [str(exc)],
                    )
                    continue
                run_scout_menu_loop(
                    session_state=session_state,
                    dashboard=dashboard,
                )
                continue

            if (allow_phase2_start and choice == "6") or (not allow_phase2_start and choice == "5"):
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
