from __future__ import annotations

import importlib
import inspect
import threading
import time
from collections import Counter
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from typing import Callable, Dict, List, Optional, Tuple

from tools.pdf_fetcher.core.config import (
    BASE_AVAILABLE_STATUSES,
    BASE_DOWNLOADED_NOW_STATUSES,
    ENABLE_SPECIALIZED_RESOLVERS,
    MAX_WORKERS,
    PDF_BASE_DIR,
    REFRESH_DASHBOARD_EVERY_N_COMPLETIONS,
    SAVE_EVERY_N_ROWS,
    SLEEP_BETWEEN_REQUESTS,
    SPECIALIZED_DOWNLOADED_NOW_STATUSES,
    SPECIALIZED_SAVE_EVERY_N_ROWS,
)
from tools.pdf_fetcher.core.excel_io import safe_save_workbook, save_final_workbook, save_session_checkpoint, write_result
from tools.pdf_fetcher.core.models import (
    DownloadResult,
    Phase1Summary,
    Phase2Summary,
    Record,
    RetryTask,
    SessionState,
)
from tools.pdf_fetcher.core.resolver_detector import get_ordered_resolver_names
from tools.pdf_fetcher.core.utils import normalize_doi
from tools.pdf_fetcher.core.resolvers.base_download import process_record_phase1


ReporterType = Optional[Callable[[str, dict], None]]
SaveCallbackType = Optional[Callable[[int], Tuple[bool, str]]]
StopEventType = Optional[threading.Event]


def emit(reporter: ReporterType, event_name: str, payload: dict) -> None:
    if reporter is None:
        return
    reporter(event_name, payload)


def count_pdf_files_in_output_dir() -> int:
    if not PDF_BASE_DIR.exists():
        return 0
    return sum(1 for path in PDF_BASE_DIR.glob("*.pdf") if path.is_file())


def _resolve_specialized_resolver_callable(resolver_name: str):
    resolver_specs = {
        "elsevier": ("tools.pdf_fetcher.core.resolvers.elsevier", ("try_elsevier_resolver",)),
        "frontiers": ("tools.pdf_fetcher.core.resolvers.frontiers", ("try_frontiers_resolver",)),
        "mdpi": ("tools.pdf_fetcher.core.resolvers.mdpi", ("try_mdpi_resolver",)),
        "springer": ("tools.pdf_fetcher.core.resolvers.springer", ("try_springer_resolver",)),
    }

    spec = resolver_specs.get(resolver_name)
    if spec is None:
        return None

    module_name, candidate_function_names = spec

    try:
        module = importlib.import_module(module_name)
    except Exception:
        return None

    for function_name in candidate_function_names:
        fn = getattr(module, function_name, None)
        if callable(fn):
            return fn

    return None


def _call_with_optional_stop_event(run_fn, **kwargs):
    """
    Chama run_fn passando stop_event apenas se a assinatura o aceitar.
    """
    stop_event = kwargs.pop("stop_event", None)

    if stop_event is None:
        return run_fn(**kwargs)

    try:
        signature = inspect.signature(run_fn)
    except Exception:
        return run_fn(**kwargs)

    if "stop_event" in signature.parameters:
        return run_fn(stop_event=stop_event, **kwargs)

    return run_fn(**kwargs)


def build_retry_tasks(
    records: List[Record],
    phase1_results_by_row: Dict[int, DownloadResult],
    selected_resolver: Optional[str] = None,
) -> List[RetryTask]:
    tasks: List[RetryTask] = []
    resolver_order = {"mdpi": 0, "frontiers": 1, "springer": 2, "elsevier": 3}

    if not ENABLE_SPECIALIZED_RESOLVERS:
        return tasks

    for record in records:
        phase1_result = phase1_results_by_row.get(record.row_idx)
        if phase1_result is None:
            continue

        resolver_names = get_ordered_resolver_names(record, phase1_result)
        if not resolver_names:
            continue

        if selected_resolver and resolver_names[0] != selected_resolver:
            continue

        tasks.append(RetryTask(record=record, resolver_names=resolver_names))

    tasks.sort(
        key=lambda task: (
            resolver_order.get(task.resolver_names[0] if task.resolver_names else "", 99),
            task.record.row_idx,
        )
    )

    return tasks


