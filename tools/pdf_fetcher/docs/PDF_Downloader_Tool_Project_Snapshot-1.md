# PDF Downloader Tool — Snapshot Completo do Projeto

> **Objetivo deste documento**  
> Este ficheiro serve como **snapshot de continuidade** do projeto.  
> A ideia é que, ao iniciar um novo chat, possas carregar este documento para fornecer de imediato:
>
> - a arquitetura atual;
> - os scripts propostos;
> - a lógica de funcionamento;
> - o ponto de situação;
> - o que já foi feito;
> - o que ainda falta validar ou melhorar.

---

# 1. Contexto do projeto

O projeto **PDF Downloader Tool** foi concebido para automatizar a tentativa de descarga de PDFs a partir de um workbook Excel com registos bibliográficos.

A aplicação deve:

- ler um workbook Excel;
- identificar os registos úteis;
- tentar descarregar PDFs com uma lógica genérica;
- aplicar lógica especializada para publishers/sites específicos;
- escrever o estado final de cada tentativa no workbook;
- funcionar em:
  - **modo terminal**
  - **modo Streamlit**

O objetivo foi sair de um **script monolítico** funcional e migrar para uma **arquitetura modular**, leve, clara e extensível.

---

# 2. Estado atual do projeto

## 2.1 O que já foi desenhado
Foi proposta uma arquitetura modular com:

- `app/` para a lógica central;
- `resolvers/` para lógica por site;
- `ui/` para apresentação em terminal e Streamlit;
- `main.py` como entry point do modo terminal;
- `.bat` para arranque rápido.

## 2.2 O que já foi produzido neste trabalho
Foram redigidos os scripts-base para:

- configuração;
- modelos;
- utilitários;
- sessão HTTP;
- leitura/escrita de Excel;
- resolver base;
- resolver Frontiers;
- deteção de resolvers;
- pipeline;
- dashboard terminal;
- interface Streamlit;
- ficheiros `.bat`;
- documentação.

## 2.3 O que ainda deve ser assumido
Este snapshot representa uma **base funcional proposta**, muito próxima do script original, mas ainda deve ser validada em ambiente real com:

- o workbook verdadeiro;
- os caminhos verdadeiros em `config.py`;
- instalação local do `.venv`;
- instalação de dependências;
- testes reais em terminal;
- testes reais em Streamlit.

---

# 3. Arquitetura final proposta

```text
pdf_downloader_tool/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── excel_io.py
│   ├── models.py
│   ├── pipeline.py
│   ├── resolver_detector.py
│   ├── session_factory.py
│   └── utils.py
├── resolvers/
│   ├── __init__.py
│   ├── base_download.py
│   └── frontiers.py
├── ui/
│   ├── __init__.py
│   ├── components.py
│   ├── streamlit_app.py
│   └── terminal_dashboard.py
├── logs/
├── old/
├── main.py
├── requirements.txt
├── run_streamlit.bat
└── run_terminal.bat
```

---

# 4. Lógica geral da arquitetura

## 4.1 `app/`
Contém o núcleo da aplicação:

- configuração global;
- leitura e escrita de Excel;
- modelos de dados;
- pipeline de execução;
- deteção de resolvers;
- criação de sessões HTTP;
- utilitários.

## 4.2 `resolvers/`
Cada ficheiro representa um resolver especializado por site/publisher.

Exemplos:
- `base_download.py`
- `frontiers.py`

## 4.3 `ui/`
Contém a camada de apresentação:
- terminal;
- Streamlit.

## 4.4 Entry points
- `main.py` → terminal
- `run_terminal.bat` → arranque rápido terminal
- `run_streamlit.bat` → arranque rápido Streamlit

---

# 5. Fluxo lógico da aplicação

```text
Início
  ↓
Resolver workbook de entrada
  ↓
Abrir workbook e sheet
  ↓
Validar colunas obrigatórias
  ↓
Construir lista de records
  ↓
Fase 1 — base download
  ↓
Escrever resultados fase 1
  ↓
Construir retry tasks
  ↓
Fase 2 — specialized retry
  ↓
Escrever resultados fase 2
  ↓
Guardar workbook final
  ↓
Apresentar resumo
  ↓
Fim
```

---

# 6. Scripts produzidos

## 6.1 `app/__init__.py`

```python
# app/__init__.py
```

### Função
Serve apenas para marcar `app` como pacote Python.

---

## 6.2 `app/config.py`

