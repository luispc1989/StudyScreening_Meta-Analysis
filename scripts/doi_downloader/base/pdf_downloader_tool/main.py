
from __future__ import annotations

from app.config import (
    MAX_ROWS_TO_PROCESS,
    PDF_BASE_DIR,
    SHEET_NAME,
    build_output_workbook_path,
    resolve_workbook_path,
)
from app.excel_io import (
    build_col_map,
    collect_records,
    load_workbook_and_sheet,
    safe_save_workbook,
    validate_required_columns,
)
from app.pipeline import run_full_pipeline
from ui.terminal_dashboard import TerminalDashboard


def main() -> None:
    dashboard = TerminalDashboard()
    dashboard.init_terminal_mode()

    workbook_path = resolve_workbook_path()
    output_workbook_path = build_output_workbook_path(workbook_path)

    PDF_BASE_DIR.mkdir(parents=True, exist_ok=True)

    wb, ws = load_workbook_and_sheet(workbook_path, SHEET_NAME)
    col_map = build_col_map(ws)
    validate_required_columns(col_map, SHEET_NAME)

    records = collect_records(ws, col_map, MAX_ROWS_TO_PROCESS)

    if not records:
        raise ValueError("No records found to process.")

    try:
        final_summary = run_full_pipeline(
            wb=wb,
            ws=ws,
            col_map=col_map,
            records=records,
            output_workbook_path=output_workbook_path,
            reporter=dashboard.handle_event,
        )

        phase2 = final_summary["phase2"]

        print()
        print(f"PDFs disponíveis        : {phase2['pdfs_available_global']}")
        print(f"PDFs descarregados agora: {phase2['downloaded_now_total']}")
        print(f"Saved workbook          : {output_workbook_path}")
        print(f"PDF folder              : {PDF_BASE_DIR}")

    except KeyboardInterrupt:
        print("\nInterrupção pedida. A guardar progresso...")

        ok = safe_save_workbook(wb, output_workbook_path)
        if ok:
            print("Progresso guardado com sucesso.")
        else:
            print("Não foi possível guardar o workbook de forma segura.")

        print(f"Saved workbook          : {output_workbook_path}")

    except Exception as exc:
        print(f"\nErro: {exc}")
        ok = safe_save_workbook(wb, output_workbook_path)
        if ok:
            print("Progresso parcial guardado.")
        else:
            print("Não foi possível guardar o workbook após erro.")


if __name__ == "__main__":
    main()