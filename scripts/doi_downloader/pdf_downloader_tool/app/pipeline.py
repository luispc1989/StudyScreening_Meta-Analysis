from __future__ import annotations

import importlib
import inspect
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from typing import Callable, Dict, List, Optional, Tuple

from app.config import (
    BASE_AVAILABLE_STATUSES,
    BASE_DOWNLOADED_NOW_STATUSES,
    ENABLE_SPECIALIZED_RESOLVERS,
    MAX_WORKERS,
    REFRESH_DASHBOARD_EVERY_N_COMPLETIONS,
    SAVE_EVERY_N_ROWS,
    SLEEP_BETWEEN_REQUESTS,
    SPECIALIZED_DOWNLOADED_NOW_STATUSES,
    SPECIALIZED_SAVE_EVERY_N_ROWS,
)
from app.excel_io import safe_save_workbook, save_final_workbook, save_session_checkpoint, write_result
from app.models import (
    DownloadResult,
    Phase1Summary,
    Phase2Summary,
    Record,
    RetryTask,
    SessionState,
)
from app.resolver_detector import detect_specialized_resolver_name, should_retry_in_phase2
from app.utils import normalize_doi
from resolvers.base_download import process_record_phase1


ReporterType = Optional[Callable[[str, dict], None]]
SaveCallbackType = Optional[Callable[[int], Tuple[bool, str]]]
StopEventType = Optional[threading.Event]


def emit(reporter: ReporterType, event_name: str, payload: dict) -> None:
    if reporter is None:
        return
    reporter(event_name, payload)


def _resolve_specialized_resolver_callable(resolver_name: str):
    resolver_specs = {
        "frontiers": ("resolvers.frontiers", ("try_frontiers_resolver",)),
        "mdpi": ("resolvers.mdpi", ("try_mdpi_resolver",)),
        "springer": ("resolvers.springer", ("try_springer_resolver",)),
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
) -> List[RetryTask]:
    tasks: List[RetryTask] = []

    if not ENABLE_SPECIALIZED_RESOLVERS:
        return tasks

    for record in records:
        phase1_result = phase1_results_by_row.get(record.row_idx)
        if phase1_result is None:
            continue

        if not should_retry_in_phase2(phase1_result):
            continue

        resolver_name = detect_specialized_resolver_name(record, phase1_result)
        if resolver_name is None:
            continue

        tasks.append(RetryTask(record=record, resolver_name=resolver_name))

    return tasks


def process_record_phase2(record: Record, resolver_name: str) -> DownloadResult:
    resolver_fn = _resolve_specialized_resolver_callable(resolver_name)

    if resolver_fn is not None:
        try:
            return resolver_fn(record)
        except Exception:
            pass

    return DownloadResult(
        pdf_downloaded=0,
        pdf_download_status="unsupported_specialized_resolver",
        pdf_file_name=record.file_name,
        pdf_source_url="",
        pdf_local_path="",
        pdf_http_status=None,
        pdf_checked_at=time.strftime("%Y-%m-%d %H:%M:%S"),
    )


def _should_emit_progress(processed: int, total: int) -> bool:
    if processed == 1:
        return True
    if processed == total:
        return True
    if processed % REFRESH_DASHBOARD_EVERY_N_COMPLETIONS == 0:
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
) -> dict:
    total_to_process = len(records)
    retry_tasks = build_retry_tasks(records, phase1_results_by_row)
    retry_total = len(retry_tasks)

    pdfs_available_global = phase1_summary["pdfs_available_global"]
    downloaded_now_total = phase1_summary["downloaded_now_total"]

    if retry_total == 0:
        payload = {
            "retry_processed": 0,
            "retry_total": 0,
            "phase2_start_time": time.time(),
            "resolver_name": "none",
            "last_record_id": "",
            "last_doi": "",
            "last_status": "no_retry_tasks",
            "pdfs_available_global": pdfs_available_global,
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
    phase2_current_resolver = "starting"

    emit(
        reporter,
        "phase2_start",
        {
            "retry_processed": 0,
            "retry_total": retry_total,
            "phase2_start_time": phase2_start_time,
            "resolver_name": phase2_current_resolver,
            "last_record_id": "",
            "last_doi": "",
            "last_status": "starting",
            "pdfs_available_global": pdfs_available_global,
            "downloaded_now_total": downloaded_now_total,
            "recovered_this_phase": 0,
            "total_records": total_to_process,
            "stopped_early": False,
        },
    )

    for task in retry_tasks:
        if stop_event is not None and stop_event.is_set():
            break

        record = task.record
        resolver_name = task.resolver_name

        phase2_current_resolver = resolver_name
        phase2_last_record_id = record.record_id
        phase2_last_doi = normalize_doi(record.doi_raw) or normalize_doi(record.doi_link_raw) or ""

        result = process_record_phase2(record, resolver_name)
        write_result(ws, record.row_idx, col_map, result)
        phase1_results_by_row[record.row_idx] = result

        retry_processed += 1
        phase2_last_status = result.pdf_download_status

        if result.pdf_download_status in SPECIALIZED_DOWNLOADED_NOW_STATUSES:
            downloaded_now_total += 1
            recovered_this_phase += 1
            pdfs_available_global += 1
        elif result.pdf_download_status == "duplicate_pdf":
            pdfs_available_global += 1

        if _should_emit_progress(retry_processed, retry_total):
            emit(
                reporter,
                "phase2_update",
                {
                    "retry_processed": retry_processed,
                    "retry_total": retry_total,
                    "phase2_start_time": phase2_start_time,
                    "resolver_name": phase2_current_resolver,
                    "last_record_id": phase2_last_record_id,
                    "last_doi": phase2_last_doi,
                    "last_status": phase2_last_status,
                    "pdfs_available_global": pdfs_available_global,
                    "downloaded_now_total": downloaded_now_total,
                    "recovered_this_phase": recovered_this_phase,
                    "total_records": total_to_process,
                    "stopped_early": False,
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
        "retry_processed": retry_processed,
        "retry_total": retry_total,
        "phase2_start_time": phase2_start_time,
        "resolver_name": phase2_current_resolver if phase2_current_resolver else "finished",
        "last_record_id": phase2_last_record_id,
        "last_doi": phase2_last_doi,
        "last_status": phase2_last_status if phase2_last_status else "finished",
        "pdfs_available_global": pdfs_available_global,
        "downloaded_now_total": downloaded_now_total,
        "recovered_this_phase": recovered_this_phase,
        "total_records": total_to_process,
        "stopped_early": stopped_early,
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
) -> dict:
    if not session_state.is_workbook_loaded:
        raise ValueError("SessionState workbook is not loaded.")

    session_state.current_phase = "phase2"
    session_state.retry_tasks = build_retry_tasks(session_state.records, phase1_results_by_row)

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
        module = importlib.import_module("app.doi_enrichment")
    except Exception as exc:
        raise NotImplementedError(
            "Phase 0 DOI enrichment is not wired yet."
        ) from exc

    run_fn = getattr(module, "run_phase0_doi_enrichment_for_session", None)
    if not callable(run_fn):
        raise NotImplementedError(
            "app.doi_enrichment does not expose "
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
    module = importlib.import_module("app.diagnostics")
    run_fn = getattr(module, "run_diagnostic_for_session", None)

    if not callable(run_fn):
        raise RuntimeError(
            "app.diagnostics does not expose 'run_diagnostic_for_session'."
        )

    return _call_with_optional_stop_event(
        run_fn,
        session_state=session_state,
        diagnostic_label=diagnostic_label,
        reporter=reporter,
        stop_event=stop_event,
    )