```python
from __future__ import annotations

from pathlib import Path
from typing import Optional


# =========================
# PATHS
# =========================

EXTERNAL_WOS_DIR = Path(
    r"C:\Users\Luís Pinto Coelho\Desktop\Dissertação\metanalysis development\2 - literature search & study screening\data\wos"
)

EXCEL_INPUT_DIR = EXTERNAL_WOS_DIR / "excel_files"
PDF_BASE_DIR = EXTERNAL_WOS_DIR / "pdf_files"

PREFERRED_WORKBOOK_PATH = EXCEL_INPUT_DIR / "wos_workbook_03.03.2026_v2.xlsx"


# =========================
# WORKBOOK
# =========================

OUTPUT_WORKBOOK_SUFFIX = "_pdf_downloaded.xlsx"
SHEET_NAME = "wos_full_text"


# =========================
# PHASE 1 - BASE DOWNLOAD
# =========================

MAX_WORKERS = 4
CONNECT_TIMEOUT = 8
READ_TIMEOUT = 15
SLEEP_BETWEEN_REQUESTS = 0.05
MAX_ROWS_TO_PROCESS: Optional[int] = None


# =========================
# BENCHMARK MODE
# =========================

ENABLE_BENCHMARK_MODE = False
BENCHMARK_RECORD_IDS: set[str] = set()


# =========================
# SAVE CADENCE
# =========================

SAVE_EVERY_N_ROWS = 100
SPECIALIZED_SAVE_EVERY_N_ROWS = 10


# =========================
# DASHBOARD REFRESH
# =========================

REFRESH_DASHBOARD_EVERY_N_COMPLETIONS = 10
FORCE_SIMPLE_TERMINAL = False


# =========================
# PHASE 2 - SPECIALIZED RETRY
# =========================

ENABLE_SPECIALIZED_RESOLVERS = True


# =========================
# FRONTIERS / PLAYWRIGHT
# =========================

ENABLE_FRONTIERS_RESOLVER = True
FRONTIERS_HEADLESS = False
FRONTIERS_NAVIGATION_TIMEOUT_MS = 30000
FRONTIERS_DOWNLOAD_TIMEOUT_MS = 40000
FRONTIERS_POST_LOAD_WAIT_MS = 1000
FRONTIERS_ALLOWED_DOMAIN_PATTERN = r"(^|\.)frontiersin\.org$"


# =========================
# HTTP HEADERS
# =========================

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


# =========================
# REQUIRED COLUMNS
# =========================

REQUIRED_INPUT_COLUMNS = [
    "record_id",
    "Title",
    "DOI",
    "DOI Link",
]

REQUIRED_OUTPUT_COLUMNS = [
    "pdf_downloaded",
    "pdf_download_status",
    "pdf_file_name",
    "pdf_source_url",
    "pdf_local_path",
    "pdf_http_status",
    "pdf_checked_at",
]

REQUIRED_COLUMNS = REQUIRED_INPUT_COLUMNS + REQUIRED_OUTPUT_COLUMNS


# =========================
# STATUS SETS
# =========================

BASE_AVAILABLE_STATUSES = {"downloaded", "duplicate_pdf"}
BASE_DOWNLOADED_NOW_STATUSES = {"downloaded"}

SPECIALIZED_DOWNLOADED_NOW_STATUSES = {
    "downloaded_frontiers",
}


# =========================
# TERMINAL / DASHBOARD
# =========================

FRAME_WIDTH = 78


# =========================
# HELPER FUNCTIONS
# =========================

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


def build_output_workbook_path(workbook_path: Path) -> Path:
    return EXCEL_INPUT_DIR / f"{workbook_path.stem}{OUTPUT_WORKBOOK_SUFFIX}"
```

### O que faz
Centraliza toda a configuração do sistema:
- caminhos;
- timeouts;
- número de workers;
- flags dos resolvers;
- colunas obrigatórias;
- estados.

### Notas
É o primeiro ficheiro a rever quando o projeto muda de pasta ou de workbook.

---

## 6.3 `app/models.py`

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


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
```

### O que faz
Define as estruturas de dados principais da aplicação.

### Importância
Evita o uso de dicionários soltos e torna a pipeline muito mais clara.

---

## 6.4 `app/utils.py`

```python
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def is_blank(value) -> bool:
    return value is None or str(value).strip() == ""


def sanitize_filename(text: str, max_len: int = 140) -> str:
    text = str(text or "").strip()

    text = re.sub(r'[\\/:*?"<>|]', " ", text)
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" ", "_")
    text = re.sub(r"_+", "_", text).strip("_")

    if not text:
        text = "untitled"

    return text[:max_len].rstrip("_")


def build_pdf_filename(record_id: str, title: str) -> str:
    safe_title = sanitize_filename(title)
    return f"{record_id}__{safe_title}.pdf"


def normalize_doi(doi: str) -> Optional[str]:
    if is_blank(doi):
        return None

    doi = str(doi).strip()
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.IGNORECASE)
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    doi = doi.strip()

    if re.match(r"^10\.\d{4,9}/\S+$", doi):
        return doi.rstrip(" .;,:)")

    match = re.search(r"(10\.\d{4,9}/\S+)", doi, flags=re.IGNORECASE)
    if match:
        return match.group(1).rstrip(" .;,:)")

    return None


def make_doi_url(doi: str) -> str:
    return f"https://doi.org/{doi}"


def extract_host(url: str) -> str:
    parsed = urlparse(str(url or "").strip())
    return (parsed.netloc or "").lower()


def url_matches_domain_pattern(url: str, pattern: str) -> bool:
    host = extract_host(url)
    if not host:
        return False
    return re.search(pattern, host) is not None


def format_seconds(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def deduplicate_urls(urls: list[str]) -> list[str]:
    seen = set()
    unique_urls: list[str] = []

    for url in urls:
        cleaned = str(url or "").strip()
        if not cleaned:
            continue
        if cleaned not in seen:
            seen.add(cleaned)
            unique_urls.append(cleaned)

    return unique_urls


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def save_pdf_bytes(pdf_path: Path, content: bytes) -> bool:
    if not content:
        return False

    ensure_parent_dir(pdf_path)
    pdf_path.write_bytes(content)
    return pdf_path.exists() and pdf_path.stat().st_size > 0
```

### O que faz
Concentra funções utilitárias reutilizáveis e neutras.

---

## 6.5 `app/session_factory.py`

```python
from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def build_session() -> requests.Session:
    session = requests.Session()

    retry = Retry(
        total=2,
        read=2,
        connect=2,
        backoff_factor=0.3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD", "OPTIONS"],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=20,
        pool_maxsize=20,
    )

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session
```

### O que faz
Cria a sessão `requests` usada na fase base, com retries e pool configurado.

---

## 6.6 `app/excel_io.py`

```python
from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List, Optional

from openpyxl import load_workbook

from app.config import (
    BENCHMARK_RECORD_IDS,
    ENABLE_BENCHMARK_MODE,
    PDF_BASE_DIR,
    REQUIRED_COLUMNS,
)
from app.models import DownloadResult, Record
from app.utils import build_pdf_filename


def load_workbook_and_sheet(workbook_path: Path, sheet_name: str):
    if not workbook_path.exists():
        raise FileNotFoundError(f"Workbook not found: {workbook_path}")

    wb = load_workbook(workbook_path)

    if sheet_name not in wb.sheetnames:
        raise ValueError(f"Sheet not found: {sheet_name}")

    ws = wb[sheet_name]
    return wb, ws


def build_col_map(ws) -> Dict[str, int]:
    col_map: Dict[str, int] = {}

    for col_idx in range(1, ws.max_column + 1):
        header = ws.cell(row=1, column=col_idx).value
        if header is not None and str(header).strip():
            col_map[str(header).strip()] = col_idx

    return col_map


def validate_required_columns(col_map: Dict[str, int], sheet_name: str) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in col_map]
    if missing:
        raise ValueError(f"Missing required columns in '{sheet_name}': {missing}")


