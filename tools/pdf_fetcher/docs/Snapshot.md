# PDF Downloader Tool — Project Snapshot v6 SFF

## Nota de integridade

Este snapshot é a **base operacional atual e autoritativa** do projeto, consolidada a partir do snapshot v5 e das correções mais recentes feitas neste chat.

Inclui:
- contexto funcional do projeto;
- arquitetura e navegação atual da app;
- histórico técnico resumido do que foi corrigido;
- ponto de situação real no fim desta conversa;
- **scripts completos** dos ficheiros relevantes incluídos no snapshot anterior, com substituição pelas versões mais recentes dos ficheiros que foram atualizados neste chat.

Este documento deve ser tratado como o **snapshot de handoff** para abrir um novo chat e continuar o trabalho sem perder contexto.

## Objetivo funcional da app

A app serve para apoiar o workflow de download e diagnóstico de PDFs na pipeline de study screening / meta-analysis, sobre a sheet principal `wos_full_text`, com lógica por fases:

- **Fase 0 - DOI Enrichment**
  - identifica registos elegíveis sem DOI útil;
  - tenta enriquecer `DOI` e `DOI Link`;
  - atualiza apenas essas colunas no workbook principal;
  - pode gerar report separado da fase 0.

- **Fase 1 - PDF Basic Download**
  - executa o download base / diagnóstico principal dos PDFs;
  - atualiza colunas de resultado do workbook em memória;
  - alimenta a fase 2.

- **Fase 2 - PDF Specialized Download**
  - corre apenas sobre candidatos de retry derivados da fase 1;
  - usa resolvers especializados;
  - continua dependente da fase 1.

Além disso, existem diagnósticos:
- **diagnóstico inicial**;
- **diagnóstico fase 0**;
- **diagnóstico fase 1**;
- **diagnóstico fase 2**.

## Ponto de situação atual

Estado funcional consolidado no fim desta conversa:

- o menu inicial passa a ter:
  - `[1] Começar pela fase 0 - DOI Enrichment`
  - `[2] Começar pela fase 1 - PDF Basic Download`
  - `[3] Realizar diagnóstico inicial`
  - `[4] Sair`
- a **fase 0 é opcional**;
- a **fase 1 pode arrancar diretamente** a partir do menu inicial;
- a **fase 2 continua sempre dependente da fase 1**;
- os menus finais das fases foram reestruturados com nomes explícitos das fases;
- a fase 1 passa a ter opção explícita para **voltar à fase 0**;
- a fase 2 passa a ter opção explícita para **voltar à fase 1**;
- durante execução de **fases e diagnósticos**, a barra de controlos deve suportar:
  - `P` -> abrir menu de pausa;
  - `V` -> voltar diretamente ao menu anterior;
  - `S` -> sair da app com checkpoint;
- o menu de pausa deve suportar:
  - continuar;
  - voltar ao menu anterior;
  - sair da app;
- a cadeia `main.py -> app/pipeline.py -> app/doi_enrichment.py` foi alinhada para `stop_event`;
- a cadeia `main.py -> app/pipeline.py -> app/diagnostics.py` foi alinhada para `stop_event`;
- os diagnósticos deixaram de correr fora do mecanismo central de controlo e passaram a ser compatíveis com a mesma lógica de pausa / back / quit;
- o snapshot inclui também a versão atual de `app/diagnostics.py`, agora preparada para paragem controlada.

## Bugs resolvidos nesta fase do projeto

### 1) Incompatibilidade `stop_event` na fase 0
Erro observado:
- `run_phase0_doi_enrichment_for_session() got an unexpected keyword argument 'stop_event'`

Causa real:
- `main.py` já passava `stop_event`;
- `app/doi_enrichment.py` já aceitava `stop_event`;
- o wrapper intermédio em `app/pipeline.py` ainda estava com a assinatura antiga.

Correção aplicada:
- `app/pipeline.py` passou a aceitar e reencaminhar `stop_event` na fase 0.

### 2) Voltar ao menu anterior fazia sair da app
Causa real:
- havia `return` / `break` encadeados no `main.py` que faziam a navegação regressar até ao topo e encerrar a app.

Correção aplicada:
- a navegação foi reestruturada para que “voltar” apenas regresse ao menu certo, sem encerrar a app.

### 3) `P`, `V` e `S` tinham o mesmo comportamento efetivo
Causa real:
- qualquer `stop_reason` disparava sempre o mesmo handler de pausa.

Correção aplicada:
- a lógica passou a distinguir corretamente:
  - `pause`;
  - `back`;
  - `quit`.

### 4) Menu inicial do dashboard e lógica do `main.py` estavam desalinhados
Causa real:
- o `ui/terminal_dashboard.py` foi atualizado primeiro para 4 opções, mas o `main.py` ainda tratava o menu antigo de 3 opções.

Correção aplicada:
- o `main.py` foi alinhado com o novo menu inicial.

### 5) Diagnósticos não aceitavam controlo por teclado
Causa real:
- o diagnóstico corria fora do `_run_phase_with_controls(...)`;
- `app/pipeline.py` ainda não propagava `stop_event` ao diagnóstico;
- `app/diagnostics.py` lançava todos os futures sem gestão de paragem controlada.

Correção aplicada:
- os diagnósticos passaram a correr pelo mesmo mecanismo central de controlo das fases;
- `pipeline.py` passou a encaminhar `stop_event` ao diagnóstico;
- `diagnostics.py` foi adaptado para aceitar `stop_event` e parar de forma controlada.

## Estado de validação neste handoff

O que foi validado neste chat:
- coerência arquitetural e de navegação;
- sintaxe Python dos ficheiros atualizados;
- alinhamento entre assinaturas e chamadas de função.

O que ainda deve ser validado no repositório local real:
- substituição efetiva dos ficheiros no disco;
- execução end-to-end do fluxo completo em terminal;
- verificação manual destes percursos:
  - menu inicial -> fase 0;
  - menu inicial -> fase 1;
  - menu inicial -> diagnóstico inicial;
  - fase 1 -> voltar à fase 0;
  - fase 2 -> voltar à fase 1;
  - diagnósticos -> `P`, `V`, `S`.

## Próximo passo recomendado

O próximo passo técnico recomendado já não é redesenhar menus; é **bloco de robustez e validação**:

- validar todos os percursos em runtime no projeto real;
- garantir que o repositório local contém exatamente estas versões dos ficheiros atualizados;
- testar checkpoints, save intermédio e saída controlada;
- confirmar que a renderização final no terminal está limpa em Git Bash / PowerShell / cmd;
- depois disso, avançar para reforço de robustez, validação e novos resolvers.

## Instruções para um novo chat

Se este snapshot for colocado noutro chat, o novo chat deve assumir o seguinte:

1. Este documento é a referência atual do projeto.
2. As versões dos scripts incluídas aqui são a base autoritativa.
3. Quando devolver atualizações de código, deve devolver **sempre o script completo**, não patches parciais.
4. O foco imediato deve ser:
   - validar a app no repositório local real;
   - corrigir divergências entre ficheiros reais e snapshot;
   - continuar o bloco de robustez e validação.
5. Em caso de bug novo, o novo chat deve primeiro confirmar se o problema está:
   - na navegação (`main.py`);
   - na mediação (`app/pipeline.py`);
   - no módulo da fase/diagnóstico;
   - ou no `ui/terminal_dashboard.py`.

---

# Scripts incluídos neste snapshot


## 1) `app/config.py`