def _should_try_next_resolver(result: DownloadResult) -> bool:
    status = str(result.pdf_download_status or "").strip().lower()
    if not status:
        return True

    if status in {"downloaded", "duplicate_pdf", "downloaded_frontiers", "downloaded_mdpi", "downloaded_springer"}:
        return False

    if status.startswith("not_"):
        return True
    if status.startswith("pdf_link_not_found_"):
        return True
    if status.startswith("download_failed_"):
        return True
    if status.startswith("resolver_exception_"):
        return True
    if status.startswith("unsupported_specialized_resolver_"):
        return True

    return False


def process_record_phase2(
    record: Record,
    resolver_names: List[str],
    phase1_result: Optional[DownloadResult] = None,
) -> tuple[DownloadResult, str]:
    source_url = ""
    if phase1_result is not None:
        source_url = str(phase1_result.pdf_source_url or "").strip()

    last_result: Optional[DownloadResult] = None
    last_resolver_name = "none"

    for resolver_name in resolver_names:
        resolver_fn = _resolve_specialized_resolver_callable(resolver_name)
        last_resolver_name = resolver_name

        if resolver_fn is not None:
            try:
                result = resolver_fn(record, source_url=source_url)
            except Exception as exc:
                detail = type(exc).__name__
                message = str(exc).strip()
                if message:
                    detail = f"{detail}: {message}"
                result = DownloadResult(
                    pdf_downloaded=0,
                    pdf_download_status=f"resolver_exception_{resolver_name}",
                    pdf_file_name=record.file_name,
                    pdf_source_url=source_url,
                    pdf_local_path="",
                    pdf_http_status=None,
                    pdf_checked_at=f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {detail}",
                )
        else:
            result = DownloadResult(
                pdf_downloaded=0,
                pdf_download_status=f"unsupported_specialized_resolver_{resolver_name}",
                pdf_file_name=record.file_name,
                pdf_source_url=source_url,
                pdf_local_path="",
                pdf_http_status=None,
                pdf_checked_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            )

        last_result = result
        if not _should_try_next_resolver(result):
            return result, resolver_name

    if last_result is None:
        last_result = DownloadResult(
            pdf_downloaded=0,
            pdf_download_status="unsupported_specialized_resolver_none",
            pdf_file_name=record.file_name,
            pdf_source_url=source_url,
            pdf_local_path="",
            pdf_http_status=None,
            pdf_checked_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        )
    return last_result, last_resolver_name


def _should_emit_progress(processed: int, total: int) -> bool:
    if processed == 1:
        return True
    if processed == total:
        return True
    if processed % REFRESH_DASHBOARD_EVERY_N_COMPLETIONS == 0:
        return True
    return False


def _should_emit_phase2_progress(processed: int, total: int) -> bool:
    if total <= 0:
        return True
    if processed == 1:
        return True
    if processed == total:
        return True
    if processed % 5 == 0:
        return True
    return False


