from __future__ import annotations

import importlib
import queue
import sys
import threading

from app.config import (
    PDF_BASE_DIR,
    SHEET_NAME,
    build_timestamp,
    resolve_workbook_path,
)
from app.excel_io import (
    initialize_session_state,
    save_final_workbook,
    save_session_checkpoint,
)
from app.pipeline import (
    run_diagnostic_for_session,
    run_phase0_doi_enrichment_for_session,
    run_phase1_for_session,
    run_phase2_for_session,
)
from ui.terminal_dashboard import TerminalDashboard


# ============================================================
# FILA CENTRAL DE STDIN
# ============================================================

_input_queue: queue.Queue[str] = queue.Queue()


def _start_stdin_reader() -> None:
    """Inicia a thread daemon de leitura de stdin. Chamar uma vez no main()."""

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

    t = threading.Thread(target=_reader, daemon=True, name="stdin-reader")
    t.start()


def _get_line(prompt: str = "") -> str:
    """Substituto de input() — lê da fila central."""
    if prompt:
        sys.stdout.write(prompt)
        sys.stdout.flush()
    return _input_queue.get()


# ============================================================
# EXCEÇÃO INTERNA PARA SAÍDA PELO UTILIZADOR
# ============================================================

class UserRequestedQuit(Exception):
    """Levantada quando o utilizador escolhe sair da app."""
    pass


# ============================================================
# EXECUÇÃO DE FASE / DIAGNÓSTICO COM CONTROLOS DE TECLADO
# ============================================================

def _run_phase_with_controls(
    dashboard: TerminalDashboard,
    phase_fn,
    **phase_kwargs,
):
    """
    Executa phase_fn numa thread de fundo.
    A thread principal monitoriza a fila de stdin por P / V / S.

    Devolve (result, stop_reason) onde stop_reason é:
    None | 'pause' | 'back' | 'quit'
    """
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
    t = threading.Thread(target=_phase_thread, daemon=True)
    t.start()

    while not phase_done.is_set():
        try:
            line = _input_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        key = line.lower()
        if key in valid_controls:
            stop_reason[0] = valid_controls[key]
            stop_event.set()
            t.join()
            break

    else:
        t.join()

    dashboard.show_controls_bar = False

    if result_holder[1] is not None:
        raise result_holder[1]

    return result_holder[0], stop_reason[0]


# ============================================================
# SAÍDA / PAUSA / NAVEGAÇÃO
# ============================================================

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
                "Checkpoint guardado antes de sair.",
                f"Ficheiro               : {checkpoint_path}",
            ],
        )
    raise UserRequestedQuit("Utilizador escolheu sair da app.")


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
    """
    Traduz o stop_reason para ação de navegação.
    """
    if stop_reason is None:
        return "finished"

    if stop_reason == "pause":
        return _handle_pause_menu(session_state, dashboard)

    if stop_reason == "back":
        return "back"

    if stop_reason == "quit":
        _quit_app_with_checkpoint(session_state, dashboard)

    return "back"


# ============================================================
# HELPERS GENÉRICOS
# ============================================================

def wait_for_enter(prompt: str = "Press Enter to continue...") -> None:
    _get_line(prompt)


def show_message_and_wait(
    dashboard: TerminalDashboard,
    title: str,
    lines: list[str],
) -> None:
    dashboard.show_message(title, lines)
    wait_for_enter()


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

        lines = [f"{diagnostic_label.capitalize()} concluído."]
        if report_path:
            lines.append(f"Report guardado         : {report_path}")

        show_message_and_wait(dashboard, title_after_finish, lines)
        return


def run_initial_diagnostic(session_state, dashboard: TerminalDashboard) -> None:
    run_diagnostic_with_controls(
        session_state=session_state,
        dashboard=dashboard,
        diagnostic_label="diagnóstico inicial",
        title_after_finish="DIAGNÓSTICO INICIAL",
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
        title_after_finish="DIAGNÓSTICO",
    )


def generate_phase0_report_from_cache(session_state) -> str:
    module = importlib.import_module("app.doi_enrichment")
    generate_fn = getattr(module, "generate_phase0_report_from_cache", None)

    if not callable(generate_fn):
        raise RuntimeError(
            "app.doi_enrichment does not expose 'generate_phase0_report_from_cache'."
        )

    return str(generate_fn(session_state) or "")