```python
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

EXTERNAL_WOS_DIR = Path(
    r"C:\Users\Luís Pinto Coelho\Desktop\Dissertação\metanalysis development\2 - literature search & study screening\data\wos"
)

EXCEL_INPUT_DIR = EXTERNAL_WOS_DIR / "excel_files"
PDF_BASE_DIR = EXTERNAL_WOS_DIR / "pdf_files"

APP_OUTPUTS_DIR = Path(
    r"C:\Users\Luís Pinto Coelho\Desktop\Dissertação\metanalysis development\2 - literature search & study screening\data\wos\excel_files\app_outputs"
)
REPORTS_OUTPUT_DIR = APP_OUTPUTS_DIR / "reports"
FINAL_OUTPUT_DIR = APP_OUTPUTS_DIR / "final"
TEMP_OUTPUT_DIR = APP_OUTPUTS_DIR / "temp"

PREFERRED_WORKBOOK_PATH = EXCEL_INPUT_DIR / "wos_workbook_03.03.2026_v2.xlsx"

OUTPUT_WORKBOOK_SUFFIX = "_pdf_downloaded.xlsx"
SHEET_NAME = "wos_full_text"

ENABLE_DOI_ENRICHMENT = True
DOI_MAX_ROWS_TO_PROCESS: Optional[int] = None
DOI_MIN_TITLE_SIMILARITY = 0.88
DOI_MIN_CONFIDENCE_SCORE = 75.0
DOI_OVERWRITE_EXISTING = False
DOI_CONNECT_TIMEOUT = 10
DOI_READ_TIMEOUT = 25
DOI_REQUEST_TIMEOUT = (DOI_CONNECT_TIMEOUT, DOI_READ_TIMEOUT)
DOI_SLEEP_BETWEEN_REQUESTS = 0.20
DOI_CROSSREF_MAILTO = ""
DOI_GENERATE_REPORT_BY_DEFAULT = False
DOI_REQUIRED_INPUT_COLUMNS = [
    "record_id", "Authors", "Publication Year", "Title", "DOI", "DOI Link"
]
DOI_REPORT_MAIN_SHEET_NAME = SHEET_NAME
DOI_REPORT_STATS_SHEET_NAME = "doi_stats"
DOI_REPORT_ALL_PROCESSED_SHEET_NAME = "doi_all_processed"
DOI_REPORT_ENRICHED_SHEET_NAME = "doi_enriched"
DOI_REPORT_UNRESOLVED_SHEET_NAME = "doi_unresolved"

MAX_WORKERS = 4
CONNECT_TIMEOUT = 8
READ_TIMEOUT = 15
SLEEP_BETWEEN_REQUESTS = 0.05
MAX_ROWS_TO_PROCESS: Optional[int] = None

ENABLE_BENCHMARK_MODE = False
BENCHMARK_RECORD_IDS: set[str] = set()

SAVE_EVERY_N_ROWS = 100
SPECIALIZED_SAVE_EVERY_N_ROWS = 10

REFRESH_DASHBOARD_EVERY_N_COMPLETIONS = 10
FORCE_SIMPLE_TERMINAL = False

ENABLE_SPECIALIZED_RESOLVERS = True
ENABLE_FRONTIERS_RESOLVER = True
ENABLE_MDPI_RESOLVER = True
ENABLE_SPRINGER_RESOLVER = True

FRONTIERS_HEADLESS = False
FRONTIERS_NAVIGATION_TIMEOUT_MS = 30000
FRONTIERS_DOWNLOAD_TIMEOUT_MS = 40000
FRONTIERS_POST_LOAD_WAIT_MS = 1000
FRONTIERS_ALLOWED_DOMAIN_PATTERN = r"(^|\.)frontiersin\.org$"

MDPI_HEADLESS = False
MDPI_NAVIGATION_TIMEOUT_MS = 30000
MDPI_DOWNLOAD_TIMEOUT_MS = 40000
MDPI_POST_LOAD_WAIT_MS = 1000
MDPI_ALLOWED_DOMAIN_PATTERN = r"(^|\.)mdpi\.com$"

SPRINGER_HEADLESS = False
SPRINGER_NAVIGATION_TIMEOUT_MS = 30000
SPRINGER_DOWNLOAD_TIMEOUT_MS = 40000
SPRINGER_POST_LOAD_WAIT_MS = 1000
SPRINGER_ALLOWED_DOMAIN_PATTERN = r"(^|\.)springer\.com$|(^|\.)link\.springer\.com$"

ENABLE_DIAGNOSTICS = True
DIAGNOSTIC_CONNECT_TIMEOUT = 5
DIAGNOSTIC_READ_TIMEOUT = 10
DIAGNOSTIC_REQUEST_TIMEOUT = (DIAGNOSTIC_CONNECT_TIMEOUT, DIAGNOSTIC_READ_TIMEOUT)
DIAGNOSTIC_MAX_WORKERS = 12
DIAGNOSTIC_MAX_ROWS_TO_PROCESS: Optional[int] = None
DIAGNOSTIC_PROGRESS_REFRESH_EVERY_N = 20
DIAGNOSTIC_PROGRESS_REFRESH_EVERY_SECONDS = 1.5
DIAGNOSTIC_OUTPUT_SHEET_NAME = SHEET_NAME
DIAGNOSTIC_STATS_SHEET_NAME = "pdf_error_stats"
DIAGNOSTIC_REQUIRED_INPUT_COLUMNS_INITIAL = [
    "record_id", "source", "Authors", "Publication Year", "Title", "Abstract",
    "Author Keywords", "Source Title", "Volume", "Issue", "Begin Page", "End Page",
    "E-mail Address", "DOI", "DOI Link"
]
DIAGNOSTIC_REQUIRED_INPUT_COLUMNS_SESSION = [
    "record_id", "Authors", "Title", "DOI", "DOI Link", "pdf_download_status"
]
DIAGNOSTIC_OUTPUT_COLUMNS = [
    "record_id", "Authors", "Title", "DOI", "DOI Link",
    "pdf_download_status", "pdf_source_url", "pdf_http_status"
]
DIAGNOSTIC_ERROR_TAB_COLUMNS = DIAGNOSTIC_OUTPUT_COLUMNS
DIAGNOSTIC_EXCLUDED_FROM_ERROR_RANKING = {"downloaded", "", None}

REPORT_NAME_DIAGNOSTICO_INICIAL = "diagnostico_inicial"
REPORT_NAME_FASE0_DOI = "fase0_doi"
REPORT_NAME_DIAGNOSTICO_FASE0 = "diagnostico_fase0"
REPORT_NAME_DIAGNOSTICO_FASE1 = "diagnostico_fase1"
REPORT_NAME_DIAGNOSTICO_FASE2 = "diagnostico_fase2"
FINAL_WORKBOOK_NAME = "workbook_final"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "application/pdf,*/*;q=0.8"
    ),
}

REQUIRED_INPUT_COLUMNS = ["record_id", "Title", "DOI", "DOI Link"]
REQUIRED_OUTPUT_COLUMNS = [
    "pdf_downloaded", "pdf_download_status", "pdf_file_name", "pdf_source_url",
    "pdf_local_path", "pdf_http_status", "pdf_checked_at"
]
REQUIRED_COLUMNS = REQUIRED_INPUT_COLUMNS + REQUIRED_OUTPUT_COLUMNS

BASE_AVAILABLE_STATUSES = {"downloaded", "duplicate_pdf"}
BASE_DOWNLOADED_NOW_STATUSES = {"downloaded"}
SPECIALIZED_DOWNLOADED_NOW_STATUSES = {
    "downloaded_frontiers", "downloaded_mdpi", "downloaded_springer"
}

FRAME_WIDTH = 78


def resolve_workbook_path() -> Path:
    if PREFERRED_WORKBOOK_PATH.exists():
        return PREFERRED_WORKBOOK_PATH

    candidates = sorted(
        [p for p in EXCEL_INPUT_DIR.glob("*.xlsx") if not p.name.startswith("~$")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(f"No .xlsx workbook found in: {EXCEL_INPUT_DIR}")
    return candidates[0]


def ensure_output_directories() -> None:
    REPORTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def build_output_workbook_path(workbook_path: Path) -> Path:
    return EXCEL_INPUT_DIR / f"{workbook_path.stem}{OUTPUT_WORKBOOK_SUFFIX}"


def build_final_workbook_path(timestamp: Optional[str] = None) -> Path:
    ensure_output_directories()
    ts = timestamp or build_timestamp()
    return FINAL_OUTPUT_DIR / f"{FINAL_WORKBOOK_NAME}_{ts}.xlsx"


def build_report_output_path(report_prefix: str, timestamp: Optional[str] = None) -> Path:
    ensure_output_directories()
    ts = timestamp or build_timestamp()
    return REPORTS_OUTPUT_DIR / f"{report_prefix}_{ts}.xlsx"


def build_temp_workbook_path(label: str, timestamp: Optional[str] = None) -> Path:
    ensure_output_directories()
    ts = timestamp or build_timestamp()
    safe_label = str(label).strip().replace(" ", "_")
    return TEMP_OUTPUT_DIR / f"{safe_label}_{ts}.xlsx"
```