def _run_phase1_core(
    wb,
    ws,
    col_map,
    records: List[Record],
    reporter: ReporterType = None,
    save_callback: SaveCallbackType = None,
    stop_event: StopEventType = None,
) -> tuple[Dict[int, DownloadResult], dict]:
    total_to_process = len(records)
    phase1_results_by_row: Dict[int, DownloadResult] = {}

    pdfs_available_global = 0
    downloaded_now_total = 0

    phase1_start_time = time.time()
    phase1_processed = 0
    phase1_last_record_id = ""
    phase1_last_status = "starting"

    emit(
        reporter,
        "phase1_start",
        {
            "processed": 0,
            "total": total_to_process,
            "workers": MAX_WORKERS,
            "start_time": phase1_start_time,
            "last_record_id": "",
            "last_status": "starting",
            "pdfs_available_global": 0,
            "pdfs_in_folder": count_pdf_files_in_output_dir(),
            "downloaded_now_total": 0,
        },
    )

    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    try:
        futures = {}
        next_idx = 0

        while next_idx < total_to_process and len(futures) < MAX_WORKERS:
            record = records[next_idx]
            futures[executor.submit(process_record_phase1, record)] = record
            next_idx += 1

            if SLEEP_BETWEEN_REQUESTS > 0:
                time.sleep(SLEEP_BETWEEN_REQUESTS)

        while futures:
            done, _ = wait(list(futures.keys()), return_when=FIRST_COMPLETED)

            for future in done:
                _original_record = futures.pop(future)
                record, result = future.result()

                write_result(ws, record.row_idx, col_map, result)
                phase1_results_by_row[record.row_idx] = result

                phase1_processed += 1
                phase1_last_record_id = record.record_id
                phase1_last_status = result.pdf_download_status

                if result.pdf_download_status in BASE_AVAILABLE_STATUSES:
                    pdfs_available_global += 1

                if result.pdf_download_status in BASE_DOWNLOADED_NOW_STATUSES:
                    downloaded_now_total += 1

                if _should_emit_progress(phase1_processed, total_to_process):
                    pdfs_in_folder = count_pdf_files_in_output_dir()
                    emit(
                        reporter,
                        "phase1_update",
                        {
                            "processed": phase1_processed,
                            "total": total_to_process,
                            "workers": MAX_WORKERS,
                            "start_time": phase1_start_time,
                            "last_record_id": phase1_last_record_id,
                            "last_status": phase1_last_status,
                            "pdfs_available_global": pdfs_available_global,
                            "pdfs_in_folder": pdfs_in_folder,
                            "downloaded_now_total": downloaded_now_total,
                        },
                    )

                if save_callback is not None and phase1_processed % SAVE_EVERY_N_ROWS == 0:
                    ok, save_path = save_callback(phase1_processed)
                    emit(
                        reporter,
                        "save",
                        {
                            "phase": 1,
                            "ok": ok,
                            "path": save_path,
                            "processed": phase1_processed,
                        },
                    )

                if stop_event is not None and stop_event.is_set():
                    for pending in list(futures.keys()):
                        pending.cancel()
                    futures.clear()
                    break

                while next_idx < total_to_process and len(futures) < MAX_WORKERS:
                    next_record = records[next_idx]
                    futures[executor.submit(process_record_phase1, next_record)] = next_record
                    next_idx += 1

                    if SLEEP_BETWEEN_REQUESTS > 0:
                        time.sleep(SLEEP_BETWEEN_REQUESTS)

            if stop_event is not None and stop_event.is_set():
                break

        stopped_early = stop_event is not None and stop_event.is_set()

        phase1_summary = {
            "processed": phase1_processed,
            "total": total_to_process,
            "workers": MAX_WORKERS,
            "start_time": phase1_start_time,
            "last_record_id": phase1_last_record_id,
            "last_status": phase1_last_status,
            "pdfs_available_global": pdfs_available_global,
            "pdfs_in_folder": count_pdf_files_in_output_dir(),
            "downloaded_now_total": downloaded_now_total,
            "stopped_early": stopped_early,
        }

        emit(reporter, "phase1_end", phase1_summary)
        return phase1_results_by_row, phase1_summary

    except KeyboardInterrupt:
        executor.shutdown(wait=False, cancel_futures=True)
        raise
    finally:
        try:
            executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass


