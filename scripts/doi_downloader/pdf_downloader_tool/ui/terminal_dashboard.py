from __future__ import annotations

import os
import sys
import time
from typing import Callable, Dict, List, Optional, Sequence

from app.config import FORCE_SIMPLE_TERMINAL, FRAME_WIDTH
from app.utils import format_seconds


class TerminalDashboard:
    def __init__(self, input_fn: Optional[Callable[[str], str]] = None) -> None:
        self.terminal_mode = "simple"  # "ansi" or "simple"
        self._input_fn: Callable[[str], str] = input_fn if input_fn is not None else input

        self.phase0_rendered = False
        self.phase1_rendered = False
        self.phase2_rendered = False
        self.diagnostic_rendered = False

        self.phase0_last_height = 0
        self.phase1_last_height = 0
        self.phase2_last_height = 0
        self.diagnostic_last_height = 0

        self.phase0_lines: List[str] = []
        self.phase1_lines: List[str] = []
        self.phase2_lines: List[str] = []
        self.diagnostic_lines: List[str] = []

        self.show_controls_bar = False

    # =========================
    # TERMINAL CAPABILITY
    # =========================

    def is_git_bash(self) -> bool:
        env = os.environ
        return (
            "MINGW" in env.get("MSYSTEM", "").upper()
            or "git\\usr\\bin" in env.get("SHELL", "").lower()
            or "bash.exe" in env.get("TERM_PROGRAM", "").lower()
        )

    def enable_windows_vt_mode(self) -> bool:
        if os.name != "nt":
            return True
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
                new_mode = mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
                return bool(kernel32.SetConsoleMode(handle, new_mode))
        except Exception:
            return False
        return False

    def init_terminal_mode(self) -> None:
        if FORCE_SIMPLE_TERMINAL:
            self.terminal_mode = "simple"
            return
        if self.is_git_bash():
            self.terminal_mode = "simple"
            return
        ansi_ok = sys.stdout.isatty() and self.enable_windows_vt_mode()
        self.terminal_mode = "ansi" if ansi_ok else "simple"

    # =========================
    # LOW LEVEL RENDER HELPERS
    # =========================

    def fit_line(self, text: str, width: int = FRAME_WIDTH) -> str:
        text = str(text or "")
        if len(text) > width:
            return text[:width]
        return text.ljust(width)

    def normalize_block(self, lines: Sequence[str]) -> List[str]:
        return [self.fit_line(line) for line in lines]

    def clear_screen_simple(self) -> None:
        import subprocess

        try:
            if self.is_git_bash():
                subprocess.run(
                    ["clear"],
                    stdin=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif os.name == "nt":
                subprocess.run(
                    "cls",
                    shell=True,
                    stdin=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                subprocess.run(
                    ["clear"],
                    stdin=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except Exception:
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()

    def _clear_current_line(self) -> None:
        sys.stdout.write("\033[2K\r")

    def _move_up(self, lines: int) -> None:
        if lines > 0:
            sys.stdout.write(f"\033[{lines}A")

    def _render_block_in_place(
        self,
        lines: List[str],
        already_rendered: bool,
        last_height: int,
    ) -> int:
        lines = self.normalize_block(lines)
        new_height = len(lines)

        if self.terminal_mode != "ansi":
            sys.stdout.write("\n".join(lines) + "\n")
            sys.stdout.flush()
            return new_height

        if already_rendered:
            self._move_up(last_height)

        total_lines_to_draw = max(last_height, new_height)

        for i in range(total_lines_to_draw):
            self._clear_current_line()
            if i < new_height:
                sys.stdout.write(lines[i])
            if i < total_lines_to_draw - 1:
                sys.stdout.write("\n")

        sys.stdout.flush()
        return new_height

    def render_simple_combined(
        self,
        top_lines: List[str],
        bottom_lines: Optional[List[str]] = None,
    ) -> None:
        self.clear_screen_simple()
        sys.stdout.write("\n".join(self.normalize_block(top_lines)))
        sys.stdout.write("\n")
        if bottom_lines:
            sys.stdout.write("\n")
            sys.stdout.write("\n".join(self.normalize_block(bottom_lines)))
            sys.stdout.write("\n")
        sys.stdout.flush()

    def render_static_block(self, lines: List[str]) -> None:
        self.clear_screen_simple()
        sys.stdout.write("\n".join(self.normalize_block(lines)))
        sys.stdout.write("\n")
        sys.stdout.flush()

    def reset_dynamic_blocks(self) -> None:
        self.phase0_rendered = False
        self.phase1_rendered = False
        self.phase2_rendered = False
        self.diagnostic_rendered = False

        self.phase0_last_height = 0
        self.phase1_last_height = 0
        self.phase2_last_height = 0
        self.diagnostic_last_height = 0

        self.phase0_lines = []
        self.phase1_lines = []
        self.phase2_lines = []
        self.diagnostic_lines = []

        self.show_controls_bar = False

    # =========================
    # CONTROLS BAR
    # =========================

    def _build_controls_bar(self) -> List[str]:
        col = FRAME_WIDTH // 3
        line = (
            "  [P] Parar".ljust(col)
            + "[V] Voltar ao menu".ljust(col)
            + "[S] Sair da app"
        )
        return [
            "-" * FRAME_WIDTH,
            line,
            "-" * FRAME_WIDTH,
            "Comando (P/V/S) + Enter:",
        ]

    def _with_controls(self, lines: List[str]) -> List[str]:
        if self.show_controls_bar:
            return lines + self._build_controls_bar()
        return lines

    # =========================
    # GENERIC BLOCK HELPERS
    # =========================

    def build_title_block(self, title: str, subtitle: Optional[str] = None) -> List[str]:
        lines = [
            "=" * FRAME_WIDTH,
            title,
            "=" * FRAME_WIDTH,
        ]
        if subtitle:
            lines.append(subtitle)
            lines.append("-" * FRAME_WIDTH)
        return lines

    def build_menu_lines(
        self,
        title: str,
        options: Sequence[str],
        subtitle: Optional[str] = None,
    ) -> List[str]:
        lines = self.build_title_block(title, subtitle=subtitle)
        lines.extend(options)
        lines.append("=" * FRAME_WIDTH)
        lines.append("Escolha:")
        return lines

    def prompt_choice(self, valid_choices: Sequence[str]) -> str:
        valid = {str(c).strip() for c in valid_choices}
        while True:
            choice = self._input_fn("> ").strip()
            if choice in valid:
                return choice

    def show_initial_menu(self) -> str:
        lines = self.build_menu_lines(
            title="PDF FETCHER - Study Screening Toolkit",
            options=[
                "[1] Começar pela fase 0 - DOI Enrichment",
                "[2] Começar pela fase 1 - PDF Basic Download",
                "[3] Realizar diagnóstico inicial",
                "[4] Sair",
            ],
        )
        self.render_static_block(lines)
        return self.prompt_choice(["1", "2", "3", "4"])

    # =========================
    # STANDALONE MENUS (fallback)
    # =========================

    def show_phase0_menu(self) -> str:
        lines = self.build_menu_lines(
            title="FASE 0 CONCLUÍDA — DOI ENRICHMENT",
            options=[
                "[1] Repetir fase 0 - DOI Enrichment",
                "[2] Gerar report da fase 0",
                "[3] Passar à fase 1 - PDF Basic Download",
                "[4] Realizar diagnóstico",
                "[5] Voltar ao menu inicial",
            ],
        )
        self.render_static_block(lines)
        return self.prompt_choice(["1", "2", "3", "4", "5"])

    def show_phase1_menu(self) -> str:
        lines = self.build_menu_lines(
            title="FASE 1 CONCLUÍDA — PDF BASIC DOWNLOAD",
            options=[
                "[1] Repetir fase 1 - PDF Basic Download",
                "[2] Passar à fase 2 - PDF Specialized Download",
                "[3] Realizar diagnóstico",
                "[4] Voltar à fase 0 - DOI Enrichment",
                "[5] Voltar ao menu inicial",
            ],
        )
        self.render_static_block(lines)
        return self.prompt_choice(["1", "2", "3", "4", "5"])

    def show_phase2_menu(self) -> str:
        lines = self.build_menu_lines(
            title="FASE 2 CONCLUÍDA — PDF SPECIALIZED DOWNLOAD",
            options=[
                "[1] Repetir fase 2 - PDF Specialized Download",
                "[2] Guardar workbook final",
                "[3] Realizar diagnóstico",
                "[4] Voltar à fase 1 - PDF Basic Download",
                "[5] Voltar ao menu inicial",
            ],
        )
        self.render_static_block(lines)
        return self.prompt_choice(["1", "2", "3", "4", "5"])

    # =========================
    # PAUSE MENU
    # =========================

    def show_pause_menu(self) -> str:
        self.reset_dynamic_blocks()
        lines = self.build_menu_lines(
            title="EXECUÇÃO PAUSADA",
            options=[
                "[1] Continuar",
                "[2] Voltar ao menu anterior",
                "[3] Sair da app",
            ],
        )
        self.render_static_block(lines)
        return self.prompt_choice(["1", "2", "3"])

    # =========================
    # SUMMARY MENUS
    # =========================

    def _strip_trailing_separator(self, lines: List[str]) -> List[str]:
        if lines and lines[-1] == "=" * FRAME_WIDTH:
            return lines[:-1]
        return list(lines)

    def show_phase0_summary_menu(self) -> str:
        panel = self._strip_trailing_separator(
            self.phase0_lines if self.phase0_lines else [
                "=" * FRAME_WIDTH,
                "FASE 0 CONCLUÍDA — DOI ENRICHMENT",
                "=" * FRAME_WIDTH,
            ]
        )
        menu_lines = [
            "-" * FRAME_WIDTH,
            "O QUE FAZER A SEGUIR?",
            "-" * FRAME_WIDTH,
            "[1] Repetir fase 0 - DOI Enrichment",
            "[2] Gerar report da fase 0",
            "[3] Passar à fase 1 - PDF Basic Download",
            "[4] Realizar diagnóstico",
            "[5] Voltar ao menu inicial",
            "=" * FRAME_WIDTH,
            "Escolha:",
        ]
        self.reset_dynamic_blocks()
        self.render_static_block(panel + menu_lines)
        return self.prompt_choice(["1", "2", "3", "4", "5"])

    def show_phase1_summary_menu(self) -> str:
        panel = self._strip_trailing_separator(
            self.phase1_lines if self.phase1_lines else [
                "=" * FRAME_WIDTH,
                "FASE 1 CONCLUÍDA — PDF BASIC DOWNLOAD",
                "=" * FRAME_WIDTH,
            ]
        )
        menu_lines = [
            "-" * FRAME_WIDTH,
            "O QUE FAZER A SEGUIR?",
            "-" * FRAME_WIDTH,
            "[1] Repetir fase 1 - PDF Basic Download",
            "[2] Passar à fase 2 - PDF Specialized Download",
            "[3] Realizar diagnóstico",
            "[4] Voltar à fase 0 - DOI Enrichment",
            "[5] Voltar ao menu inicial",
            "=" * FRAME_WIDTH,
            "Escolha:",
        ]
        self.reset_dynamic_blocks()
        self.render_static_block(panel + menu_lines)
        return self.prompt_choice(["1", "2", "3", "4", "5"])

    def show_phase2_summary_menu(self) -> str:
        panel = self._strip_trailing_separator(
            self.phase2_lines if self.phase2_lines else [
                "=" * FRAME_WIDTH,
                "FASE 2 CONCLUÍDA — PDF SPECIALIZED DOWNLOAD",
                "=" * FRAME_WIDTH,
            ]
        )
        menu_lines = [
            "-" * FRAME_WIDTH,
            "O QUE FAZER A SEGUIR?",
            "-" * FRAME_WIDTH,
            "[1] Repetir fase 2 - PDF Specialized Download",
            "[2] Guardar workbook final",
            "[3] Realizar diagnóstico",
            "[4] Voltar à fase 1 - PDF Basic Download",
            "[5] Voltar ao menu inicial",
            "=" * FRAME_WIDTH,
            "Escolha:",
        ]
        self.reset_dynamic_blocks()
        self.render_static_block(panel + menu_lines)
        return self.prompt_choice(["1", "2", "3", "4", "5"])

    def show_message(self, title: str, message_lines: Sequence[str]) -> None:
        lines = self.build_title_block(title)
        lines.extend(message_lines)
        lines.append("=" * FRAME_WIDTH)
        self.render_static_block(lines)

    # =========================
    # BLOCK BUILDERS
    # =========================

    def build_phase0_lines(self, payload: Dict) -> List[str]:
        processed = payload.get("processed", 0)
        total = payload.get("total", 0)
        start_time = payload.get("start_time", time.time())

        total_rows_read = payload.get("total_rows_read", total)
        existing_doi = payload.get("total_existing_doi", 0)
        missing_doi = payload.get("total_missing_doi", total)
        eligible = payload.get("total_eligible", total)
        skipped_missing_title = payload.get("total_skipped_missing_title", 0)
        skipped_already_downloaded = payload.get("total_skipped_already_downloaded", 0)

        enriched = payload.get("total_enriched", 0)
        unresolved = payload.get("total_unresolved", 0)
        errors = payload.get("total_errors", 0)

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

        enrichment_rate = (enriched / eligible * 100.0) if eligible > 0 else 0.0
        report_status = "sim" if str(report_path).strip() else "não"

        return [
            "=" * FRAME_WIDTH,
            "PDF FETCHER - DOWNLOAD STATUS",
            "=" * FRAME_WIDTH,
            "Fase atual              : Fase 0 - DOI Enrichment",
            "-" * FRAME_WIDTH,
            f"Artigos lidos           : {total_rows_read}",
            f"Com DOI já existente    : {existing_doi}",
            f"Sem DOI detetados       : {missing_doi}",
            f"Elegíveis para procurar : {eligible}",
            f"Ignorados (sem título)  : {skipped_missing_title}",
            f"Ignorados (já com PDF)  : {skipped_already_downloaded}",
            "-" * FRAME_WIDTH,
            f"DOIs enriquecidos       : {enriched}",
            f"Não resolvidos          : {unresolved}",
            f"Erros de pesquisa       : {errors}",
            f"Taxa de enriquecimento  : {enrichment_rate:6.2f}%",
            f"Report gerado           : {report_status}",
            "-" * FRAME_WIDTH,
            f"Artigos tratados        : {processed}",
            f"Artigos por tratar      : {remaining_count}",
            f"Tempo decorrido         : {format_seconds(elapsed)}",
            f"Tempo estimado total    : {format_seconds(estimated_total)}",
            f"Tempo restante estimado : {format_seconds(estimated_remaining)}",
            "-" * FRAME_WIDTH,
            f"Último registo          : {last_record_id or '-'}",
            f"Último título           : {last_title or '-'}",
            f"Último resultado        : {last_status or '-'}",
            f"Último DOI              : {last_doi or '-'}",
            f"Confiança               : {last_confidence or '-'}",
            "=" * FRAME_WIDTH,
        ]

    def build_phase1_lines(self, payload: Dict) -> List[str]:
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
            "=" * FRAME_WIDTH,
            "PDF FETCHER - DOWNLOAD STATUS",
            "=" * FRAME_WIDTH,
            "Fase atual              : Fase 1 - PDF Basic Download",
            "-" * FRAME_WIDTH,
            f"Artigos diagnosticados  : {processed}",
            f"Artigos por diagnosticar: {remaining_count}",
            f"Total a diagnosticar    : {total}",
            f"Workers paralelos       : {workers}",
            "-" * FRAME_WIDTH,
            f"PDFs disponíveis        : {pdfs_available_global}",
            f"PDFs descarregados agora: {downloaded_now_total}",
            f"Falhas                  : {failures_count}",
            f"Taxa de sucesso global  : {success_rate_global:6.2f}%",
            "-" * FRAME_WIDTH,
            f"Tempo decorrido         : {format_seconds(elapsed)}",
            f"Tempo estimado total    : {format_seconds(estimated_total)}",
            f"Tempo restante estimado : {format_seconds(estimated_remaining)}",
            "-" * FRAME_WIDTH,
            f"Último registo          : {last_record_id or '-'}",
            f"Último estado           : {last_status or '-'}",
            "=" * FRAME_WIDTH,
        ]

    def build_phase2_lines(self, payload: Dict) -> List[str]:
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
            "=" * FRAME_WIDTH,
            "PDF FETCHER - DOWNLOAD STATUS",
            "=" * FRAME_WIDTH,
            "Fase atual              : Fase 2 - PDF Specialized Download",
            f"Resolver atual          : {resolver_name or '-'}",
            "-" * FRAME_WIDTH,
            f"Artigos em retry        : {retry_total}",
            f"Artigos tratados        : {retry_processed}",
            f"Artigos por tratar      : {retry_remaining}",
            "-" * FRAME_WIDTH,
            f"PDFs disponíveis        : {pdfs_available_global}",
            f"PDFs descarregados agora: {downloaded_now_total}",
            f"Recuperados nesta fase  : {recovered_this_phase}",
            f"Ainda sem PDF           : {phase2_still_without_pdf}",
            f"Taxa de sucesso global  : {success_rate_global:6.2f}%",
            "-" * FRAME_WIDTH,
            f"Tempo decorrido fase 2  : {format_seconds(elapsed)}",
            f"Tempo estimado fase 2   : {format_seconds(estimated_total)}",
            f"Tempo restante fase 2   : {format_seconds(estimated_remaining)}",
            "-" * FRAME_WIDTH,
            f"Último registo          : {last_record_id or '-'}",
            f"Último DOI              : {last_doi or '-'}",
            f"Último estado           : {last_status or '-'}",
            "=" * FRAME_WIDTH,
        ]

    def build_diagnostic_lines(self, payload: Dict) -> List[str]:
        processed = payload.get("processed", 0)
        total = payload.get("total", 0)
        workers = payload.get("workers", "-")
        start_time = payload.get("start_time", time.time())
        title = payload.get("title", "DIAGNÓSTICO")
        last_record_id = payload.get("last_record_id", "")
        last_status = payload.get("last_status", "")

        elapsed = time.time() - start_time
        remaining_count = max(0, total - processed)

        if processed > 0:
            estimated_total = (elapsed / processed) * total
            estimated_remaining = max(0.0, estimated_total - elapsed)
        else:
            estimated_total = 0.0
            estimated_remaining = 0.0

        return [
            "=" * FRAME_WIDTH,
            title,
            "=" * FRAME_WIDTH,
            f"Artigos diagnosticados  : {processed}",
            f"Artigos por diagnosticar: {remaining_count}",
            f"Total a diagnosticar    : {total}",
            f"Workers paralelos       : {workers}",
            "-" * FRAME_WIDTH,
            f"Tempo decorrido         : {format_seconds(elapsed)}",
            f"Tempo estimado total    : {format_seconds(estimated_total)}",
            f"Tempo restante estimado : {format_seconds(estimated_remaining)}",
            "-" * FRAME_WIDTH,
            f"Último registo          : {last_record_id or '-'}",
            f"Último estado           : {last_status or '-'}",
            "=" * FRAME_WIDTH,
        ]

    # =========================
    # HIGH LEVEL RENDER
    # =========================

    def render_phase0_block(self, lines: List[str]) -> None:
        display = self._with_controls(lines)
        if self.terminal_mode == "simple":
            self.render_simple_combined(display, None)
            self.phase0_rendered = True
            self.phase0_last_height = len(display)
            return
        self.phase0_last_height = self._render_block_in_place(
            lines=display,
            already_rendered=self.phase0_rendered,
            last_height=self.phase0_last_height,
        )
        self.phase0_rendered = True

    def render_phase1_block(self, lines: List[str]) -> None:
        display = self._with_controls(lines)
        if self.terminal_mode == "simple":
            self.render_simple_combined(display, None)
            self.phase1_rendered = True
            self.phase1_last_height = len(display)
            return
        self.phase1_last_height = self._render_block_in_place(
            lines=display,
            already_rendered=self.phase1_rendered,
            last_height=self.phase1_last_height,
        )
        self.phase1_rendered = True

    def freeze_phase1_and_start_phase2(self, phase1_lines: List[str], phase2_lines: List[str]) -> None:
        display2 = self._with_controls(phase2_lines)
        if self.terminal_mode == "simple":
            self.render_simple_combined(phase1_lines, display2)
            self.phase2_rendered = True
            self.phase2_last_height = len(display2)
            return
        if self.phase2_rendered:
            self.phase2_last_height = self._render_block_in_place(
                lines=display2,
                already_rendered=True,
                last_height=self.phase2_last_height,
            )
            return
        sys.stdout.write("\n")
        sys.stdout.flush()
        self.phase2_last_height = self._render_block_in_place(
            lines=display2,
            already_rendered=False,
            last_height=0,
        )
        self.phase2_rendered = True

    def render_phase2_block(self, phase1_lines: List[str], phase2_lines: List[str]) -> None:
        display2 = self._with_controls(phase2_lines)
        if self.terminal_mode == "simple":
            self.render_simple_combined(phase1_lines, display2)
            self.phase2_rendered = True
            self.phase2_last_height = len(display2)
            return
        if not self.phase2_rendered:
            self.freeze_phase1_and_start_phase2(phase1_lines, phase2_lines)
            return
        self.phase2_last_height = self._render_block_in_place(
            lines=display2,
            already_rendered=True,
            last_height=self.phase2_last_height,
        )

    def render_diagnostic_block(self, lines: List[str]) -> None:
        display = self._with_controls(lines)
        if self.terminal_mode == "simple":
            self.render_simple_combined(display, None)
            self.diagnostic_rendered = True
            self.diagnostic_last_height = len(display)
            return
        self.diagnostic_last_height = self._render_block_in_place(
            lines=display,
            already_rendered=self.diagnostic_rendered,
            last_height=self.diagnostic_last_height,
        )
        self.diagnostic_rendered = True

    # =========================
    # REPORTER INTERFACE
    # =========================

    def handle_event(self, event_name: str, payload: Dict) -> None:
        if event_name in {"phase0_start", "phase0_update", "phase0_end"}:
            self.phase0_lines = self.build_phase0_lines(payload)
            self.render_phase0_block(self.phase0_lines)
            return

        if event_name in {"phase1_start", "phase1_update", "phase1_end"}:
            self.phase1_lines = self.build_phase1_lines(payload)
            self.render_phase1_block(self.phase1_lines)
            return

        if event_name == "phase2_start":
            self.phase2_lines = self.build_phase2_lines(payload)
            self.freeze_phase1_and_start_phase2(self.phase1_lines, self.phase2_lines)
            return

        if event_name in {"phase2_update", "phase2_end"}:
            self.phase2_lines = self.build_phase2_lines(payload)
            self.render_phase2_block(self.phase1_lines, self.phase2_lines)
            return

        if event_name in {"diagnostic_start", "diagnostic_update", "diagnostic_end"}:
            self.diagnostic_lines = self.build_diagnostic_lines(payload)
            self.render_diagnostic_block(self.diagnostic_lines)
            return

        if event_name in {"save", "finish"}:
            return