## 2) `app/models.py`

```python
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

@dataclass
class Record:
    row_idx: int
    record_id: str
    title: str
    doi_raw: str
    doi_link_raw: str
    file_name: str
    pdf_path: Path
    relative_path: str

@dataclass
class DownloadResult:
    pdf_downloaded: int
    pdf_download_status: str
    pdf_file_name: str
    pdf_source_url: str
    pdf_local_path: str
    pdf_http_status: Optional[int]
    pdf_checked_at: str

@dataclass
class RetryTask:
    record: Record
    resolver_name: str

@dataclass
class Phase0Summary:
    total_rows_read: int = 0
    total_existing_doi: int = 0
    total_missing_doi: int = 0
    total_eligible: int = 0
    total_skipped_missing_title: int = 0
    total_skipped_already_downloaded: int = 0
    total_enriched: int = 0
    total_unresolved: int = 0
    total_errors: int = 0
    report_path: Optional[Path] = None

@dataclass
class Phase1Summary:
    total_records_considered: int = 0
    total_available_before: int = 0
    total_downloaded_now: int = 0
    total_failed: int = 0
    total_skipped: int = 0

@dataclass
class Phase2Summary:
    total_retry_candidates: int = 0
    total_recovered_now: int = 0
    total_failed: int = 0
    total_skipped: int = 0

@dataclass
class DiagnosticSummary:
    diagnostic_label: str = ""
    total_rows_considered: int = 0
    total_rows_diagnosed: int = 0
    total_downloaded: int = 0
    total_errors: int = 0
    report_path: Optional[Path] = None

@dataclass
class SessionState:
    workbook_path: Path
    sheet_name: str
    workbook: Optional[Any] = None
    worksheet: Optional[Any] = None
    col_map: dict[str, int] = field(default_factory=dict)
    records: list[Record] = field(default_factory=list)
    retry_tasks: list[RetryTask] = field(default_factory=list)
    current_phase: str = "initial"
    timestamp: str = ""
    phase0_summary: Phase0Summary = field(default_factory=Phase0Summary)
    phase1_summary: Phase1Summary = field(default_factory=Phase1Summary)
    phase2_summary: Phase2Summary = field(default_factory=Phase2Summary)
    diagnostics_history: list[DiagnosticSummary] = field(default_factory=list)
    generated_report_paths: list[Path] = field(default_factory=list)
    final_workbook_path: Optional[Path] = None
    temp_workbook_path: Optional[Path] = None

    def add_generated_report(self, report_path: Optional[Path]) -> None:
        if report_path is not None:
            self.generated_report_paths.append(report_path)

    def add_diagnostic_summary(self, summary: DiagnosticSummary) -> None:
        self.diagnostics_history.append(summary)
        if summary.report_path is not None:
            self.generated_report_paths.append(summary.report_path)

    @property
    def is_workbook_loaded(self) -> bool:
        return self.workbook is not None and self.worksheet is not None
```

## 3) `app/excel_io.py`