def _run_phase2_core(
    wb,
    ws,
    col_map,
    records: List[Record],
    phase1_results_by_row: Dict[int, DownloadResult],
    phase1_summary: dict,
    reporter: ReporterType = None,
    save_callback: SaveCallbackType = None,
    stop_event: StopEventType = None,
    selected_resolver: Optional[str] = None,
) -> dict:
    total_to_process = len(records)
    phase2_pool_tasks = build_retry_tasks(
        records,
        phase1_results_by_row,
        selected_resolver=selected_resolver,
    )
    phase2_pool_total = len(phase2_pool_tasks)
    retry_tasks = [task for task in phase2_pool_tasks if task.resolver_names]
    retry_total = len(retry_tasks)
    unassigned_total = max(0, phase2_pool_total - retry_total)

    pdfs_available_global = phase1_summary["pdfs_available_global"]
    downloaded_now_total = phase1_summary["downloaded_now_total"]

    if retry_total == 0:
        payload = {
            "phase2_pool_total": phase2_pool_total,
            "retry_processed": 0,
            "retry_total": 0,
            "unassigned_total": unassigned_total,
            "phase2_start_time": time.time(),
            "resolver_name": "none",
            "last_record_id": "",
            "last_doi": "",
            "last_status": "no_retry_tasks",
            "last_detail": "",
            "pdfs_available_global": pdfs_available_global,
            "pdfs_in_folder": count_pdf_files_in_output_dir(),
            "downloaded_now_total": downloaded_now_total,
            "recovered_this_phase": 0,
            "total_records": total_to_process,
            "stopped_early": False,
        }
        emit(reporter, "phase2_start", payload)
        emit(reporter, "phase2_end", payload)
        return payload

    phase2_start_time = time.time()
    retry_processed = 0
    recovered_this_phase = 0
    phase2_last_record_id = ""
    phase2_last_status = "starting"
    phase2_last_doi = ""
    phase2_last_detail = ""
    phase2_current_resolver = "starting"
    resolver_attempts: Counter[str] = Counter()
    resolver_recovered: Counter[str] = Counter()
    resolver_duplicates: Counter[str] = Counter()
    resolver_failed: Counter[str] = Counter()
    resolver_totals: Counter[str] = Counter()
    resolver_processed: Counter[str] = Counter()
    last_emitted_resolver = ""

    for task in retry_tasks:
        primary_name = task.resolver_names[0] if task.resolver_names else "none"
        resolver_totals[primary_name] += 1

    emit(
        reporter,
        "phase2_start",
            {
                "phase2_pool_total": phase2_pool_total,
                "retry_processed": 0,
                "retry_total": retry_total,
                "unassigned_total": unassigned_total,
                "phase2_start_time": phase2_start_time,
                "resolver_name": phase2_current_resolver,
                "last_record_id": "",
                "last_doi": "",
                "last_status": "starting",
                "last_detail": "",
                "pdfs_available_global": pdfs_available_global,
                "pdfs_in_folder": count_pdf_files_in_output_dir(),
            "downloaded_now_total": downloaded_now_total,
            "recovered_this_phase": 0,
            "total_records": total_to_process,
            "stopped_early": False,
            "resolver_attempts": {},
            "resolver_recovered": {},
            "resolver_duplicates": {},
            "resolver_failed": {},
            "resolver_totals": dict(resolver_totals),
            "resolver_processed": {},
        },
    )

    for task in retry_tasks:
        if stop_event is not None and stop_event.is_set():
            break

        record = task.record
        primary_resolver_name = task.resolver_names[0] if task.resolver_names else "none"
        resolver_attempts[primary_resolver_name] += 1
        resolver_processed[primary_resolver_name] += 1

        if primary_resolver_name != last_emitted_resolver:
            pdfs_in_folder = count_pdf_files_in_output_dir()
            emit(
                reporter,
                "phase2_update",
                {
                    "phase2_pool_total": phase2_pool_total,
                    "retry_processed": retry_processed,
                    "retry_total": retry_total,
                    "unassigned_total": unassigned_total,
                    "phase2_start_time": phase2_start_time,
                    "resolver_name": primary_resolver_name,
                    "last_record_id": phase2_last_record_id,
                    "last_doi": phase2_last_doi,
                    "last_status": phase2_last_status,
                    "last_detail": phase2_last_detail,
                    "pdfs_available_global": pdfs_available_global,
                    "pdfs_in_folder": pdfs_in_folder,
                    "downloaded_now_total": downloaded_now_total,
                    "recovered_this_phase": recovered_this_phase,
                    "total_records": total_to_process,
                    "stopped_early": False,
                    "resolver_attempts": dict(resolver_attempts),
                    "resolver_recovered": dict(resolver_recovered),
                    "resolver_duplicates": dict(resolver_duplicates),
                    "resolver_failed": dict(resolver_failed),
                    "resolver_totals": dict(resolver_totals),
                    "resolver_processed": dict(resolver_processed),
                },
            )
            last_emitted_resolver = primary_resolver_name

        phase2_current_resolver = primary_resolver_name
        phase2_last_record_id = record.record_id
        phase2_last_doi = normalize_doi(record.doi_raw) or normalize_doi(record.doi_link_raw) or ""

        phase1_result = phase1_results_by_row.get(record.row_idx)
        result, used_resolver_name = process_record_phase2(record, task.resolver_names, phase1_result=phase1_result)
        write_result(ws, record.row_idx, col_map, result)
        phase1_results_by_row[record.row_idx] = result

        retry_processed += 1
        phase2_last_status = result.pdf_download_status
        phase2_last_detail = str(result.pdf_checked_at or "")
        phase2_current_resolver = used_resolver_name or primary_resolver_name

        if result.pdf_download_status in SPECIALIZED_DOWNLOADED_NOW_STATUSES:
            downloaded_now_total += 1
            recovered_this_phase += 1
            pdfs_available_global += 1
            resolver_recovered[used_resolver_name or primary_resolver_name] += 1
        elif result.pdf_download_status == "duplicate_pdf":
            resolver_duplicates[used_resolver_name or primary_resolver_name] += 1
        else:
            resolver_failed[used_resolver_name or primary_resolver_name] += 1

        if _should_emit_phase2_progress(retry_processed, retry_total):
            pdfs_in_folder = count_pdf_files_in_output_dir()
            emit(
                reporter,
                "phase2_update",
                {
                    "phase2_pool_total": phase2_pool_total,
                    "retry_processed": retry_processed,
                    "retry_total": retry_total,
                    "unassigned_total": unassigned_total,
                    "phase2_start_time": phase2_start_time,
                    "resolver_name": phase2_current_resolver,
                    "last_record_id": phase2_last_record_id,
                    "last_doi": phase2_last_doi,
                    "last_status": phase2_last_status,
                    "last_detail": phase2_last_detail,
                    "pdfs_available_global": pdfs_available_global,
                    "pdfs_in_folder": pdfs_in_folder,
                    "downloaded_now_total": downloaded_now_total,
                    "recovered_this_phase": recovered_this_phase,
                    "total_records": total_to_process,
                    "stopped_early": False,
                    "resolver_attempts": dict(resolver_attempts),
                    "resolver_recovered": dict(resolver_recovered),
                    "resolver_duplicates": dict(resolver_duplicates),
                    "resolver_failed": dict(resolver_failed),
                    "resolver_totals": dict(resolver_totals),
                    "resolver_processed": dict(resolver_processed),
                },
            )

        if save_callback is not None and retry_processed % SPECIALIZED_SAVE_EVERY_N_ROWS == 0:
            ok, save_path = save_callback(retry_processed)
            emit(
                reporter,
                "save",
                {
                    "phase": 2,
                    "ok": ok,
                    "path": save_path,
                    "processed": retry_processed,
                },
            )

    stopped_early = stop_event is not None and stop_event.is_set()

    phase2_summary = {
        "phase2_pool_total": phase2_pool_total,
        "retry_processed": retry_processed,
        "retry_total": retry_total,
        "unassigned_total": unassigned_total,
        "phase2_start_time": phase2_start_time,
        "resolver_name": phase2_current_resolver if phase2_current_resolver else "finished",
        "last_record_id": phase2_last_record_id,
        "last_doi": phase2_last_doi,
        "last_status": phase2_last_status if phase2_last_status else "finished",
        "last_detail": phase2_last_detail,
        "pdfs_available_global": pdfs_available_global,
        "pdfs_in_folder": count_pdf_files_in_output_dir(),
        "downloaded_now_total": downloaded_now_total,
        "recovered_this_phase": recovered_this_phase,
        "total_records": total_to_process,
        "stopped_early": stopped_early,
        "resolver_attempts": dict(resolver_attempts),
        "resolver_recovered": dict(resolver_recovered),
        "resolver_duplicates": dict(resolver_duplicates),
        "resolver_failed": dict(resolver_failed),
        "resolver_totals": dict(resolver_totals),
        "resolver_processed": dict(resolver_processed),
    }

    emit(reporter, "phase2_end", phase2_summary)
    return phase2_summary