def get_cell(ws, row_idx: int, col_map: Dict[str, int], header: str):
    return ws.cell(row=row_idx, column=col_map[header]).value


def set_cell(ws, row_idx: int, col_map: Dict[str, int], header: str, value) -> None:
    ws.cell(row=row_idx, column=col_map[header], value=value)


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

    return Record(
        row_idx=row_idx,
        record_id=record_id,
        title=title,
        doi_raw=doi_raw,
        doi_link_raw=doi_link_raw,
        file_name=file_name,
        pdf_path=pdf_path,
        relative_path=relative_path,
    )


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
    set_cell(
        ws,
        row_idx,
        col_map,
        "pdf_http_status",
        result.pdf_http_status if result.pdf_http_status is not None else "",
    )
    set_cell(ws, row_idx, col_map, "pdf_checked_at", result.pdf_checked_at)


def safe_save_workbook(wb, output_path: Path, max_attempts: int = 2) -> bool:
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
```

### O que faz
É o módulo responsável pela interação com o workbook Excel.

---

## 6.7 `resolvers/__init__.py`

```python
# resolvers/__init__.py
```

### O que faz
Marca a pasta como pacote Python.

---

## 6.8 `resolvers/base_download.py`

```python
from __future__ import annotations

import re
from typing import List, Optional, Tuple
from urllib.parse import urljoin

import requests

from app.config import CONNECT_TIMEOUT, HEADERS, READ_TIMEOUT
from app.models import DownloadResult, Record
from app.session_factory import build_session
from app.utils import deduplicate_urls, make_doi_url, normalize_doi, now_str, save_pdf_bytes


def response_looks_like_pdf(resp: requests.Response) -> bool:
    content_type = (resp.headers.get("Content-Type") or "").lower()
    if "application/pdf" in content_type:
        return True

    try:
        return resp.content[:5] == b"%PDF-"
    except Exception:
        return False


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


def classify_html_failure(status_code: Optional[int], html: str) -> str:
    text = (html or "").lower()

    if status_code == 403:
        return "paywalled"

    paywall_markers = [
        "purchase pdf",
        "buy article",
        "access through your institution",
        "institutional access",
        "subscribe to journal",
        "get access",
        "login via institution",
        "rent this article",
    ]
    if any(marker in text for marker in paywall_markers):
        return "paywalled"

    metadata_markers = [
        "abstract",
        "references",
        "metrics",
        "article info",
    ]
    if any(marker in text for marker in metadata_markers):
        return "metadata_only"

    if status_code == 404:
        return "not_found"

    if status_code is not None and status_code >= 500:
        return "broken_link"

    return "manual_check"


def make_result(
    record: Record,
    downloaded: int,
    status: str,
    source_url: str = "",
    local_path: str = "",
    http_status: Optional[int] = None,
) -> DownloadResult:
    return DownloadResult(
        pdf_downloaded=downloaded,
        pdf_download_status=status,
        pdf_file_name=record.file_name,
        pdf_source_url=source_url,
        pdf_local_path=local_path,
        pdf_http_status=http_status,
        pdf_checked_at=now_str(),
    )


def try_download_from_url(
    url: str,
    session: requests.Session,
) -> Tuple[bool, str, Optional[int], Optional[bytes], str]:
    try:
        resp = session.get(
            url,
            headers=HEADERS,
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            allow_redirects=True,
        )
        http_status = resp.status_code
        final_url = resp.url

        if http_status >= 400:
            if http_status == 403:
                return False, "paywalled", http_status, None, final_url
            if http_status == 404:
                return False, "not_found", http_status, None, final_url
            return False, "broken_link", http_status, None, final_url

        if response_looks_like_pdf(resp):
            return True, "downloaded", http_status, resp.content, final_url

        html = resp.text or ""
        pdf_url = extract_pdf_url_from_html(final_url, html)

        if pdf_url:
            pdf_resp = session.get(
                pdf_url,
                headers=HEADERS,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                allow_redirects=True,
            )
            pdf_http_status = pdf_resp.status_code
            pdf_final_url = pdf_resp.url

            if pdf_http_status >= 400:
                if pdf_http_status == 403:
                    return False, "paywalled", pdf_http_status, None, pdf_final_url
                if pdf_http_status == 404:
                    return False, "not_found", pdf_http_status, None, pdf_final_url
                return False, "broken_link", pdf_http_status, None, pdf_final_url

            if response_looks_like_pdf(pdf_resp):
                return True, "downloaded", pdf_http_status, pdf_resp.content, pdf_final_url

            return False, "manual_check", pdf_http_status, None, pdf_final_url

        return False, classify_html_failure(http_status, html), http_status, None, final_url

    except requests.Timeout:
        return False, "broken_link", None, None, url
    except requests.RequestException:
        return False, "broken_link", None, None, url


def build_candidate_urls(record: Record) -> List[str]:
    urls: List[str] = []

    doi_link = str(record.doi_link_raw or "").strip()
    doi = normalize_doi(record.doi_raw)

    if doi_link:
        urls.append(doi_link)

    if doi:
        urls.append(make_doi_url(doi))

    return deduplicate_urls(urls)