```python
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from openpyxl import load_workbook

from app.config import (
    BENCHMARK_RECORD_IDS,
    ENABLE_BENCHMARK_MODE,
    MAX_ROWS_TO_PROCESS,
    PDF_BASE_DIR,
    REQUIRED_COLUMNS,
    SHEET_NAME,
    build_final_workbook_path,
    build_temp_workbook_path,
)
from app.models import DownloadResult, Record, SessionState
from app.utils import build_pdf_filename


def load_workbook_and_sheet(workbook_path: Path, sheet_name: str):
    if not workbook_path.exists():
        raise FileNotFoundError(f"Workbook not found: {workbook_path}")
    wb = load_workbook(workbook_path)
    if sheet_name not in wb.sheetnames:
        raise ValueError(f"Sheet not found: {sheet_name}")
    return wb, wb[sheet_name]


def build_col_map(ws) -> Dict[str, int]:
    col_map: Dict[str, int] = {}
    for col_idx in range(1, ws.max_column + 1):
        header = ws.cell(row=1, column=col_idx).value
        if header is not None and str(header).strip():
            col_map[str(header).strip()] = col_idx
    return col_map


def validate_required_columns(col_map: Dict[str, int], sheet_name: str, required_columns: Optional[Sequence[str]] = None) -> None:
    required = list(required_columns or REQUIRED_COLUMNS)
    missing = [c for c in required if c not in col_map]
    if missing:
        raise ValueError(f"Missing required columns in '{sheet_name}': {missing}")


def get_cell(ws, row_idx: int, col_map: Dict[str, int], header: str):
    return ws.cell(row=row_idx, column=col_map[header]).value


def get_optional_cell(ws, row_idx: int, col_map: Dict[str, int], header: str, default: Any = ""):
    if header not in col_map:
        return default
    return ws.cell(row=row_idx, column=col_map[header]).value


def set_cell(ws, row_idx: int, col_map: Dict[str, int], header: str, value) -> None:
    ws.cell(row=row_idx, column=col_map[header], value=value)


def is_blank(value) -> bool:
    return value is None or str(value).strip() == ""


def normalize_doi_like(value: str) -> Optional[str]:
    if is_blank(value):
        return None
    doi = str(value).strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE).strip()
    if re.match(r"^10\.\d{4,9}/\S+$", doi):
        return doi
    return None


def row_has_usable_doi(ws, row_idx: int, col_map: Dict[str, int]) -> bool:
    doi_raw = str(get_optional_cell(ws, row_idx, col_map, "DOI", "") or "").strip()
    doi_link_raw = str(get_optional_cell(ws, row_idx, col_map, "DOI Link", "") or "").strip()
    if doi_link_raw:
        return True
    return normalize_doi_like(doi_raw) is not None


def row_is_already_downloaded(ws, row_idx: int, col_map: Dict[str, int]) -> bool:
    pdf_downloaded = get_optional_cell(ws, row_idx, col_map, "pdf_downloaded", "")
    pdf_status = str(get_optional_cell(ws, row_idx, col_map, "pdf_download_status", "") or "").strip().lower()
    if str(pdf_downloaded).strip() == "1":
        return True
    return pdf_status == "downloaded"


def build_record(ws, row_idx: int, col_map: Dict[str, int]) -> Optional[Record]:
    record_id = str(get_cell(ws, row_idx, col_map, "record_id") or "").strip()
    if not record_id:
        return None
    if ENABLE_BENCHMARK_MODE and BENCHMARK_RECORD_IDS and record_id not in BENCHMARK_RECORD_IDS:
        return None
    title = str(get_cell(ws, row_idx, col_map, "Title") or "").strip()
    doi_raw = str(get_cell(ws, row_idx, col_map, "DOI") or "").strip()
    doi_link_raw = str(get_cell(ws, row_idx, col_map, "DOI Link") or "").strip()
    file_name = build_pdf_filename(record_id, title)
    pdf_path = PDF_BASE_DIR / file_name
    relative_path = f"pdf_files/{file_name}"
    return Record(row_idx, record_id, title, doi_raw, doi_link_raw, file_name, pdf_path, relative_path)


def collect_records(ws, col_map: Dict[str, int], max_rows_to_process: Optional[int]) -> List[Record]:
    records: List[Record] = []
    logical_seen = 0
    for row_idx in range(2, ws.max_row + 1):
        record = build_record(ws, row_idx, col_map)
        if record is None:
            continue
        records.append(record)
        logical_seen += 1
        if max_rows_to_process is not None and logical_seen >= max_rows_to_process:
            break
    return records


def write_result(ws, row_idx: int, col_map: Dict[str, int], result: DownloadResult) -> None:
    set_cell(ws, row_idx, col_map, "pdf_downloaded", result.pdf_downloaded)
    set_cell(ws, row_idx, col_map, "pdf_download_status", result.pdf_download_status)
    set_cell(ws, row_idx, col_map, "pdf_file_name", result.pdf_file_name)
    set_cell(ws, row_idx, col_map, "pdf_source_url", result.pdf_source_url)
    set_cell(ws, row_idx, col_map, "pdf_local_path", result.pdf_local_path)
    set_cell(ws, row_idx, col_map, "pdf_http_status", result.pdf_http_status if result.pdf_http_status is not None else "")
    set_cell(ws, row_idx, col_map, "pdf_checked_at", result.pdf_checked_at)


def write_doi_enrichment_result(ws, row_idx: int, col_map: Dict[str, int], doi: str, doi_link: str) -> None:
    set_cell(ws, row_idx, col_map, "DOI", doi)
    set_cell(ws, row_idx, col_map, "DOI Link", doi_link)


def refresh_records_from_worksheet(ws, col_map: Dict[str, int], max_rows_to_process: Optional[int] = None) -> List[Record]:
    return collect_records(ws, col_map, max_rows_to_process)


def initialize_session_state(workbook_path: Path, sheet_name: str = SHEET_NAME, max_rows_to_process: Optional[int] = None) -> SessionState:
    wb, ws = load_workbook_and_sheet(workbook_path, sheet_name)
    col_map = build_col_map(ws)
    validate_required_columns(col_map, sheet_name)
    effective_max_rows = max_rows_to_process if max_rows_to_process is not None else MAX_ROWS_TO_PROCESS
    records = collect_records(ws, col_map, effective_max_rows)
    return SessionState(workbook_path=workbook_path, sheet_name=sheet_name, workbook=wb, worksheet=ws, col_map=col_map, records=records)


def refresh_session_records(session_state: SessionState, max_rows_to_process: Optional[int] = None) -> None:
    if not session_state.is_workbook_loaded:
        raise ValueError("SessionState workbook is not loaded.")
    effective_max_rows = max_rows_to_process if max_rows_to_process is not None else MAX_ROWS_TO_PROCESS
    session_state.records = refresh_records_from_worksheet(session_state.worksheet, session_state.col_map, effective_max_rows)


def safe_save_workbook(wb, output_path: Path, max_attempts: int = 2) -> bool:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, max_attempts + 1):
        try:
            temp_path = output_path.with_name(output_path.stem + ".__tmp__.xlsx")
            wb.save(temp_path)
            if output_path.exists():
                try:
                    output_path.unlink()
                except PermissionError:
                    pass
            temp_path.replace(output_path)
            return True
        except KeyboardInterrupt:
            raise
        except Exception:
            if attempt == max_attempts:
                return False
            time.sleep(0.5)
    return False


def save_session_checkpoint(session_state: SessionState, label: str, timestamp: Optional[str] = None) -> Optional[Path]:
    if not session_state.is_workbook_loaded:
        raise ValueError("SessionState workbook is not loaded.")
    checkpoint_path = build_temp_workbook_path(label=label, timestamp=timestamp)
    ok = safe_save_workbook(session_state.workbook, checkpoint_path)
    if not ok:
        return None
    session_state.temp_workbook_path = checkpoint_path
    return checkpoint_path


def save_final_workbook(session_state: SessionState, output_path: Optional[Path] = None, timestamp: Optional[str] = None) -> Optional[Path]:
    if not session_state.is_workbook_loaded:
        raise ValueError("SessionState workbook is not loaded.")
    final_path = output_path or build_final_workbook_path(timestamp=timestamp)
    ok = safe_save_workbook(session_state.workbook, final_path)
    if not ok:
        return None
    session_state.final_workbook_path = final_path
    return final_path
```

## 4) `app/pipeline.py`

```python
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
```

## 5) `app/diagnostics.py`