# ============================================================
# LEGACY PUBLIC API
# ============================================================

def run_phase1(
    wb,
    ws,
    col_map,
    records: List[Record],
    output_workbook_path,
    reporter: ReporterType = None,
) -> tuple[Dict[int, DownloadResult], dict]:
    def legacy_save_callback(processed: int) -> Tuple[bool, str]:
        ok = safe_save_workbook(wb, output_workbook_path)
        return ok, str(output_workbook_path)

    phase1_results_by_row, phase1_summary = _run_phase1_core(
        wb=wb,
        ws=ws,
        col_map=col_map,
        records=records,
        reporter=reporter,
        save_callback=legacy_save_callback,
    )

    safe_save_workbook(wb, output_workbook_path)
    return phase1_results_by_row, phase1_summary


def run_phase2(
    wb,
    ws,
    col_map,
    records: List[Record],
    phase1_results_by_row: Dict[int, DownloadResult],
    output_workbook_path,
    phase1_summary: dict,
    reporter: ReporterType = None,
    selected_resolver: Optional[str] = None,
) -> dict:
    def legacy_save_callback(processed: int) -> Tuple[bool, str]:
        ok = safe_save_workbook(wb, output_workbook_path)
        return ok, str(output_workbook_path)

    phase2_summary = _run_phase2_core(
        wb=wb,
        ws=ws,
        col_map=col_map,
        records=records,
        phase1_results_by_row=phase1_results_by_row,
        phase1_summary=phase1_summary,
        reporter=reporter,
        save_callback=legacy_save_callback,
        selected_resolver=selected_resolver,
    )

    safe_save_workbook(wb, output_workbook_path)
    return phase2_summary