def try_base_download(record: Record, session: requests.Session) -> DownloadResult:
    if record.pdf_path.exists() and record.pdf_path.stat().st_size > 0:
        return make_result(
            record=record,
            downloaded=1,
            status="duplicate_pdf",
            local_path=record.relative_path,
        )

    candidate_urls = build_candidate_urls(record)

    if not candidate_urls:
        return make_result(
            record=record,
            downloaded=0,
            status="invalid_doi",
        )

    final_status = "not_found"
    final_http_status: Optional[int] = None
    final_source_url = ""

    for url in candidate_urls:
        success, status_label, http_status, pdf_bytes, final_url = try_download_from_url(url, session)

        final_status = status_label
        final_http_status = http_status
        final_source_url = final_url or url

        if success and pdf_bytes:
            saved = save_pdf_bytes(record.pdf_path, pdf_bytes)
            if saved:
                return make_result(
                    record=record,
                    downloaded=1,
                    status="downloaded",
                    source_url=final_source_url,
                    local_path=record.relative_path,
                    http_status=http_status,
                )

            final_status = "manual_check"
            final_http_status = http_status
            final_source_url = final_url or url

    return make_result(
        record=record,
        downloaded=0,
        status=final_status,
        source_url=final_source_url,
        http_status=final_http_status,
    )


def process_record_phase1(record: Record) -> Tuple[Record, DownloadResult]:
    session = build_session()
    try:
        result = try_base_download(record, session)
        return record, result
    finally:
        session.close()
```

### O que faz
Implementa a fase base de download.

---

## 6.9 `app/resolver_detector.py`

```python
from __future__ import annotations

from typing import Optional

from app.config import ENABLE_FRONTIERS_RESOLVER
from app.models import DownloadResult, Record
from app.utils import normalize_doi


def is_frontiers_candidate_from_values(
    doi_raw: str,
    doi_link_raw: str,
    source_url: str = "",
) -> bool:
    values = [
        str(doi_raw or "").strip(),
        str(doi_link_raw or "").strip(),
        str(source_url or "").strip(),
    ]

    normalized_doi = normalize_doi(doi_raw)
    normalized_doi_link = normalize_doi(doi_link_raw)

    if normalized_doi:
        values.append(normalized_doi)

    if normalized_doi_link:
        values.append(normalized_doi_link)

    lowered = [v.lower() for v in values if v]

    for value in lowered:
        if "frontiersin.org" in value:
            return True
        if "frontiers" in value:
            return True
        if value.startswith("10.3389/"):
            return True
        if "/10.3389/" in value:
            return True

    return False


def detect_specialized_resolver_name(
    record: Record,
    phase1_result: DownloadResult,
) -> Optional[str]:
    if ENABLE_FRONTIERS_RESOLVER and is_frontiers_candidate_from_values(
        doi_raw=record.doi_raw,
        doi_link_raw=record.doi_link_raw,
        source_url=phase1_result.pdf_source_url,
    ):
        return "frontiers"

    return None


def should_retry_in_phase2(result: DownloadResult) -> bool:
    return result.pdf_download_status != "downloaded"
```

### O que faz
Decide qual o resolver especializado aplicável.

---

## 6.10 `resolvers/frontiers.py`

```python
from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from app.config import (
    ENABLE_FRONTIERS_RESOLVER,
    FRONTIERS_ALLOWED_DOMAIN_PATTERN,
    FRONTIERS_DOWNLOAD_TIMEOUT_MS,
    FRONTIERS_HEADLESS,
    FRONTIERS_NAVIGATION_TIMEOUT_MS,
    FRONTIERS_POST_LOAD_WAIT_MS,
)
from app.models import DownloadResult, Record
from app.utils import make_doi_url, normalize_doi, now_str, save_pdf_bytes, url_matches_domain_pattern


def looks_like_pdf_url(href: str) -> bool:
    href_l = str(href or "").lower()
    return (
        "/pdf" in href_l
        or href_l.endswith(".pdf")
        or "download-a-pdf" in href_l
    )


def is_pdf_bytes_bytes(data: bytes) -> bool:
    return bool(data) and data.startswith(b"%PDF")


def make_result(
    record: Record,
    downloaded: int,
    status: str,
    source_url: str = "",
    local_path: str = "",
    http_status: Optional[int] = None,
) -> DownloadResult:
    return DownloadResult(
        pdf_downloaded=downloaded,
        pdf_download_status=status,
        pdf_file_name=record.file_name,
        pdf_source_url=source_url,
        pdf_local_path=local_path,
        pdf_http_status=http_status,
        pdf_checked_at=now_str(),
    )


def extract_doi_from_page(page, fallback_url: str | None = None) -> str:
    meta_selectors = [
        "meta[name='citation_doi']",
        "meta[name='dc.Identifier']",
        "meta[name='DC.Identifier']",
        "meta[name='dc.identifier']",
        "meta[name='DC.identifier']",
        "meta[name='prism.doi']",
        "meta[property='og:doi']",
    ]

    for selector in meta_selectors:
        try:
            locator = page.locator(selector).first
            if locator.count() > 0:
                content = locator.get_attribute("content")
                if content:
                    match = re.search(r"(10\.\d{4,9}/\S+)", content.strip(), re.I)
                    if match:
                        return match.group(1).rstrip(" .;,:)")
        except Exception:
            pass

    doi_link_selectors = [
        "a[href*='doi.org/']",
        "a[href*='dx.doi.org/']",
    ]

    for selector in doi_link_selectors:
        try:
            count = page.locator(selector).count()
            for idx in range(count):
                href = page.locator(selector).nth(idx).get_attribute("href")
                if not href:
                    continue
                match = re.search(r"doi\.org/(10\.\d{4,9}/\S+)", href, re.I)
                if match:
                    return match.group(1).rstrip(" .;,:)")
        except Exception:
            pass

    try:
        html = page.content()
        match = re.search(r"(10\.\d{4,9}/[^\s\"<>&]+)", html, re.I)
        if match:
            return match.group(1).rstrip(" .;,:)")
    except Exception:
        pass

    if fallback_url:
        match = re.search(r"(10\.\d{4,9}/\S+)", fallback_url, re.I)
        if match:
            return match.group(1).rstrip(" .;,:)")

    raise RuntimeError("Could not detect DOI from Frontiers page.")


