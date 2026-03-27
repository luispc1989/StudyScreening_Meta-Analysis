# USER_GUIDE.md — Manual do Utilizador

## 1. Objetivo

Este guia explica como usar a aplicação **PDF Downloader Tool** passo a passo, assumindo que o utilizador não tem experiência técnica.

## 2. O que a aplicação faz

A aplicação:

- lê um workbook Excel;
- tenta descarregar PDFs automaticamente;
- escreve o estado de cada tentativa no Excel;
- guarda PDFs numa pasta local;
- pode ser usada em terminal ou em Streamlit.

## 3. Requisitos

Antes de começar, deves ter:

- Windows
- Python instalado
- internet para instalar dependências
- a pasta do projeto completa

## 4. Instalação inicial

### Passo 1 — abrir a pasta do projeto
Abre `pdf_downloader_tool` no Explorador do Windows.

### Passo 2 — abrir uma consola nessa pasta
Na barra do caminho, escreve:

```bat
cmd
```

e carrega Enter.

### Passo 3 — criar o ambiente virtual

```bat
py -m venv .venv
```

Se falhar:

```bat
python -m venv .venv
```

### Passo 4 — instalar dependências

```bat
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m playwright install chromium
```

### Passo 5 — confirmar instalação

```bat
.venv\Scripts\python.exe -m streamlit --version
```

## 5. Como usar em modo terminal

### Método A — duplo clique
Clica em:

```text
run_terminal.bat
```

### Método B — consola

```bat
.venv\Scripts\python.exe main.py
```

### O que vais ver
No terminal aparecem métricas como:
- artigos diagnosticados
- PDFs disponíveis
- falhas
- tempo estimado
- último registo
- último estado

## 6. Como usar em modo Streamlit

### Método A — duplo clique
Clica em:

```text
run_streamlit.bat
```

### Método B — consola

```bat
.venv\Scripts\python.exe -m streamlit run ui\streamlit_app.py
```

### O que a interface permite
Na barra lateral podes:
- usar workbook automático
- carregar workbook manualmente
- correr a pipeline
- limpar o estado da interface

## 7. Workbook por defeito

O workbook é definido em:

```text
app/config.py
```

A aplicação:
1. usa `PREFERRED_WORKBOOK_PATH` se existir;
2. se não existir, usa o `.xlsx` mais recente em `EXCEL_INPUT_DIR`.

## 8. Colunas obrigatórias

### Entrada
- `record_id`
- `Title`
- `DOI`
- `DOI Link`

### Saída
- `pdf_downloaded`
- `pdf_download_status`
- `pdf_file_name`
- `pdf_source_url`
- `pdf_local_path`
- `pdf_http_status`
- `pdf_checked_at`

## 9. Estados principais

| Estado | Significado |
|---|---|
| `downloaded` | PDF descarregado com sucesso |
| `duplicate_pdf` | PDF já existia |
| `invalid_doi` | DOI ausente/inválido |
| `paywalled` | barreira de acesso |
| `not_found` | recurso não encontrado |
| `broken_link` | falha técnica |
| `metadata_only` | só página descritiva |
| `manual_check` | rever manualmente |
| `downloaded_frontiers` | descarregado por resolver Frontiers |

## 10. Onde ficam os resultados

### Workbook final
O ficheiro final recebe o sufixo:

```text
_pdf_downloaded.xlsx
```

### PDFs
Os PDFs ficam em `PDF_BASE_DIR`.

## 11. Primeira validação recomendada

Antes de correr muitos registos, altera em `app/config.py`:

```python
MAX_ROWS_TO_PROCESS = 20
```

Depois testa primeiro em terminal.

## 12. Erros frequentes

### Ambiente virtual não encontrado
Cria `.venv`:

```bat
py -m venv .venv
```

### `No module named streamlit`
Instala dependências no `.venv`:

```bat
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Sheet não encontrada
Confirma `SHEET_NAME` em `app/config.py`.

### Colunas em falta
Confirma que o Excel tem as colunas obrigatórias.

## 13. Ordem recomendada de utilização

1. Criar `.venv`
2. Instalar dependências
3. Testar `main.py`
4. Testar Streamlit
5. Correr com poucos registos
6. Validar resultados
