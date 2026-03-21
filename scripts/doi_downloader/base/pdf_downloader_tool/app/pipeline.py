
from __future__ import annotations

import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from typing import Callable, Dict, List, Optional

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
from app.excel_io import safe_save_workbook, write_result
from app.models import DownloadResult, Record, RetryTask
from app.resolver_detector import detect_specialized_resolver_name, should_retry_in_phase2
from app.utils import normalize_doi
from resolvers.base_download import process_record_phase1
from resolvers.frontiers import try_frontiers_resolver


ReporterType = Optional[Callable[[str, dict], None]]


def emit(reporter: ReporterType, event_name: str, payload: dict) -> None:
    """
    Send an event to the optional reporter callback.
    """
    if reporter is None:
        return
    reporter(event_name, payload)


def build_retry_tasks(
    records: List[Record],
    phase1_results_by_row: Dict[int, DownloadResult],
) -> List[RetryTask]:
    """
    Build the phase 2 retry task list.
    """
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
    """
    Dispatch phase 2 processing to the correct specialized resolver.
    """
    if resolver_name == "frontiers":
        return try_frontiers_resolver(record)

    return DownloadResult(
        pdf_downloaded=0,
        pdf_download_status="unsupported_specialized_resolver",
        pdf_file_name=record.file_name,
        pdf_source_url="",
        pdf_local_path="",
        pdf_http_status=None,
        pdf_checked_at=time.strftime("%Y-%m-%d %H:%M:%S"),
    )


def run_phase1(
    wb,
    ws,
    col_map,
    records: List[Record],
    output_workbook_path,
    reporter: ReporterType = None,
) -> tuple[Dict[int, DownloadResult], dict]:
    """
    Run phase 1 in parallel using the base download resolver.
    """
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

                if (
                    phase1_processed == 1
                    or phase1_processed % REFRESH_DASHBOARD_EVERY_N_COMPLETIONS == 0
                    or phase1_processed == total_to_process
                ):
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

                if phase1_processed % SAVE_EVERY_N_ROWS == 0:
                    ok = safe_save_workbook(wb, output_workbook_path)
                    emit(
                        reporter,
                        "save",
                        {
                            "phase": 1,
                            "ok": ok,
                            "path": str(output_workbook_path),
                            "processed": phase1_processed,
                        },
                    )

                while next_idx < total_to_process and len(futures) < MAX_WORKERS:
                    next_record = records[next_idx]
                    futures[executor.submit(process_record_phase1, next_record)] = next_record
                    next_idx += 1

                    if SLEEP_BETWEEN_REQUESTS > 0:
                        time.sleep(SLEEP_BETWEEN_REQUESTS)

        safe_save_workbook(wb, output_workbook_path)

        phase1_summary = {
            "processed": phase1_processed,
            "total": total_to_process,
            "workers": MAX_WORKERS,
            "start_time": phase1_start_time,
            "last_record_id": phase1_last_record_id,
            "last_status": phase1_last_status,
            "pdfs_available_global": pdfs_available_global,
            "downloaded_now_total": downloaded_now_total,
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
    """
    Run phase 2 sequentially using specialized resolvers.
    """
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
        },
    )

    for task in retry_tasks:
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

        if (
            retry_processed == 1
            or retry_processed % REFRESH_DASHBOARD_EVERY_N_COMPLETIONS == 0
            or retry_processed == retry_total
        ):
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
                },
            )

        if retry_processed % SPECIALIZED_SAVE_EVERY_N_ROWS == 0:
            ok = safe_save_workbook(wb, output_workbook_path)
            emit(
                reporter,
                "save",
                {
                    "phase": 2,
                    "ok": ok,
                    "path": str(output_workbook_path),
                    "processed": retry_processed,
                },
            )

    safe_save_workbook(wb, output_workbook_path)

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
    }

    emit(reporter, "phase2_end", phase2_summary)
    return phase2_summary


def run_full_pipeline(
    wb,
    ws,
    col_map,
    records: List[Record],
    output_workbook_path,
    reporter: ReporterType = None,
) -> dict:
    """
    Run the full pipeline:
    - phase 1
    - phase 2
    - return final summaries
    """
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