def find_frontiers_pdf_href(page) -> Optional[str]:
    selectors = [
        "a[data-event='download-a-pdf']",
        "a.DownloadArticleButton_action",
        "a[href*='/pdf']",
        "a[href$='.pdf']",
        "li.ToolbarDownload a",
        "a.ToolbarDownload_action",
        "nav.Toolbar a[data-event='download-a-pdf']",
        "a:has-text('PDF')",
        "a:has-text('Download')",
    ]

    for selector in selectors:
        try:
            count = page.locator(selector).count()
            for idx in range(count):
                href = page.locator(selector).nth(idx).get_attribute("href")
                if href and looks_like_pdf_url(href):
                    return href
        except Exception:
            pass

    return None


def try_frontiers_resolver(record: Record) -> DownloadResult:
    if not ENABLE_FRONTIERS_RESOLVER:
        return make_result(
            record=record,
            downloaded=0,
            status="frontiers_resolver_disabled",
        )

    doi = normalize_doi(record.doi_raw)
    if not doi:
        doi = normalize_doi(record.doi_link_raw)

    if not doi:
        return make_result(
            record=record,
            downloaded=0,
            status="invalid_doi",
        )

    doi_url = make_doi_url(doi)

    if record.pdf_path.exists() and record.pdf_path.stat().st_size > 0:
        return make_result(
            record=record,
            downloaded=1,
            status="duplicate_pdf",
            source_url=doi_url,
            local_path=record.relative_path,
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=FRONTIERS_HEADLESS,
            args=["--disable-blink-features=AutomationControlled"],
        )

        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        try:
            page.goto(
                doi_url,
                wait_until="domcontentloaded",
                timeout=FRONTIERS_NAVIGATION_TIMEOUT_MS,
            )
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(FRONTIERS_POST_LOAD_WAIT_MS)

            final_page_url = page.url

            if not url_matches_domain_pattern(final_page_url, FRONTIERS_ALLOWED_DOMAIN_PATTERN):
                return make_result(
                    record=record,
                    downloaded=0,
                    status="not_frontiers",
                    source_url=final_page_url,
                )

            pdf_href = find_frontiers_pdf_href(page)
            _detected_doi = extract_doi_from_page(page, fallback_url=final_page_url)

            if not pdf_href:
                return make_result(
                    record=record,
                    downloaded=0,
                    status="pdf_link_not_found_frontiers",
                    source_url=final_page_url,
                )

            pdf_url = urljoin(final_page_url, pdf_href)

            try:
                response = context.request.get(
                    pdf_url,
                    headers={"Referer": final_page_url},
                    timeout=FRONTIERS_DOWNLOAD_TIMEOUT_MS,
                )

                if response.status == 200:
                    data = response.body()
                    if is_pdf_bytes_bytes(data):
                        if save_pdf_bytes(record.pdf_path, data):
                            return make_result(
                                record=record,
                                downloaded=1,
                                status="downloaded_frontiers",
                                source_url=pdf_url,
                                local_path=record.relative_path,
                                http_status=response.status,
                            )
            except Exception:
                pass

            selectors = [
                "a[data-event='download-a-pdf']",
                "a.DownloadArticleButton_action",
                "a[href*='/pdf']",
                "a[href$='.pdf']",
                "li.ToolbarDownload a",
                "a.ToolbarDownload_action",
                "nav.Toolbar a[data-event='download-a-pdf']",
                "a:has-text('PDF')",
                "a:has-text('Download')",
            ]

            for selector in selectors:
                try:
                    count = page.locator(selector).count()
                    for idx in range(count):
                        locator = page.locator(selector).nth(idx)
                        href = locator.get_attribute("href")
                        if not href or not looks_like_pdf_url(href):
                            continue

                        with page.expect_download(timeout=FRONTIERS_DOWNLOAD_TIMEOUT_MS) as download_info:
                            locator.click()

                        download = download_info.value
                        download.save_as(str(record.pdf_path))

                        if record.pdf_path.exists() and record.pdf_path.stat().st_size > 0:
                            return make_result(
                                record=record,
                                downloaded=1,
                                status="downloaded_frontiers",
                                source_url=pdf_url,
                                local_path=record.relative_path,
                            )
                except PlaywrightTimeoutError:
                    continue
                except Exception:
                    continue

            return make_result(
                record=record,
                downloaded=0,
                status="download_failed_frontiers",
                source_url=final_page_url,
            )

        finally:
            browser.close()
```

### O que faz
Implementa o resolver especializado para Frontiers usando Playwright.

---

## 6.11 `app/pipeline.py`

```python
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
    if reporter is None:
        return
    reporter(event_name, payload)


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
```

### O que faz
É o coração da aplicação:
- corre fase 1;
- corre fase 2;
- escreve resultados;
- emite eventos para terminal ou Streamlit.

---

## 6.12 `ui/__init__.py`

```python
# ui/__init__.py
```

---

## 6.13 `ui/terminal_dashboard.py`

```python
from __future__ import annotations

import os
import sys
import time
from typing import Dict, List, Optional

from app.config import FORCE_SIMPLE_TERMINAL, FRAME_WIDTH
from app.utils import format_seconds


class TerminalDashboard:
    def __init__(self) -> None:
        self.terminal_mode = "simple"
        self.phase1_rendered = False
        self.phase2_rendered = False
        self.phase1_last_height = 0
        self.phase2_last_height = 0
        self.phase1_lines: List[str] = []
        self.phase2_lines: List[str] = []

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

    def _render_block_in_place(self, lines: List[str], already_rendered: bool, last_height: int) -> int:
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

    def render_simple_combined(self, phase1_lines: List[str], phase2_lines: Optional[List[str]] = None) -> None:
        self.clear_screen_simple()
        sys.stdout.write("\n".join(self.normalize_block(phase1_lines)))
        sys.stdout.write("\n")

        if phase2_lines:
            sys.stdout.write("\n")
            sys.stdout.write("\n".join(self.normalize_block(phase2_lines)))
            sys.stdout.write("\n")

        sys.stdout.flush()

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
```

### O que faz
Mostra o progresso no terminal sem duplicação descontrolada de blocos.

---

## 6.14 `main.py`

```python
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
```

### O que faz
É o entry point do modo terminal.

---

## 6.15 `ui/components.py`

```python
from __future__ import annotations