```python
from __future__ import annotations

import re
import threading
import time
import unicodedata
from collections import Counter, defaultdict
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config import (
    DIAGNOSTIC_ERROR_TAB_COLUMNS,
    DIAGNOSTIC_EXCLUDED_FROM_ERROR_RANKING,
    DIAGNOSTIC_MAX_ROWS_TO_PROCESS,
    DIAGNOSTIC_MAX_WORKERS,
    DIAGNOSTIC_OUTPUT_COLUMNS,
    DIAGNOSTIC_OUTPUT_SHEET_NAME,
    DIAGNOSTIC_PROGRESS_REFRESH_EVERY_N,
    DIAGNOSTIC_PROGRESS_REFRESH_EVERY_SECONDS,
    DIAGNOSTIC_REQUEST_TIMEOUT,
    DIAGNOSTIC_REQUIRED_INPUT_COLUMNS_INITIAL,
    DIAGNOSTIC_REQUIRED_INPUT_COLUMNS_SESSION,
    DIAGNOSTIC_STATS_SHEET_NAME,
    HEADERS,
    REPORT_NAME_DIAGNOSTICO_FASE0,
    REPORT_NAME_DIAGNOSTICO_FASE1,
    REPORT_NAME_DIAGNOSTICO_FASE2,
    REPORT_NAME_DIAGNOSTICO_INICIAL,
    SHEET_NAME,
    build_report_output_path,
)
from app.excel_io import build_col_map, get_optional_cell, safe_save_workbook
from app.models import DiagnosticSummary, SessionState


ReporterType = Optional[Callable[[str, dict], None]]
StopEventType = Optional[threading.Event]

_thread_local = threading.local()


# =========================
# STYLE CONSTANTS
# =========================

GREEN_TITLE_FILL = "FF1F6E43"
DARK_HEADER_FILL = "FF000000"
BLUE_SECTION_FILL = "FF1F4E78"
LIGHT_BLUE_HEADER_FILL = "FFD9EAF7"
WHITE_FONT = "FFFFFFFF"

CENTER = Alignment(horizontal="center", vertical="center")
CENTER_TOP = Alignment(horizontal="center", vertical="top")


# =========================
# GENERIC HELPERS
# =========================

def emit(reporter: ReporterType, event_name: str, payload: dict) -> None:
    if reporter is None:
        return
    reporter(event_name, payload)


def is_blank(value) -> bool:
    return value is None or str(value).strip() == ""


def normalize_text(value: str) -> str:
    value = str(value or "").strip()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.strip().lower()


def normalize_label(value: str) -> str:
    return normalize_text(value)


def normalize_doi(doi: str) -> Optional[str]:
    if is_blank(doi):
        return None

    doi = str(doi).strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    doi = doi.strip()

    if re.match(r"^10\.\d{4,9}/\S+$", doi):
        return doi

    return None


def make_doi_url(doi: str) -> str:
    return f"https://doi.org/{doi}"


def extract_pdf_url_from_html(base_url: str, html: str) -> Optional[str]:
    if not html:
        return None

    patterns = [
        r'<meta[^>]+name=["\']citation_pdf_url["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']citation_pdf_url["\']',
        r'href=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']',
        r'src=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']',
    ]

    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if match:
            return urljoin(base_url, match.group(1))

    return None


def normalize_host(url: str) -> str:
    if is_blank(url):
        return "(missing)"

    try:
        parsed = urlparse(str(url).strip())
        host = (parsed.netloc or "").strip().lower()
        if ":" in host:
            host = host.split(":")[0]
        if host.startswith("www."):
            host = host[4:]
        return host if host else "(missing)"
    except Exception:
        return "(missing)"


def make_safe_sheet_name(name: str) -> str:
    name = re.sub(r'[:\\/?*\[\]]', "_", str(name).strip())
    return name[:31] if len(name) > 31 else name


def response_looks_like_pdf(resp: requests.Response) -> bool:
    content_type = (resp.headers.get("Content-Type") or "").lower()
    if "application/pdf" in content_type:
        return True

    try:
        return resp.content[:5] == b"%PDF-"
    except Exception:
        return False


def classify_html_failure(status_code: Optional[int], html: str, final_url: str = "") -> str:
    text = (html or "").lower()

    security_markers = [
        "captcha",
        "cf-chl",
        "cloudflare",
        "attention required",
        "verify you are human",
        "security check",
        "bot check",
        "checking if the site connection is secure",
        "recaptcha",
        "hcaptcha",
    ]
    if any(marker in text for marker in security_markers):
        return "captcha_or_security_check"

    if status_code == 403:
        if any(x in text for x in ["captcha", "security", "human", "cloudflare"]):
            return "captcha_or_security_check"
        return "paywalled_institutional_access"

    purchase_markers = [
        "purchase pdf",
        "buy article",
        "buy now",
        "purchase access",
        "rent this article",
        "add to cart",
        "purchase this article",
    ]
    if any(marker in text for marker in purchase_markers):
        return "paywalled_purchase_required"

    institutional_markers = [
        "access through your institution",
        "institutional access",
        "login via institution",
        "shibboleth",
        "sign in through your institution",
        "institutional login",
        "check access",
        "get access",
        "subscribe to journal",
        "subscription required",
    ]
    if any(marker in text for marker in institutional_markers):
        return "paywalled_institutional_access"

    if status_code == 404:
        return "not_found"

    if status_code is not None and status_code >= 500:
        return "broken_link"

    metadata_markers = [
        "abstract",
        "references",
        "article info",
        "metrics",
        "supplementary",
        "full text",
        "author information",
    ]
    if any(marker in text for marker in metadata_markers):
        return "manual_check"

    return "manual_check"


def build_retry_strategy() -> Retry:
    return Retry(
        total=1,
        connect=1,
        read=1,
        redirect=2,
        status=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET", "HEAD"]),
        backoff_factor=0.3,
        raise_on_status=False,
        respect_retry_after_header=True,
    )


def get_thread_session() -> requests.Session:
    session = getattr(_thread_local, "session", None)
    if session is not None:
        return session

    session = requests.Session()
    retry_strategy = build_retry_strategy()

    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=100,
        pool_maxsize=100,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    merged_headers = dict(HEADERS)
    merged_headers.setdefault("Accept-Language", "en-US,en;q=0.9")
    merged_headers.setdefault("Connection", "keep-alive")
    session.headers.update(merged_headers)

    _thread_local.session = session
    return session


def try_download_diagnostic(
    url: str,
    session: requests.Session,
) -> Tuple[str, Optional[int], str]:
    """
    Returns:
        (status_label, http_status, final_url_used)
    """
    try:
        resp = session.get(
            url,
            timeout=DIAGNOSTIC_REQUEST_TIMEOUT,
            allow_redirects=True,
            stream=False,
        )
        http_status = resp.status_code
        final_url = resp.url

        if http_status >= 400:
            if http_status == 404:
                return "not_found", http_status, final_url
            if http_status == 403:
                html = ""
                try:
                    html = resp.text or ""
                except Exception:
                    pass
                return classify_html_failure(http_status, html, final_url), http_status, final_url
            return "broken_link", http_status, final_url

        if response_looks_like_pdf(resp):
            return "downloaded", http_status, final_url

        html = ""
        try:
            html = resp.text or ""
        except Exception:
            pass

        pdf_url = extract_pdf_url_from_html(final_url, html)

        if pdf_url:
            pdf_resp = session.get(
                pdf_url,
                timeout=DIAGNOSTIC_REQUEST_TIMEOUT,
                allow_redirects=True,
                stream=False,
            )
            pdf_http_status = pdf_resp.status_code
            pdf_final_url = pdf_resp.url

            if pdf_http_status >= 400:
                if pdf_http_status == 404:
                    return "not_found", pdf_http_status, pdf_final_url
                if pdf_http_status == 403:
                    pdf_html = ""
                    try:
                        pdf_html = pdf_resp.text or ""
                    except Exception:
                        pass
                    return classify_html_failure(pdf_http_status, pdf_html, pdf_final_url), pdf_http_status, pdf_final_url
                return "broken_link", pdf_http_status, pdf_final_url

            if response_looks_like_pdf(pdf_resp):
                return "downloaded", pdf_http_status, pdf_final_url

            pdf_html = ""
            try:
                pdf_html = pdf_resp.text or ""
            except Exception:
                pass
            return classify_html_failure(pdf_http_status, pdf_html, pdf_final_url), pdf_http_status, pdf_final_url

        return classify_html_failure(http_status, html, final_url), http_status, final_url

    except requests.Timeout:
        return "broken_link", None, url
    except requests.RequestException:
        return "broken_link", None, url


def autosize_columns(ws, extra_padding: int = 2, max_width: int = 80) -> None:
    for col_idx in range(1, ws.max_column + 1):
        col_letter = get_column_letter(col_idx)
        max_len = 0

        for row_idx in range(1, ws.max_row + 1):
            value = ws.cell(row=row_idx, column=col_idx).value
            value_str = "" if value is None else str(value)
            if len(value_str) > max_len:
                max_len = len(value_str)

        ws.column_dimensions[col_letter].width = min(max(max_len + extra_padding, 10), max_width)


# =========================
# FORMATTING HELPERS
# =========================

def format_wos_full_text_header(ws) -> None:
    for col_idx in range(1, ws.max_column + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = Font(bold=True)
        cell.alignment = CENTER


def format_error_tab_header(ws) -> None:
    for col_idx in range(1, ws.max_column + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = Font(bold=True)
        cell.alignment = CENTER_TOP


def format_error_tab_body(ws) -> None:
    for row_idx in range(2, ws.max_row + 1):
        for col_idx in (1, 6, 8):
            ws.cell(row=row_idx, column=col_idx).alignment = CENTER


def style_title_green(ws, start_cell: str, end_cell: str, text: str) -> None:
    ws[start_cell] = text
    ws[start_cell].font = Font(bold=True, size=14, color=WHITE_FONT)
    ws[start_cell].fill = PatternFill(fill_type="solid", fgColor=GREEN_TITLE_FILL)
    ws[start_cell].alignment = CENTER
    ws.merge_cells(f"{start_cell}:{end_cell}")


def style_dark_header_row(ws, row_num: int, headers: list[str], start_col: int = 1) -> None:
    fill = PatternFill(fill_type="solid", fgColor=DARK_HEADER_FILL)
    font = Font(color=WHITE_FONT, bold=True)

    for idx, header in enumerate(headers, start=start_col):
        cell = ws.cell(row=row_num, column=idx, value=header)
        cell.fill = fill
        cell.font = font
        cell.alignment = CENTER


def style_blue_section_title(ws, row_num: int, col_start: int, col_end: int, text: str) -> None:
    cell = ws.cell(row=row_num, column=col_start, value=text)
    cell.fill = PatternFill(fill_type="solid", fgColor=BLUE_SECTION_FILL)
    cell.font = Font(color=WHITE_FONT, bold=True)
    cell.alignment = CENTER
    ws.merge_cells(start_row=row_num, start_column=col_start, end_row=row_num, end_column=col_end)


def style_blue_light_header_row(ws, row_num: int, headers: list[str], start_col: int = 1) -> None:
    fill = PatternFill(fill_type="solid", fgColor=LIGHT_BLUE_HEADER_FILL)
    font = Font(bold=True)

    for idx, header in enumerate(headers, start=start_col):
        cell = ws.cell(row=row_num, column=idx, value=header)
        cell.fill = fill
        cell.font = font
        cell.alignment = CENTER


def apply_stats_sheet_layout(ws) -> None:
    ws["A2"].font = Font(italic=True)
    ws["A2"].alignment = CENTER
    ws["A3"].font = Font(italic=True)
    ws["A3"].alignment = CENTER

    for row_idx in range(6, ws.max_row + 1):
        for col_idx in range(1, 6):
            ws.cell(row=row_idx, column=col_idx).alignment = CENTER

    for row_idx in range(1, ws.max_row + 1):
        if ws.cell(row=row_idx, column=2).value == "Total de erros":
            ws.cell(row=row_idx, column=2).font = Font(bold=True)
            ws.cell(row=row_idx, column=3).font = Font(bold=True)
            ws.cell(row=row_idx, column=2).alignment = CENTER
            ws.cell(row=row_idx, column=3).alignment = CENTER

    for row_idx in range(6, ws.max_row + 1):
        for col_idx in range(7, 11):
            ws.cell(row=row_idx, column=col_idx).alignment = CENTER

    widths = {
        "A": 8,
        "B": 34,
        "C": 10,
        "D": 12,
        "E": 18,
        "F": 3,
        "G": 8,
        "H": 30,
        "I": 28,
        "J": 10,
    }
    for col_letter, width in widths.items():
        ws.column_dimensions[col_letter].width = width


# =========================
# DIAGNOSTIC MODE / OUTPUT
# =========================

def resolve_diagnostic_mode(diagnostic_label: str) -> str:
    normalized = normalize_label(diagnostic_label)
    if "inicial" in normalized:
        return "initial"
    return "session"


def resolve_report_prefix(diagnostic_label: str) -> str:
    normalized = normalize_label(diagnostic_label)

    if "inicial" in normalized:
        return REPORT_NAME_DIAGNOSTICO_INICIAL
    if "fase 0" in normalized or "fase0" in normalized:
        return REPORT_NAME_DIAGNOSTICO_FASE0
    if "fase 1" in normalized or "fase1" in normalized:
        return REPORT_NAME_DIAGNOSTICO_FASE1
    if "fase 2" in normalized or "fase2" in normalized:
        return REPORT_NAME_DIAGNOSTICO_FASE2

    return "diagnostico"


def build_diagnostic_title(diagnostic_label: str) -> str:
    return diagnostic_label.upper()


def validate_required_input_columns(col_map: Dict[str, int], sheet_name: str, diagnostic_mode: str) -> None:
    if diagnostic_mode == "initial":
        required = DIAGNOSTIC_REQUIRED_INPUT_COLUMNS_INITIAL
    else:
        required = DIAGNOSTIC_REQUIRED_INPUT_COLUMNS_SESSION

    missing = [c for c in required if c not in col_map]
    if missing:
        raise ValueError(f"Missing required columns in '{sheet_name}' for diagnostic mode '{diagnostic_mode}': {missing}")


# =========================
# REPORT SHEETS
# =========================

def create_stats_sheet(
    wb: Workbook,
    diagnosed_rows: list[dict],
    source_sheet_name: str,
    diagnostic_label: str,
    diagnostic_mode: str,
) -> None:
    ws = wb.create_sheet(DIAGNOSTIC_STATS_SHEET_NAME)

    style_title_green(ws, "A1", "E1", "PDF download status - ranking de erros e top websites")
    ws["A2"] = f"Base analisada: {source_sheet_name} — {diagnostic_label}"

    if diagnostic_mode == "initial":
        ws["A3"] = (
            "Nota: o ranking de erros exclui o estado 'downloaded'. "
            "O campo 'website' corresponde ao host de pdf_source_url."
        )
    else:
        ws["A3"] = (
            "Nota: esta análise considera apenas registos cujo estado atual não é "
            "'downloaded'. O ranking exclui o estado final 'downloaded'. "
            "O campo 'website' corresponde ao host de pdf_source_url."
        )

    error_counter = Counter()
    error_website_counter = defaultdict(Counter)
    combo_counter = Counter()

    total_rows = len(diagnosed_rows)

    for row in diagnosed_rows:
        status = row.get("pdf_download_status")
        if status in DIAGNOSTIC_EXCLUDED_FROM_ERROR_RANKING:
            continue

        website = normalize_host(row.get("pdf_source_url"))
        error_counter[status] += 1
        error_website_counter[status][website] += 1
        combo_counter[(status, website)] += 1

    total_errors = sum(error_counter.values())

    fifth_header = "% total registos" if diagnostic_mode == "initial" else "% base não-downloaded"

    style_dark_header_row(
        ws,
        5,
        ["Rank", "Erro (pdf_download_status)", "N", "% erros", fifth_header],
        start_col=1,
    )

    sorted_errors = sorted(error_counter.items(), key=lambda x: (-x[1], str(x[0]).lower()))

    current_row = 6
    for rank, (error_name, count) in enumerate(sorted_errors, start=1):
        ws.cell(current_row, 1, rank)
        ws.cell(current_row, 2, error_name)
        ws.cell(current_row, 3, count)
        ws.cell(current_row, 4, count / total_errors if total_errors else 0)
        ws.cell(current_row, 5, count / total_rows if total_rows else 0)
        ws.cell(current_row, 4).number_format = "0.0%"
        ws.cell(current_row, 5).number_format = "0.0%"
        current_row += 1

    ws.cell(current_row, 2, "Total de erros")
    ws.cell(current_row, 3, total_errors)
    ws.cell(current_row, 2).font = Font(bold=True)
    ws.cell(current_row, 3).font = Font(bold=True)

    combo_start_col = 7
    style_blue_section_title(ws, 5, combo_start_col, combo_start_col + 3, "Combinações erro + website mais frequentes")
    style_blue_light_header_row(ws, 6, ["Rank", "Erro", "Website", "N"], start_col=combo_start_col)

    combo_sorted = sorted(
        combo_counter.items(),
        key=lambda x: (-x[1], str(x[0][0]).lower(), str(x[0][1]).lower()),
    )

    combo_row = 7
    for rank, ((error_name, website), n) in enumerate(combo_sorted[:15], start=1):
        ws.cell(combo_row, combo_start_col, rank)
        ws.cell(combo_row, combo_start_col + 1, error_name)
        ws.cell(combo_row, combo_start_col + 2, website)
        ws.cell(combo_row, combo_start_col + 3, n)
        combo_row += 1

    section_row = current_row + 4
    for error_name, _ in sorted_errors:
        style_blue_section_title(ws, section_row, 1, 3, f"Top websites — {error_name}")
        section_row += 1
        style_blue_light_header_row(ws, section_row, ["Rank", "Website", "N"], start_col=1)
        section_row += 1

        websites_sorted = sorted(
            error_website_counter[error_name].items(),
            key=lambda x: (-x[1], str(x[0]).lower()),
        )[:10]

        for rank, (website, n) in enumerate(websites_sorted, start=1):
            ws.cell(section_row, 1, rank)
            ws.cell(section_row, 2, website)
            ws.cell(section_row, 3, n)
            section_row += 1

        section_row += 2

    apply_stats_sheet_layout(ws)


def create_error_tabs(
    wb: Workbook,
    diagnosed_rows: list[dict],
) -> None:
    grouped = defaultdict(list)

    for row in diagnosed_rows:
        status = row.get("pdf_download_status")
        if status in DIAGNOSTIC_EXCLUDED_FROM_ERROR_RANKING:
            continue
        grouped[status].append(row)

    ordered_errors = sorted(grouped.keys(), key=lambda x: (-len(grouped[x]), str(x).lower()))

    for error_name in ordered_errors:
        ws = wb.create_sheet(make_safe_sheet_name(error_name))

        for col_idx, header in enumerate(DIAGNOSTIC_ERROR_TAB_COLUMNS, start=1):
            ws.cell(row=1, column=col_idx, value=header)

        format_error_tab_header(ws)

        current_row = 2
        for row in grouped[error_name]:
            values = [
                row.get("record_id", ""),
                row.get("Authors", ""),
                row.get("Title", ""),
                row.get("DOI", ""),
                row.get("DOI Link", ""),
                row.get("pdf_download_status", ""),
                row.get("pdf_source_url", ""),
                row.get("pdf_http_status", ""),
            ]

            for col_idx, value in enumerate(values, start=1):
                cell = ws.cell(row=current_row, column=col_idx, value=value)

                if col_idx == 5 and value:
                    cell.hyperlink = str(value)
                    cell.style = "Hyperlink"

                if col_idx == 7 and value:
                    cell.hyperlink = str(value)
                    cell.style = "Hyperlink"

            current_row += 1

        format_error_tab_body(ws)
        autosize_columns(ws)


# =========================
# DATA EXTRACTION
# =========================

def extract_rows_for_initial_diagnostic(
    ws,
    col_map: Dict[str, int],
    max_rows: Optional[int],
) -> list[dict]:
    rows: list[dict] = []
    processed = 0

    headers = DIAGNOSTIC_REQUIRED_INPUT_COLUMNS_INITIAL

    for row_idx in range(2, ws.max_row + 1):
        record_id = str(get_optional_cell(ws, row_idx, col_map, "record_id", "") or "").strip()
        if not record_id:
            continue

        row_values = {header: get_optional_cell(ws, row_idx, col_map, header, "") for header in headers}
        row_values["_source_row_idx"] = row_idx
        rows.append(row_values)

        processed += 1
        if max_rows is not None and processed >= max_rows:
            break

    return rows


def extract_rows_for_session_diagnostic(
    ws,
    col_map: Dict[str, int],
    max_rows: Optional[int],
) -> list[dict]:
    rows: list[dict] = []
    processed = 0

    headers = DIAGNOSTIC_REQUIRED_INPUT_COLUMNS_SESSION

    for row_idx in range(2, ws.max_row + 1):
        record_id = str(get_optional_cell(ws, row_idx, col_map, "record_id", "") or "").strip()
        if not record_id:
            continue

        existing_status = str(get_optional_cell(ws, row_idx, col_map, "pdf_download_status", "") or "").strip().lower()
        if existing_status == "downloaded":
            continue

        row_values = {header: get_optional_cell(ws, row_idx, col_map, header, "") for header in headers}
        row_values["_source_row_idx"] = row_idx
        row_values["_previous_pdf_download_status"] = get_optional_cell(ws, row_idx, col_map, "pdf_download_status", "")
        rows.append(row_values)

        processed += 1
        if max_rows is not None and processed >= max_rows:
            break

    return rows


def diagnose_single_row(row_data: dict) -> dict:
    session = get_thread_session()

    doi_raw_str = str(row_data.get("DOI") or "").strip()
    doi_link = str(row_data.get("DOI Link") or "").strip()
    doi = normalize_doi(doi_raw_str)

    if not doi_raw_str and not doi_link:
        diagnostic_status = "missing_doi"
        diagnostic_http_status = ""
        diagnostic_source_url = ""

    elif doi_raw_str and not doi and not doi_link:
        diagnostic_status = "invalid_doi"
        diagnostic_http_status = ""
        diagnostic_source_url = ""

    else:
        candidate_urls: list[str] = []

        if doi_link:
            candidate_urls.append(doi_link)

        if doi:
            doi_url = make_doi_url(doi)
            if doi_url not in candidate_urls:
                candidate_urls.append(doi_url)

        if not candidate_urls:
            diagnostic_status = "invalid_doi"
            diagnostic_http_status = ""
            diagnostic_source_url = ""
        else:
            diagnostic_status = "manual_check"
            diagnostic_http_status = ""
            diagnostic_source_url = ""

            for url in candidate_urls:
                status_label, http_status, final_url = try_download_diagnostic(url, session)
                diagnostic_status = status_label
                diagnostic_http_status = http_status if http_status is not None else ""
                diagnostic_source_url = final_url or url

                if status_label == "downloaded":
                    break

    result = {
        "record_id": row_data.get("record_id", ""),
        "Authors": row_data.get("Authors", ""),
        "Title": row_data.get("Title", ""),
        "DOI": row_data.get("DOI", ""),
        "DOI Link": row_data.get("DOI Link", ""),
        "pdf_download_status": diagnostic_status,
        "pdf_source_url": diagnostic_source_url,
        "pdf_http_status": diagnostic_http_status,
        "_source_row_idx": row_data.get("_source_row_idx"),
    }
    return result


def should_refresh_progress(
    processed: int,
    last_refresh_time: float,
    force: bool = False,
) -> bool:
    if force:
        return True
    if processed % DIAGNOSTIC_PROGRESS_REFRESH_EVERY_N == 0:
        return True
    if (time.time() - last_refresh_time) >= DIAGNOSTIC_PROGRESS_REFRESH_EVERY_SECONDS:
        return True
    return False


# =========================
# MAIN PUBLIC ENTRYPOINT
# =========================

def run_diagnostic_for_session(
    session_state: SessionState,
    diagnostic_label: str,
    reporter: ReporterType = None,
    stop_event: StopEventType = None,
) -> dict:
    if not session_state.is_workbook_loaded:
        raise ValueError("SessionState workbook is not loaded.")

    ws = session_state.worksheet
    col_map = build_col_map(ws)
    session_state.col_map = col_map

    diagnostic_mode = resolve_diagnostic_mode(diagnostic_label)
    validate_required_input_columns(col_map, session_state.sheet_name, diagnostic_mode)

    max_rows = DIAGNOSTIC_MAX_ROWS_TO_PROCESS

    if diagnostic_mode == "initial":
        rows_to_process = extract_rows_for_initial_diagnostic(ws, col_map, max_rows)
    else:
        rows_to_process = extract_rows_for_session_diagnostic(ws, col_map, max_rows)

    total_to_process = len(rows_to_process)
    start_time = time.time()
    title = build_diagnostic_title(diagnostic_label)

    emit(
        reporter,
        "diagnostic_start",
        {
            "processed": 0,
            "total": total_to_process,
            "workers": DIAGNOSTIC_MAX_WORKERS,
            "start_time": start_time,
            "last_record_id": "",
            "last_status": "starting",
            "title": title,
            "stopped_early": False,
        },
    )

    diagnosed_rows: list[dict] = []
    processed = 0
    last_refresh_time = 0.0
    last_record = ""
    last_status = ""

    if total_to_process > 0:
        executor = ThreadPoolExecutor(max_workers=DIAGNOSTIC_MAX_WORKERS)

        try:
            futures = {}
            next_idx = 0

            while (
                next_idx < total_to_process
                and len(futures) < DIAGNOSTIC_MAX_WORKERS
                and not (stop_event is not None and stop_event.is_set())
            ):
                row_data = rows_to_process[next_idx]
                futures[executor.submit(diagnose_single_row, row_data)] = row_data
                next_idx += 1

            while futures:
                done, _ = wait(
                    list(futures.keys()),
                    timeout=0.1,
                    return_when=FIRST_COMPLETED,
                )

                if stop_event is not None and stop_event.is_set():
                    for pending in list(futures.keys()):
                        pending.cancel()
                    futures.clear()
                    break

                if not done:
                    continue

                for future in done:
                    futures.pop(future, None)
                    result = future.result()
                    diagnosed_rows.append(result)

                    processed += 1
                    last_record = str(result.get("record_id", ""))
                    last_status = str(result.get("pdf_download_status", ""))

                    if should_refresh_progress(processed, last_refresh_time):
                        emit(
                            reporter,
                            "diagnostic_update",
                            {
                                "processed": processed,
                                "total": total_to_process,
                                "workers": DIAGNOSTIC_MAX_WORKERS,
                                "start_time": start_time,
                                "last_record_id": last_record,
                                "last_status": last_status,
                                "title": title,
                                "stopped_early": False,
                            },
                        )
                        last_refresh_time = time.time()

                    if stop_event is not None and stop_event.is_set():
                        for pending in list(futures.keys()):
                            pending.cancel()
                        futures.clear()
                        break

                    while (
                        next_idx < total_to_process
                        and len(futures) < DIAGNOSTIC_MAX_WORKERS
                        and not (stop_event is not None and stop_event.is_set())
                    ):
                        row_data = rows_to_process[next_idx]
                        futures[executor.submit(diagnose_single_row, row_data)] = row_data
                        next_idx += 1

                if stop_event is not None and stop_event.is_set():
                    break

        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    diagnosed_rows.sort(key=lambda row: (row.get("_source_row_idx") or 0))

    total_downloaded = sum(1 for row in diagnosed_rows if row.get("pdf_download_status") == "downloaded")
    total_errors = sum(
        1
        for row in diagnosed_rows
        if row.get("pdf_download_status") not in DIAGNOSTIC_EXCLUDED_FROM_ERROR_RANKING
    )

    stopped_early = stop_event is not None and stop_event.is_set()
    if stopped_early:
        emit(
            reporter,
            "diagnostic_end",
            {
                "processed": processed,
                "total": total_to_process,
                "workers": DIAGNOSTIC_MAX_WORKERS,
                "start_time": start_time,
                "last_record_id": last_record,
                "last_status": last_status if last_status else "stopped",
                "title": title,
                "report_path": "",
                "stopped_early": True,
            },
        )

        return {
            "diagnostic_label": diagnostic_label,
            "diagnostic_mode": diagnostic_mode,
            "processed": processed,
            "total": total_to_process,
            "downloaded": total_downloaded,
            "errors": total_errors,
            "report_path": "",
            "sheet_name": DIAGNOSTIC_OUTPUT_SHEET_NAME,
            "stats_sheet_name": DIAGNOSTIC_STATS_SHEET_NAME,
            "stopped_early": True,
        }

    output_wb = Workbook()
    output_ws = output_wb.active
    output_ws.title = DIAGNOSTIC_OUTPUT_SHEET_NAME

    for col_idx, header in enumerate(DIAGNOSTIC_OUTPUT_COLUMNS, start=1):
        output_ws.cell(row=1, column=col_idx, value=header)

    output_row = 2
    for row_values in diagnosed_rows:
        for col_idx, header in enumerate(DIAGNOSTIC_OUTPUT_COLUMNS, start=1):
            cell = output_ws.cell(row=output_row, column=col_idx, value=row_values.get(header, ""))

            if header == "DOI Link" and row_values.get(header):
                cell.hyperlink = str(row_values.get(header))
                cell.style = "Hyperlink"

            if header == "pdf_source_url" and row_values.get(header):
                cell.hyperlink = str(row_values.get(header))
                cell.style = "Hyperlink"

        output_row += 1

    format_wos_full_text_header(output_ws)
    autosize_columns(output_ws)

    create_stats_sheet(
        wb=output_wb,
        diagnosed_rows=diagnosed_rows,
        source_sheet_name=SHEET_NAME,
        diagnostic_label=diagnostic_label,
        diagnostic_mode=diagnostic_mode,
    )

    create_error_tabs(
        wb=output_wb,
        diagnosed_rows=diagnosed_rows,
    )

    report_prefix = resolve_report_prefix(diagnostic_label)
    report_path = build_report_output_path(report_prefix, timestamp=session_state.timestamp or None)

    ok = safe_save_workbook(output_wb, report_path)
    if not ok:
        raise RuntimeError(f"Could not save diagnostic report: {report_path}")

    summary = DiagnosticSummary(
        diagnostic_label=diagnostic_label,
        total_rows_considered=total_to_process,
        total_rows_diagnosed=processed,
        total_downloaded=total_downloaded,
        total_errors=total_errors,
        report_path=report_path,
    )
    session_state.add_diagnostic_summary(summary)

    emit(
        reporter,
        "diagnostic_end",
        {
            "processed": processed,
            "total": total_to_process,
            "workers": DIAGNOSTIC_MAX_WORKERS,
            "start_time": start_time,
            "last_record_id": last_record,
            "last_status": last_status if last_status else "finished",
            "title": title,
            "report_path": str(report_path),
            "stopped_early": False,
        },
    )

    return {
        "diagnostic_label": diagnostic_label,
        "diagnostic_mode": diagnostic_mode,
        "processed": processed,
        "total": total_to_process,
        "downloaded": total_downloaded,
        "errors": total_errors,
        "report_path": str(report_path),
        "sheet_name": DIAGNOSTIC_OUTPUT_SHEET_NAME,
        "stats_sheet_name": DIAGNOSTIC_STATS_SHEET_NAME,
        "stopped_early": False,
    }
```