# ============================================================
# WRAPPER FASE 0
# ============================================================

def _phase0_wrapper(session_state, stop_event=None):
    return run_phase0_doi_enrichment_for_session(
        session_state=session_state,
        reporter=session_state._dashboard_reporter,
        generate_report=False,
        stop_event=stop_event,
    )


# ============================================================
# PHASE LOOPS
# ============================================================

def run_phase0_menu_loop(session_state, dashboard: TerminalDashboard) -> str:
    """
    Devolve:
    - 'initial' para voltar ao menu inicial
    """
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

        choice = dashboard.show_phase0_summary_menu()

        if choice == "1":
            phase0_result = None
            continue

        if choice == "2":
            report_path = generate_phase0_report_from_cache(session_state)
            lines = ["Report da fase 0 concluído."]
            if report_path:
                lines.append(f"Report guardado         : {report_path}")
            show_message_and_wait(dashboard, "FASE 0 — DOI ENRICHMENT", lines)
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
                "diagnóstico fase 0",
            )
            continue

        if choice == "5":
            return "initial"


def run_phase1_menu_loop(
    session_state,
    dashboard: TerminalDashboard,
    previous_menu: str = "initial",
) -> str:
    """
    previous_menu:
    - 'initial'
    - 'phase0'

    Devolve:
    - 'initial'
    - 'phase0'
    """
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
                "diagnóstico fase 1",
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
    """
    previous_menu:
    - 'phase1'

    Devolve:
    - 'phase1'
    - 'initial'
    """
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
                lines.append(f"Workbook final guardado : {final_path}")
            else:
                lines.append("Não foi possível guardar o workbook final.")

            phase2_data = phase2_summary or {}
            lines.append(
                f"PDFs disponíveis        : {phase2_data.get('pdfs_available_global', 0)}"
            )
            lines.append(
                f"PDFs descarregados agora: {phase2_data.get('downloaded_now_total', 0)}"
            )
            lines.append(f"Pasta de PDFs           : {PDF_BASE_DIR}")

            show_message_and_wait(
                dashboard,
                "FASE 2 — PDF SPECIALIZED DOWNLOAD",
                lines,
            )
            continue

        if choice == "3":
            run_diagnostic_after_phase(
                session_state,
                dashboard,
                "diagnóstico fase 2",
            )
            continue

        if choice == "4":
            return "phase1"

        if choice == "5":
            return "initial"


# ============================================================
# NAVEGAÇÃO DE ALTO NÍVEL
# ============================================================

def run_navigation_from(
    session_state,
    dashboard: TerminalDashboard,
    start_phase: str,
) -> None:
    """
    start_phase:
    - 'phase0'
    - 'phase1'
    """
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


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    _start_stdin_reader()

    dashboard = TerminalDashboard(input_fn=_get_line)
    dashboard.init_terminal_mode()

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
            choice = dashboard.show_initial_menu()

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

            if choice == "3":
                run_initial_diagnostic(
                    session_state=session_state,
                    dashboard=dashboard,
                )
                continue

            if choice == "4":
                raise SystemExit(0)

    except UserRequestedQuit:
        raise SystemExit(0)

    except KeyboardInterrupt:
        dashboard.show_message(
            "INTERRUPÇÃO",
            [
                "Interrupção pedida pelo utilizador.",
                "A guardar checkpoint temporário...",
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
                    "Checkpoint guardado com sucesso.",
                    f"Ficheiro               : {checkpoint_path}",
                ],
            )
        else:
            dashboard.show_message(
                "CHECKPOINT",
                ["Não foi possível guardar o checkpoint."],
            )

    except Exception as exc:
        checkpoint_path = save_session_checkpoint(
            session_state=session_state,
            label="error",
            timestamp=session_state.timestamp or None,
        )

        lines = [f"Erro: {exc}"]
        if checkpoint_path:
            lines.append(f"Checkpoint guardado     : {checkpoint_path}")
        else:
            lines.append("Não foi possível guardar o checkpoint após erro.")

        dashboard.show_message("ERRO", lines)
        raise


if __name__ == "__main__":
    main()