import time
from typing import Dict, List

import streamlit as st

from app.utils import format_seconds


def ensure_streamlit_state() -> None:
    defaults = {
        "logs": [],
        "phase1_payload": None,
        "phase2_payload": None,
        "final_summary": None,
        "save_events": [],
        "run_status": "idle",
        "run_error": "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def append_log(message: str) -> None:
    ensure_streamlit_state()
    timestamp = time.strftime("%H:%M:%S")
    st.session_state["logs"].append(f"[{timestamp}] {message}")


def build_phase1_lines(payload: Dict) -> List[str]:
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
        "PHASE 1 - BASE DOWNLOAD",
        f"Processed               : {processed}",
        f"Remaining               : {remaining_count}",
        f"Total                   : {total}",
        f"Workers                 : {workers}",
        f"PDFs available          : {pdfs_available_global}",
        f"Downloaded now          : {downloaded_now_total}",
        f"Failures                : {failures_count}",
        f"Global success rate     : {success_rate_global:6.2f}%",
        f"Elapsed                 : {format_seconds(elapsed)}",
        f"Estimated total         : {format_seconds(estimated_total)}",
        f"Estimated remaining     : {format_seconds(estimated_remaining)}",
        f"Last record             : {last_record_id or '-'}",
        f"Last status             : {last_status or '-'}",
    ]


def build_phase2_lines(payload: Dict) -> List[str]:
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
        "PHASE 2 - SPECIALIZED RETRY",
        f"Resolver                : {resolver_name or '-'}",
        f"Retry total             : {retry_total}",
        f"Processed               : {retry_processed}",
        f"Remaining               : {retry_remaining}",
        f"PDFs available          : {pdfs_available_global}",
        f"Downloaded now          : {downloaded_now_total}",
        f"Recovered this phase    : {recovered_this_phase}",
        f"Still without PDF       : {phase2_still_without_pdf}",
        f"Global success rate     : {success_rate_global:6.2f}%",
        f"Elapsed                 : {format_seconds(elapsed)}",
        f"Estimated total         : {format_seconds(estimated_total)}",
        f"Estimated remaining     : {format_seconds(estimated_remaining)}",
        f"Last record             : {last_record_id or '-'}",
        f"Last DOI                : {last_doi or '-'}",
        f"Last status             : {last_status or '-'}",
    ]


def make_streamlit_reporter():
    ensure_streamlit_state()

    def reporter(event_name: str, payload: dict) -> None:
        if event_name in {"phase1_start", "phase1_update", "phase1_end"}:
            st.session_state["phase1_payload"] = payload

            if event_name == "phase1_start":
                append_log("Phase 1 started.")
            elif event_name == "phase1_end":
                append_log("Phase 1 finished.")

        elif event_name in {"phase2_start", "phase2_update", "phase2_end"}:
            st.session_state["phase2_payload"] = payload

            if event_name == "phase2_start":
                append_log("Phase 2 started.")
            elif event_name == "phase2_end":
                append_log("Phase 2 finished.")

        elif event_name == "save":
            st.session_state["save_events"].append(payload)
            append_log(
                f"Workbook save event | phase={payload.get('phase')} | ok={payload.get('ok')}"
            )

        elif event_name == "finish":
            st.session_state["final_summary"] = payload
            append_log("Pipeline finished.")

    return reporter


def render_status_panels() -> None:
    ensure_streamlit_state()

    phase1_payload = st.session_state.get("phase1_payload")
    phase2_payload = st.session_state.get("phase2_payload")
    final_summary = st.session_state.get("final_summary")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Phase 1")
        if phase1_payload:
            st.code("\n".join(build_phase1_lines(phase1_payload)), language="text")
        else:
            st.info("Phase 1 not started yet.")

    with col2:
        st.subheader("Phase 2")
        if phase2_payload:
            st.code("\n".join(build_phase2_lines(phase2_payload)), language="text")
        else:
            st.info("Phase 2 not started yet.")

    st.subheader("Logs")
    logs = st.session_state.get("logs", [])
    st.text_area(
        "Execution log",
        value="\n".join(logs),
        height=250,
        label_visibility="collapsed",
    )

    if final_summary:
        st.subheader("Final summary")
        phase2 = final_summary["phase2"]

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("PDFs available", phase2["pdfs_available_global"])
        with c2:
            st.metric("Downloaded now", phase2["downloaded_now_total"])
        with c3:
            st.metric("Recovered in phase 2", phase2["recovered_this_phase"])

        st.write(f"**Output workbook:** `{final_summary['output_workbook_path']}`")


def reset_run_state() -> None:
    st.session_state["logs"] = []
    st.session_state["phase1_payload"] = None
    st.session_state["phase2_payload"] = None
    st.session_state["final_summary"] = None
    st.session_state["save_events"] = []
    st.session_state["run_status"] = "idle"
    st.session_state["run_error"] = ""
```

### O que faz
Fornece a camada de reporte e rendering da interface Streamlit.

---

## 6.16 `ui/streamlit_app.py`

```python
from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from app.config import MAX_ROWS_TO_PROCESS, PDF_BASE_DIR, SHEET_NAME, build_output_workbook_path, resolve_workbook_path
from app.excel_io import build_col_map, collect_records, load_workbook_and_sheet, safe_save_workbook, validate_required_columns
from app.pipeline import run_full_pipeline
from ui.components import ensure_streamlit_state, make_streamlit_reporter, render_status_panels, reset_run_state, append_log