def run_full_pipeline(
    wb,
    ws,
    col_map,
    records: List[Record],
    output_workbook_path,
    reporter: ReporterType = None,
) -> dict:
    phase1_results_by_row, phase1_summary = run_phase1(
        wb=wb,
        ws=ws,
        col_map=col_map,
        records=records,
        output_workbook_path=output_workbook_path,
        reporter=reporter,
    )

    phase2_summary = run_phase2(
        wb=wb,
        ws=ws,
        col_map=col_map,
        records=records,
        phase1_results_by_row=phase1_results_by_row,
        output_workbook_path=output_workbook_path,
        phase1_summary=phase1_summary,
        reporter=reporter,
    )

    final_summary = {
        "phase1": phase1_summary,
        "phase2": phase2_summary,
        "output_workbook_path": str(output_workbook_path),
    }

    emit(reporter, "finish", final_summary)
    return final_summary


# ============================================================
# SESSION-BASED API
# ============================================================

def run_phase1_for_session(
    session_state: SessionState,
    reporter: ReporterType = None,
    stop_event: StopEventType = None,
) -> tuple[Dict[int, DownloadResult], dict]:
    if not session_state.is_workbook_loaded:
        raise ValueError("SessionState workbook is not loaded.")

    session_state.current_phase = "phase1"

    def session_save_callback(processed: int) -> Tuple[bool, str]:
        checkpoint_path = save_session_checkpoint(
            session_state,
            label=f"phase1_checkpoint_{processed}",
            timestamp=session_state.timestamp or None,
        )
        return checkpoint_path is not None, str(checkpoint_path or "")

    phase1_results_by_row, phase1_summary = _run_phase1_core(
        wb=session_state.workbook,
        ws=session_state.worksheet,
        col_map=session_state.col_map,
        records=session_state.records,
        reporter=reporter,
        save_callback=session_save_callback,
        stop_event=stop_event,
    )

    session_state.phase1_summary = Phase1Summary(
        total_records_considered=phase1_summary["total"],
        total_available_before=0,
        total_downloaded_now=phase1_summary["downloaded_now_total"],
        total_failed=max(0, phase1_summary["processed"] - phase1_summary["pdfs_available_global"]),
        total_skipped=0,
    )

    return phase1_results_by_row, phase1_summary


