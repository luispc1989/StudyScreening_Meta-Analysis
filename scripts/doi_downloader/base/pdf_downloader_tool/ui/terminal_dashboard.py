
from __future__ import annotations

import os
import sys
import time
from typing import Dict, List, Optional

from app.config import FORCE_SIMPLE_TERMINAL, FRAME_WIDTH
from app.utils import format_seconds


class TerminalDashboard:
    def __init__(self) -> None:
        self.terminal_mode = "simple"  # "ansi" or "simple"

        self.phase1_rendered = False
        self.phase2_rendered = False
        self.phase1_last_height = 0
        self.phase2_last_height = 0

        self.phase1_lines: List[str] = []
        self.phase2_lines: List[str] = []

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
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
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

    def normalize_block(self, lines: List[str]) -> List[str]:
        return [self.fit_line(line) for line in lines]

    def clear_screen_simple(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")

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
        phase1_lines: List[str],
        phase2_lines: Optional[List[str]] = None,
    ) -> None:
        self.clear_screen_simple()
        sys.stdout.write("\n".join(self.normalize_block(phase1_lines)))
        sys.stdout.write("\n")

        if phase2_lines:
            sys.stdout.write("\n")
            sys.stdout.write("\n".join(self.normalize_block(phase2_lines)))
            sys.stdout.write("\n")

        sys.stdout.flush()

    # =========================
    # BLOCK BUILDERS
    # =========================

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
            "PDF DOWNLOAD STATUS",
            "=" * FRAME_WIDTH,
            "Fase atual              : 1/2 - base download",
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
            "PDF DOWNLOAD STATUS",
            "=" * FRAME_WIDTH,
            "Fase atual              : 2/2 - specialized retry",
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

    # =========================
    # HIGH LEVEL RENDER
    # =========================

    def render_phase1_block(self, lines: List[str]) -> None:
        if self.terminal_mode == "simple":
            self.render_simple_combined(lines, None)
            self.phase1_rendered = True
            self.phase1_last_height = len(lines)
            return

        self.phase1_last_height = self._render_block_in_place(
            lines=lines,
            already_rendered=self.phase1_rendered,
            last_height=self.phase1_last_height,
        )
        self.phase1_rendered = True

    def freeze_phase1_and_start_phase2(self, phase1_lines: List[str], phase2_lines: List[str]) -> None:
        if self.terminal_mode == "simple":
            self.render_simple_combined(phase1_lines, phase2_lines)
            self.phase2_rendered = True
            self.phase2_last_height = len(phase2_lines)
            return

        if self.phase2_rendered:
            self.phase2_last_height = self._render_block_in_place(
                lines=phase2_lines,
                already_rendered=True,
                last_height=self.phase2_last_height,
            )
            return

        sys.stdout.write("\n")
        sys.stdout.flush()

        self.phase2_last_height = self._render_block_in_place(
            lines=phase2_lines,
            already_rendered=False,
            last_height=0,
        )
        self.phase2_rendered = True

    def render_phase2_block(self, phase1_lines: List[str], phase2_lines: List[str]) -> None:
        if self.terminal_mode == "simple":
            self.render_simple_combined(phase1_lines, phase2_lines)
            self.phase2_rendered = True
            self.phase2_last_height = len(phase2_lines)
            return

        if not self.phase2_rendered:
            self.freeze_phase1_and_start_phase2(phase1_lines, phase2_lines)
            return

        self.phase2_last_height = self._render_block_in_place(
            lines=phase2_lines,
            already_rendered=True,
            last_height=self.phase2_last_height,
        )

    # =========================
    # REPORTER INTERFACE
    # =========================

    def handle_event(self, event_name: str, payload: Dict) -> None:
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

        if event_name == "save":
            return

        if event_name == "finish":
            return