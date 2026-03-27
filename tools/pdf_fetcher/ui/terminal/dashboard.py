from __future__ import annotations

import os
import sys
import time
from typing import Callable, Dict, List, Optional, Sequence

from tools.pdf_fetcher.core.config import FORCE_SIMPLE_TERMINAL, FRAME_WIDTH
from tools.pdf_fetcher.core.utils import format_seconds


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
        self.phase2_last_payload: Dict = {}
        self.phase2_show_all_resolver_stats = False

        self.show_controls_bar = False

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
                enable_virtual_terminal_processing = 0x0004
                new_mode = mode.value | enable_virtual_terminal_processing
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

    def _build_controls_bar(self) -> List[str]:
        col = FRAME_WIDTH // 3
        line = "  [P] Pause".ljust(col) + "[V] Back to menu".ljust(col) + "[S] Exit app"
        return [
            "-" * FRAME_WIDTH,
            line,
            "-" * FRAME_WIDTH,
            "Command (P/V/S) + Enter:",
        ]

    def _with_controls(self, lines: List[str]) -> List[str]:
        if self.show_controls_bar:
            return lines + self._build_controls_bar()
        return lines

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
        lines.append("Choose:")
        return lines

    def prompt_choice(self, valid_choices: Sequence[str]) -> str:
        valid = {str(c).strip() for c in valid_choices}
        while True:
            choice = self._input_fn("> ").strip()
            if choice in valid:
                return choice

    def show_initial_menu(self, allow_phase2_start: bool = False) -> str:
        options = [
            "[1] Start from phase 0 - DOI Enrichment",
            "[2] Start from phase 1 - PDF Basic Download",
        ]
        valid_choices = ["1", "2"]
        subtitle = None

        if allow_phase2_start:
            options.append("[3] Start from phase 2 - PDF Specialized Download")
            options.append("[4] Run initial diagnostic")
            options.append("[5] Exit")
            valid_choices.extend(["3", "4", "5"])
            subtitle = "NOTICE: Phase 1 data found in Current. You can start directly from phase 2."
            if self.terminal_mode == "ansi":
                subtitle = f"\033[5m{subtitle}\033[0m"
        else:
            options.append("[3] Run initial diagnostic")
            options.append("[4] Exit")
            valid_choices.extend(["3", "4"])

        lines = self.build_menu_lines(
            title="PDF FETCHER - Study Screening Toolkit",
            options=options,
            subtitle=subtitle,
        )
        self.render_static_block(lines)
        return self.prompt_choice(valid_choices)

    def show_phase0_menu(self) -> str:
        lines = self.build_menu_lines(
            title="PHASE 0 COMPLETED - DOI ENRICHMENT",
            options=[
                "[1] Repeat phase 0 - DOI Enrichment",
                "[2] Generate phase 0 report",
                "[3] Move to phase 1 - PDF Basic Download",
                "[4] Run diagnostic",
                "[5] Back to main menu",
            ],
        )
        self.render_static_block(lines)
        return self.prompt_choice(["1", "2", "3", "4", "5"])

    def show_phase1_menu(self) -> str:
        lines = self.build_menu_lines(
            title="PHASE 1 COMPLETED - PDF BASIC DOWNLOAD",
            options=[
                "[1] Repeat phase 1 - PDF Basic Download",
                "[2] Move to phase 2 - PDF Specialized Download",
                "[3] Run diagnostic",
                "[4] Back to phase 0 - DOI Enrichment",
                "[5] Back to main menu",
            ],
        )
        self.render_static_block(lines)
        return self.prompt_choice(["1", "2", "3", "4", "5"])

    def show_phase2_menu(self) -> str:
        lines = self.build_menu_lines(
            title="PHASE 2 COMPLETED - PDF SPECIALIZED DOWNLOAD",
            options=[
                "[1] Repeat phase 2 - PDF Specialized Download",
                "[2] Save final workbook",
                "[3] Run diagnostic",
                "[4] Back to phase 1 - PDF Basic Download",
                "[5] Back to main menu",
            ],
        )
        self.render_static_block(lines)
        return self.prompt_choice(["1", "2", "3", "4", "5"])

    def show_pause_menu(self) -> str:
        self.reset_dynamic_blocks()
        lines = self.build_menu_lines(
            title="EXECUTION PAUSED",
            options=[
                "[1] Continue",
                "[2] Back to previous menu",
                "[3] Exit app",
            ],
        )
        self.render_static_block(lines)
        return self.prompt_choice(["1", "2", "3"])

    def _strip_trailing_separator(self, lines: List[str]) -> List[str]:
        if lines and lines[-1] == "=" * FRAME_WIDTH:
            return lines[:-1]
        return list(lines)

    def show_phase0_summary_menu(self) -> str:
        panel = self._strip_trailing_separator(
            self.phase0_lines
            if self.phase0_lines
            else [
                "=" * FRAME_WIDTH,
                "PHASE 0 COMPLETED - DOI ENRICHMENT",
                "=" * FRAME_WIDTH,
            ]
        )
        menu_lines = [
            "-" * FRAME_WIDTH,
            "WHAT WOULD YOU LIKE TO DO NEXT?",
            "-" * FRAME_WIDTH,
            "[1] Repeat phase 0 - DOI Enrichment",
            "[2] Generate phase 0 report",
            "[3] Move to phase 1 - PDF Basic Download",
            "[4] Run diagnostic",
            "[5] Back to main menu",
            "=" * FRAME_WIDTH,
            "Choose:",
        ]
        self.reset_dynamic_blocks()
        self.render_static_block(panel + menu_lines)
        return self.prompt_choice(["1", "2", "3", "4", "5"])

    def show_phase1_summary_menu(self) -> str:
        panel = self._strip_trailing_separator(
            self.phase1_lines
            if self.phase1_lines
            else [
                "=" * FRAME_WIDTH,
                "PHASE 1 COMPLETED - PDF BASIC DOWNLOAD",
                "=" * FRAME_WIDTH,
            ]
        )
        menu_lines = [
            "-" * FRAME_WIDTH,
            "WHAT WOULD YOU LIKE TO DO NEXT?",
            "-" * FRAME_WIDTH,
            "[1] Repeat phase 1 - PDF Basic Download",
            "[2] Move to phase 2 - PDF Specialized Download",
            "[3] Run diagnostic",
            "[4] Back to phase 0 - DOI Enrichment",
            "[5] Back to main menu",
            "=" * FRAME_WIDTH,
            "Choose:",
        ]
        self.reset_dynamic_blocks()
        self.render_static_block(panel + menu_lines)
        return self.prompt_choice(["1", "2", "3", "4", "5"])

    def show_phase2_summary_menu(self) -> str:
        if self.phase2_last_payload:
            self.phase2_lines = self.build_phase2_lines(self.phase2_last_payload)

        panel = self._strip_trailing_separator(
            self.phase2_lines
            if self.phase2_lines
            else [
                "=" * FRAME_WIDTH,
                "PHASE 2 COMPLETED - PDF SPECIALIZED DOWNLOAD",
                "=" * FRAME_WIDTH,
            ]
        )
        menu_lines = [
            "-" * FRAME_WIDTH,
            "WHAT WOULD YOU LIKE TO DO NEXT?",
            "-" * FRAME_WIDTH,
            "[1] Repeat phase 2 - PDF Specialized Download",
            "[2] Save final workbook",
            "[3] Run diagnostic",
            "[4] Back to phase 1 - PDF Basic Download",
            "[5] Back to main menu",
            "[6] Collapse resolver stats" if self.phase2_show_all_resolver_stats else "[6] Show all resolver stats",
            "=" * FRAME_WIDTH,
            "Choose:",
        ]
        self.reset_dynamic_blocks()
        self.render_static_block(panel + menu_lines)
        return self.prompt_choice(["1", "2", "3", "4", "5", "6"])

    def build_phase2_resolver_stats_lines(self) -> List[str]:
        payload = self.phase2_last_payload or {}
        resolver_attempts = payload.get("resolver_attempts", {}) or {}
        resolver_recovered = payload.get("resolver_recovered", {}) or {}
        resolver_duplicates = payload.get("resolver_duplicates", {}) or {}
        resolver_totals = payload.get("resolver_totals", {}) or {}
        resolver_processed = payload.get("resolver_processed", {}) or {}

        lines = [
            "=" * FRAME_WIDTH,
            "PHASE 2 - ALL RESOLVER STATS",
            "=" * FRAME_WIDTH,
        ]

        if not resolver_attempts:
            lines.extend(
                [
                    "No resolver stats available.",
                    "=" * FRAME_WIDTH,
                ]
            )
            return lines

        for resolver_name in sorted(resolver_attempts):
            total = resolver_totals.get(resolver_name, 0)
            processed = resolver_processed.get(resolver_name, 0)
            recovered = resolver_recovered.get(resolver_name, 0)
            duplicates = resolver_duplicates.get(resolver_name, 0)
            lines.append(f"Resolver               : {resolver_name}")
            lines.append(f"Progress               : {processed}/{total}")
            lines.append(f"Downloads              : {recovered}/{total}")
            lines.append(f"Duplicates             : {duplicates}/{total}")
            lines.append("-" * FRAME_WIDTH)

        lines.append("=" * FRAME_WIDTH)
        return lines

    def show_phase2_resolver_stats_menu(self) -> str:
        lines = self.build_phase2_resolver_stats_lines()
        menu_lines = [
            "-" * FRAME_WIDTH,
            "WHAT WOULD YOU LIKE TO DO NEXT?",
            "-" * FRAME_WIDTH,
            "[1] Back to phase 2 summary",
            "=" * FRAME_WIDTH,
            "Choose:",
        ]
        self.reset_dynamic_blocks()
        self.render_static_block(lines[:-1] + menu_lines)
        return self.prompt_choice(["1"])

    def show_message(self, title: str, message_lines: Sequence[str]) -> None:
        lines = self.build_title_block(title)
        lines.extend(message_lines)
        lines.append("=" * FRAME_WIDTH)
        self.render_static_block(lines)

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
        needs_review = payload.get("total_needs_review", 0)
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

        auto_applied_rate = (enriched / eligible * 100.0) if eligible > 0 else 0.0
        potential_match_rate = ((enriched + needs_review) / eligible * 100.0) if eligible > 0 else 0.0

        return [
            "=" * FRAME_WIDTH,
            "PDF FETCHER - DOWNLOAD STATUS",
            "=" * FRAME_WIDTH,
            "Current phase           : Phase 0 - DOI Enrichment",
            "-" * FRAME_WIDTH,
            f"Records read            : {total_rows_read}",
            f"Eligible for lookup     : {eligible}",
            f"Missing DOI             : {missing_doi}",
            "-" * FRAME_WIDTH,
            f"Enriched DOIs           : {enriched}",
            f"Needs review            : {needs_review}",
            f"Unresolved              : {unresolved}",
            f"Auto-applied rate       : {auto_applied_rate:6.2f}%",
            f"Potential match rate    : {potential_match_rate:6.2f}%",
            "-" * FRAME_WIDTH,
            f"Records processed       : {processed}",
            f"Records remaining       : {remaining_count}",
            f"Elapsed time            : {format_seconds(elapsed)}",
            f"Estimated total time    : {format_seconds(estimated_total)}",
            f"Estimated remaining     : {format_seconds(estimated_remaining)}",
            "-" * FRAME_WIDTH,
            f"Last record             : {last_record_id or '-'}",
            f"Last result             : {last_status or '-'}",
            f"Confidence              : {last_confidence or '-'}",
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
        pdfs_in_folder = payload.get("pdfs_in_folder", pdfs_available_global)
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
        pdf_count_warning = ""
        if pdfs_in_folder != pdfs_available_global:
            pdf_count_warning = f"Workbook/folder mismatch : {pdfs_available_global} / {pdfs_in_folder}"

        lines = [
            "=" * FRAME_WIDTH,
            "PDF FETCHER - DOWNLOAD STATUS",
            "=" * FRAME_WIDTH,
            "Current phase           : Phase 1 - PDF Basic Download",
            "-" * FRAME_WIDTH,
            f"Records checked         : {processed}",
            f"Records remaining       : {remaining_count}",
            f"Total to check          : {total}",
            f"Parallel workers        : {workers}",
            "-" * FRAME_WIDTH,
            f"PDFs available          : {pdfs_available_global}",
            f"PDFs in folder          : {pdfs_in_folder}",
            f"PDFs downloaded now     : {downloaded_now_total}",
            f"Failures                : {failures_count}",
            f"Global success rate     : {success_rate_global:6.2f}%",
            "-" * FRAME_WIDTH,
            f"Elapsed time            : {format_seconds(elapsed)}",
            f"Estimated total time    : {format_seconds(estimated_total)}",
            f"Estimated remaining     : {format_seconds(estimated_remaining)}",
            "-" * FRAME_WIDTH,
            f"Last record             : {last_record_id or '-'}",
            f"Last status             : {last_status or '-'}",
            "=" * FRAME_WIDTH,
        ]
        if pdf_count_warning:
            lines.insert(-1, pdf_count_warning)
        return lines

    def build_phase2_lines(self, payload: Dict) -> List[str]:
        phase2_pool_total = payload.get("phase2_pool_total", payload["retry_total"])
        retry_processed = payload["retry_processed"]
        retry_total = payload["retry_total"]
        unassigned_total = payload.get("unassigned_total", max(0, phase2_pool_total - retry_total))
        phase2_start_time = payload["phase2_start_time"]
        resolver_name = payload["resolver_name"]
        last_record_id = payload["last_record_id"]
        last_doi = payload["last_doi"]
        last_status = payload["last_status"]
        last_detail = payload.get("last_detail", "")
        pdfs_available_global = payload["pdfs_available_global"]
        pdfs_in_folder = payload.get("pdfs_in_folder", pdfs_available_global)
        downloaded_now_total = payload["downloaded_now_total"]
        recovered_this_phase = payload["recovered_this_phase"]
        total_records = payload["total_records"]
        resolver_attempts = payload.get("resolver_attempts", {}) or {}
        resolver_recovered = payload.get("resolver_recovered", {}) or {}
        resolver_duplicates = payload.get("resolver_duplicates", {}) or {}
        resolver_totals = payload.get("resolver_totals", {}) or {}
        resolver_processed = payload.get("resolver_processed", {}) or {}

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
        resolver_stat_lines: List[str] = []
        if resolver_attempts and self.phase2_show_all_resolver_stats:
            max_resolvers_to_show = len(resolver_attempts)
            ordered_names = sorted(resolver_attempts)
            visible_names = ordered_names[:max_resolvers_to_show]

            for idx, resolver_name_item in enumerate(visible_names):
                attempts = resolver_attempts.get(resolver_name_item, 0)
                recovered = resolver_recovered.get(resolver_name_item, 0)
                duplicates = resolver_duplicates.get(resolver_name_item, 0)
                label = "Resolver stats" if idx == 0 else ""
                stat_text = f"{resolver_name_item} {recovered}/{attempts}"
                if duplicates > 0:
                    stat_text += f" dup {duplicates}"
                resolver_stat_lines.append(f"{label:<24}: {stat_text}")

            hidden_count = max(0, len(ordered_names) - len(visible_names))
            if hidden_count > 0:
                resolver_stat_lines.append(f"{'':<24}: +{hidden_count} more resolvers")

        current_resolver_total = resolver_totals.get(resolver_name, 0) if resolver_name else 0
        current_resolver_done = resolver_processed.get(resolver_name, 0) if resolver_name else 0
        current_resolver_recovered = resolver_recovered.get(resolver_name, 0) if resolver_name else 0
        current_resolver_duplicates_count = resolver_duplicates.get(resolver_name, 0) if resolver_name else 0
        current_resolver_progress = "-"
        if resolver_name and current_resolver_total:
            current_resolver_progress = f"{current_resolver_done}/{current_resolver_total}"
        current_resolver_downloads = "-"
        if resolver_name and current_resolver_total:
            current_resolver_downloads = f"{current_resolver_recovered}/{current_resolver_total}"
        current_resolver_duplicates = "-"
        if resolver_name and current_resolver_total:
            current_resolver_duplicates = f"{current_resolver_duplicates_count}/{current_resolver_total}"

        lines = [
            "=" * FRAME_WIDTH,
            "PDF FETCHER - DOWNLOAD STATUS",
            "=" * FRAME_WIDTH,
            "Current phase           : Phase 2 - PDF Specialized Download",
            f"Current resolver        : {resolver_name or '-'}",
            f"Resolver progress       : {current_resolver_progress}",
            f"Resolver downloads      : {current_resolver_downloads}",
            f"Resolver duplicates     : {current_resolver_duplicates}",
            "-" * FRAME_WIDTH,
            f"Records in retry        : {retry_total}",
            f"Records processed       : {retry_processed}",
            f"Records remaining       : {retry_remaining}",
            "-" * FRAME_WIDTH,
            f"PDFs available          : {pdfs_available_global}",
            f"PDFs in folder          : {pdfs_in_folder}",
            f"PDFs downloaded now     : {downloaded_now_total}",
            "-" * FRAME_WIDTH,
            f"Phase 2 elapsed time    : {format_seconds(elapsed)}",
            f"Phase 2 remaining       : {format_seconds(estimated_remaining)}",
            "-" * FRAME_WIDTH,
            f"Last record             : {last_record_id or '-'}",
            f"Last DOI                : {last_doi or '-'}",
            f"Last status             : {last_status or '-'}",
            "=" * FRAME_WIDTH,
        ]
        if resolver_stat_lines:
            insert_at = lines.index("-" * FRAME_WIDTH, 10)
            for offset, stat_line in enumerate(resolver_stat_lines):
                lines.insert(insert_at + offset, stat_line)
        if last_status.startswith("resolver_exception_") and last_detail:
            lines.insert(-1, f"Last detail             : {last_detail}")
        if pdfs_in_folder != pdfs_available_global:
            lines.insert(-1, f"Workbook/folder mismatch : {pdfs_available_global} / {pdfs_in_folder}")
        return lines

    def build_diagnostic_lines(self, payload: Dict) -> List[str]:
        processed = payload.get("processed", 0)
        total = payload.get("total", 0)
        workers = payload.get("workers", "-")
        start_time = payload.get("start_time", time.time())
        title = payload.get("title", "DIAGNOSTIC")
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
            f"Records checked         : {processed}",
            f"Records remaining       : {remaining_count}",
            f"Total to check          : {total}",
            f"Parallel workers        : {workers}",
            "-" * FRAME_WIDTH,
            f"Elapsed time            : {format_seconds(elapsed)}",
            f"Estimated total time    : {format_seconds(estimated_total)}",
            f"Estimated remaining     : {format_seconds(estimated_remaining)}",
            "-" * FRAME_WIDTH,
            f"Last record             : {last_record_id or '-'}",
            f"Last status             : {last_status or '-'}",
            "=" * FRAME_WIDTH,
        ]

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
            self.phase2_last_payload = dict(payload)
            self.phase2_lines = self.build_phase2_lines(payload)
            self.freeze_phase1_and_start_phase2(self.phase1_lines, self.phase2_lines)
            return

        if event_name in {"phase2_update", "phase2_end"}:
            self.phase2_last_payload = dict(payload)
            self.phase2_lines = self.build_phase2_lines(payload)
            self.render_phase2_block(self.phase1_lines, self.phase2_lines)
            return

        if event_name in {"diagnostic_start", "diagnostic_update", "diagnostic_end"}:
            self.diagnostic_lines = self.build_diagnostic_lines(payload)
            self.render_diagnostic_block(self.diagnostic_lines)
            return

        if event_name in {"save", "finish"}:
            return