## 6) `app/doi_enrichment.py`

```python
# Neste snapshot, manter como referência a versão funcional criada neste chat.
# Conteúdo chave da versão atual:
# - run_phase0_doi_enrichment_for_session(session_state, reporter=None, generate_report=False)
# - generate_phase0_report_from_cache(session_state)
# - escreve apenas DOI e DOI Link na wos_full_text
# - faz cache interna dos resultados da última fase 0 para gerar report sem reprocessar
# - reports:
#   - doi_stats
#   - doi_all_processed
#   - doi_enriched
#   - doi_unresolved
# - thresholds:
#   - DOI_MIN_TITLE_SIMILARITY = 0.88
#   - DOI_MIN_CONFIDENCE_SCORE = 75.0
```

## 7) `ui/terminal_dashboard.py`

```python
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
            title="PDF DOWNLOADER TOOL",
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
            "PDF DOWNLOAD STATUS",
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
            "PDF DOWNLOAD STATUS",
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
            "PDF DOWNLOAD STATUS",
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
```

## 8) `main.py`

```python
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
```



---

## Ficheiros que devem estar alinhados no repositório local após este snapshot

Os ficheiros críticos que foram atualizados nesta fase são:

- `main.py`
- `app/pipeline.py`
- `app/diagnostics.py`
- `ui/terminal_dashboard.py`

Ficheiros críticos que continuam a fazer parte do fluxo atual e devem manter-se coerentes com estes:

- `app/doi_enrichment.py`
- `app/config.py`
- `app/excel_io.py`
- `app/models.py`

## Checklist de verificação manual após substituir os ficheiros

1. Abrir a app.
2. Confirmar o menu inicial com 4 opções.
3. Entrar pela fase 0.
4. Confirmar que `V` volta ao menu inicial.
5. Entrar diretamente pela fase 1.
6. Confirmar que o menu final da fase 1 permite voltar à fase 0.
7. Confirmar que o menu final da fase 2 permite voltar à fase 1.
8. Correr diagnóstico inicial e testar `P`, `V`, `S`.
9. Correr diagnóstico da fase 1 e testar `P`, `V`, `S`.
10. Confirmar criação de checkpoint ao sair da app durante execução.

## Nota final de handoff

Este snapshot foi preparado para que outro chat consiga:
- perceber o objetivo do projeto;
- perceber a arquitetura atual;
- perceber o que já foi corrigido;
- saber exatamente quais são os ficheiros atuais mais importantes;
- continuar a partir daqui sem reabrir toda a investigação anterior.