st.set_page_config(page_title="PDF Downloader Tool", layout="wide")


def save_uploaded_file_to_temp(uploaded_file) -> Path:
    suffix = Path(uploaded_file.name).suffix or ".xlsx"
    temp_dir = Path(tempfile.gettempdir())
    temp_path = temp_dir / uploaded_file.name

    temp_path.write_bytes(uploaded_file.getbuffer())
    return temp_path


def main() -> None:
    ensure_streamlit_state()

    st.title("PDF Downloader Tool")
    st.write("Run the same pipeline through a Streamlit interface.")

    with st.sidebar:
        st.header("Input workbook")
        mode = st.radio(
            "Workbook source",
            ["Automatic workbook", "Upload workbook"],
            index=0,
        )

        uploaded_file = None
        if mode == "Upload workbook":
            uploaded_file = st.file_uploader(
                "Upload .xlsx workbook",
                type=["xlsx"],
            )

        st.header("Actions")
        run_clicked = st.button("Run pipeline", use_container_width=True)
        reset_clicked = st.button("Reset UI state", use_container_width=True)

    if reset_clicked:
        reset_run_state()
        st.rerun()

    workbook_path = None
    output_workbook_path = None

    if mode == "Automatic workbook":
        try:
            workbook_path = resolve_workbook_path()
            output_workbook_path = build_output_workbook_path(workbook_path)
            st.info(f"Using workbook: `{workbook_path}`")
        except Exception as exc:
            st.error(f"Could not resolve workbook automatically: {exc}")

    elif mode == "Upload workbook":
        if uploaded_file is not None:
            workbook_path = save_uploaded_file_to_temp(uploaded_file)
            output_workbook_path = workbook_path.with_name(f"{workbook_path.stem}_pdf_downloaded.xlsx")
            st.info(f"Using uploaded workbook: `{workbook_path}`")
        else:
            st.warning("Upload a workbook to continue.")

    if run_clicked:
        if workbook_path is None:
            st.error("No valid workbook is available.")
        else:
            reset_run_state()
            st.session_state["run_status"] = "running"

            PDF_BASE_DIR.mkdir(parents=True, exist_ok=True)

            try:
                append_log(f"Opening workbook: {workbook_path}")

                wb, ws = load_workbook_and_sheet(workbook_path, SHEET_NAME)
                col_map = build_col_map(ws)
                validate_required_columns(col_map, SHEET_NAME)

                records = collect_records(ws, col_map, MAX_ROWS_TO_PROCESS)
                if not records:
                    raise ValueError("No records found to process.")

                append_log(f"Records loaded: {len(records)}")

                reporter = make_streamlit_reporter()

                final_summary = run_full_pipeline(
                    wb=wb,
                    ws=ws,
                    col_map=col_map,
                    records=records,
                    output_workbook_path=output_workbook_path,
                    reporter=reporter,
                )

                st.session_state["final_summary"] = final_summary
                st.session_state["run_status"] = "finished"

                append_log("Run completed successfully.")

            except KeyboardInterrupt:
                st.session_state["run_status"] = "interrupted"
                append_log("Run interrupted by user.")

                try:
                    ok = safe_save_workbook(wb, output_workbook_path)
                    append_log(f"Emergency save completed: {ok}")
                except Exception as save_exc:
                    append_log(f"Emergency save failed: {save_exc}")

            except Exception as exc:
                st.session_state["run_status"] = "error"
                st.session_state["run_error"] = str(exc)
                append_log(f"Run failed: {exc}")

                try:
                    ok = safe_save_workbook(wb, output_workbook_path)
                    append_log(f"Partial save completed: {ok}")
                except Exception as save_exc:
                    append_log(f"Partial save failed: {save_exc}")

    status = st.session_state.get("run_status", "idle")
    if status == "running":
        st.warning("Pipeline is running.")
    elif status == "finished":
        st.success("Pipeline finished.")
    elif status == "error":
        st.error(f"Pipeline failed: {st.session_state.get('run_error', '')}")
    elif status == "interrupted":
        st.warning("Pipeline interrupted.")

    render_status_panels()

    final_summary = st.session_state.get("final_summary")
    if final_summary:
        output_path = Path(final_summary["output_workbook_path"])
        if output_path.exists():
            with open(output_path, "rb") as f:
                st.download_button(
                    label="Download output workbook",
                    data=f.read(),
                    file_name=output_path.name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )


if __name__ == "__main__":
    main()
```

### O que faz
É o entry point da app Streamlit.

---

## 6.17 `run_terminal.bat`

```bat
@echo off
setlocal

cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXE=.venv\Scripts\python.exe
) else if exist "venv\Scripts\python.exe" (
    set PYTHON_EXE=venv\Scripts\python.exe
) else (
    echo ERRO: nao foi encontrado um ambiente virtual em .venv ou venv
    echo Cria primeiro o ambiente virtual nesta pasta do projeto.
    pause
    exit /b 1
)

"%PYTHON_EXE%" main.py

pause
```

### O que faz
Arranca a aplicação em modo terminal usando diretamente o Python do venv.

---

## 6.18 `run_streamlit.bat`

```bat
@echo off
setlocal

cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXE=.venv\Scripts\python.exe
) else if exist "venv\Scripts\python.exe" (
    set PYTHON_EXE=venv\Scripts\python.exe
) else (
    echo ERRO: nao foi encontrado um ambiente virtual em .venv ou venv
    echo Cria primeiro o ambiente virtual nesta pasta do projeto.
    pause
    exit /b 1
)

"%PYTHON_EXE%" -m streamlit run ui\streamlit_app.py