def run_phase2_for_session(
    session_state: SessionState,
    phase1_results_by_row: Dict[int, DownloadResult],
    phase1_summary: dict,
    reporter: ReporterType = None,
    stop_event: StopEventType = None,
    selected_resolver: Optional[str] = None,
) -> dict:
    if not session_state.is_workbook_loaded:
        raise ValueError("SessionState workbook is not loaded.")

    session_state.current_phase = "phase2"
    session_state.retry_tasks = build_retry_tasks(
        session_state.records,
        phase1_results_by_row,
        selected_resolver=selected_resolver,
    )

    def session_save_callback(processed: int) -> Tuple[bool, str]:
        checkpoint_path = save_session_checkpoint(
            session_state,
            label=f"phase2_checkpoint_{processed}",
            timestamp=session_state.timestamp or None,
        )
        return checkpoint_path is not None, str(checkpoint_path or "")

    phase2_summary = _run_phase2_core(
        wb=session_state.workbook,
        ws=session_state.worksheet,
        col_map=session_state.col_map,
        records=session_state.records,
        phase1_results_by_row=phase1_results_by_row,
        phase1_summary=phase1_summary,
        reporter=reporter,
        save_callback=session_save_callback,
        stop_event=stop_event,
        selected_resolver=selected_resolver,
    )

    session_state.phase2_summary = Phase2Summary(
        total_retry_candidates=phase2_summary["retry_total"],
        total_recovered_now=phase2_summary["recovered_this_phase"],
        total_failed=max(0, phase2_summary["retry_processed"] - phase2_summary["recovered_this_phase"]),
        total_skipped=0,
    )

    return phase2_summary


def run_full_pipeline_for_session(
    session_state: SessionState,
    reporter: ReporterType = None,
    save_final: bool = True,
) -> dict:
    phase1_results_by_row, phase1_summary = run_phase1_for_session(
        session_state=session_state,
        reporter=reporter,
    )

    phase2_summary = run_phase2_for_session(
        session_state=session_state,
        phase1_results_by_row=phase1_results_by_row,
        phase1_summary=phase1_summary,
        reporter=reporter,
    )

    final_path = None
    if save_final:
        final_path = save_final_workbook(
            session_state=session_state,
            timestamp=session_state.timestamp or None,
        )

    final_summary = {
        "phase1": phase1_summary,
        "phase2": phase2_summary,
        "output_workbook_path": str(final_path) if final_path else "",
    }

    emit(reporter, "finish", final_summary)
    return final_summary


# ============================================================
# PHASE 0 / DIAGNOSTICS HOOKS
# ============================================================

def run_phase0_doi_enrichment_for_session(
    session_state: SessionState,
    reporter: ReporterType = None,
    generate_report: bool = False,
    stop_event: StopEventType = None,
):
    try:
        module = importlib.import_module("tools.pdf_fetcher.core.doi_enrichment")
    except Exception as exc:
        raise NotImplementedError(
            "Phase 0 DOI enrichment is not wired yet."
        ) from exc

    run_fn = getattr(module, "run_phase0_doi_enrichment_for_session", None)
    if not callable(run_fn):
        raise NotImplementedError(
            "tools.pdf_fetcher.core.doi_enrichment does not expose "
            "'run_phase0_doi_enrichment_for_session'."
        )

    return _call_with_optional_stop_event(
        run_fn,
        session_state=session_state,
        reporter=reporter,
        generate_report=generate_report,
        stop_event=stop_event,
    )


def run_diagnostic_for_session(
    session_state: SessionState,
    diagnostic_label: str,
    reporter: ReporterType = None,
    stop_event: StopEventType = None,
):
    module = importlib.import_module("tools.pdf_fetcher.core.diagnostics")
    run_fn = getattr(module, "run_diagnostic_for_session", None)

    if not callable(run_fn):
        raise RuntimeError(
            "tools.pdf_fetcher.core.diagnostics does not expose 'run_diagnostic_for_session'."
        )

    return _call_with_optional_stop_event(
        run_fn,
        session_state=session_state,
        diagnostic_label=diagnostic_label,
        reporter=reporter,
        stop_event=stop_event,
    )