pause
```

### O que faz
Arranca a aplicação em modo Streamlit.

---

## 6.19 `requirements.txt`

```text
openpyxl
playwright
requests
streamlit
urllib3
```

---

# 7. Como tudo foi feito

## 7.1 Base de partida
O ponto de partida foi um script monolítico que já fazia:
- download base;
- paralelização da fase 1;
- retry especializado Frontiers;
- dashboard de terminal.

## 7.2 Estratégia de refatoração
A estratégia seguida foi:

1. separar configuração;
2. separar modelos;
3. separar funções utilitárias;
4. separar Excel I/O;
5. separar fase base de download;
6. separar deteção de resolvers;
7. separar resolver Frontiers;
8. criar uma pipeline única;
9. criar uma UI terminal;
10. criar uma UI Streamlit.

## 7.3 Princípio mais importante
A aplicação ficou desenhada com **uma só pipeline** e **duas interfaces**.

---

# 8. Ponto de situação para retomar num novo chat

Ao abrir um novo chat, este é o estado que deve ser assumido:

## 8.1 Objetivo já definido
O objetivo é manter e evoluir uma app local Python para descarregar PDFs com:
- terminal;
- Streamlit;
- resolvers modulares.

## 8.2 Arquitetura já definida
A arquitetura modular acima descrita deve ser assumida como a estrutura alvo.

## 8.3 Scripts já redigidos
Os scripts incluídos neste documento correspondem à base de implementação proposta.

## 8.4 Problema real mais recente observado
Foi identificado que o `.bat` falhava porque:
- não existia ainda `.venv`;
- o Python global não tinha Streamlit;
- a solução foi passar a usar `.venv\Scripts\python.exe` diretamente.

## 8.5 Documentação já criada
Já foram criados:
- manual geral;
- versão melhorada;
- versão profissional;
- versão premium;
- conjunto documental separado (`README`, `USER_GUIDE`, etc.).

---

# 9. O que falta validar

## 9.1 Instalação real
Ainda é necessário validar em ambiente real:
- criação do `.venv`;
- instalação de dependências;
- instalação do Chromium do Playwright.

## 9.2 Execução real
Ainda é necessário validar:
- `python main.py`
- `python -m streamlit run ui\streamlit_app.py`

## 9.3 Integração com workbook real
É necessário testar com:
- workbook verdadeiro;
- sheet verdadeira;
- colunas reais.

## 9.4 Robustez futura
Melhorias futuras recomendadas:
- logging persistente;
- argumentos CLI;
- novos resolvers;
- testes unitários;
- testes de integração.

---

# 10. Ordem recomendada para o próximo trabalho

Se este documento for carregado num novo chat, a sequência recomendada é:

1. confirmar a estrutura atual da pasta do projeto;
2. confirmar que `.venv` existe;
3. confirmar que `requirements.txt` está instalado;
4. testar o modo terminal;
5. testar o modo Streamlit;
6. validar com poucos registos;
7. só depois corrigir ou expandir.

---

# 11. Resumo final

Este documento deve ser interpretado como:

- **snapshot técnico do projeto**;
- **referência de continuidade**;
- **base para retomar o desenvolvimento num novo chat**.

A aplicação já está conceptual e estruturalmente definida.  
O trabalho seguinte deve concentrar-se em:

- validação em ambiente real;
- correção de incompatibilidades locais;
- expansão dos resolvers;
- robustez adicional.


---

# 12. Instruções para abrir um novo chat com este projeto

Quando este ficheiro for carregado num novo chat, o texto abaixo pode ser usado como instrução base para retomar o trabalho sem perder contexto.

## Texto recomendado para colar no novo chat

Carreguei um ficheiro chamado **`PDF_Downloader_Tool_Project_Snapshot.md`**.  
Quero que o uses como **fonte principal de contexto** para este projeto.

### Instruções para este chat

1. Lê primeiro o ficheiro completo antes de propôr alterações.
2. Assume que a arquitetura alvo do projeto é a descrita nesse ficheiro.
3. Assume que o projeto é uma app local Python para:
   - descarregar PDFs a partir de um workbook Excel;
   - correr em **modo terminal**;
   - correr em **modo Streamlit**;
   - usar **resolvers modulares** por publisher/site.
4. Assume que os scripts incluídos no ficheiro representam o **estado atual proposto da implementação**.
5. Antes de sugerires novas refatorações, confirma sempre:
   - o que já está feito;
   - o que falta validar;
   - o que é arquitetura alvo vs. o que já foi realmente testado.
6. Dá prioridade a:
   - funcionalidade real;
   - robustez;
   - compatibilidade com o script original;
   - soluções leves e claras;
   - implementação passo a passo.
7. Não mudes a arquitetura sem justificação forte.
8. Quando propuseres alterações:
   - indica exatamente que ficheiros mudam;
   - mostra o código completo atualizado;
   - explica porque a alteração é necessária.
9. Assume que eu quero instruções muito claras, passo a passo, como se soubesse pouco sobre setup técnico.
10. Sempre que houver dúvida entre “mais elegante” e “mais fiável/prático”, prefere o caminho mais fiável e prático.
11. Se identificares inconsistências entre o snapshot e o código real, assinala isso explicitamente.
12. Quando responderes, parte sempre deste enquadramento:
   - arquitetura modular já definida;
   - snapshot já criado;
   - próximo foco = validação real, correção de erros locais e expansão controlada.

### Objetivo imediato neste novo chat

Quero continuar este projeto a partir do ponto em que o snapshot ficou.  
Antes de avançares, faz primeiro:

1. um resumo curto do estado atual com base no ficheiro;
2. uma lista do que já está feito;
3. uma lista do que falta validar/testar;
4. uma proposta do próximo passo mais lógico.

## Versão curta para uso rápido

Li e usa o ficheiro `PDF_Downloader_Tool_Project_Snapshot.md` como contexto principal.  
Assume que a arquitetura modular descrita nesse ficheiro é a arquitetura alvo do projeto.  
Quero continuar a partir do ponto de situação guardado nesse snapshot, com foco em validação real, robustez e implementação passo a passo.  
Antes de propôres mudanças, resume o estado atual, diz o que já está feito, o que falta validar e qual o próximo passo mais lógico.
