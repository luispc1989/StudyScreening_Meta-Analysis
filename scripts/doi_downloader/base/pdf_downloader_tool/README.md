# PDF Downloader Tool

Ferramenta local em Python para descarregar PDFs a partir de registos bibliográficos presentes num workbook Excel, com suporte para:

- execução em **modo terminal**;
- execução em **modo Streamlit**;
- lógica genérica de download;
- lógica especializada por publisher/site;
- atualização automática do workbook com estados de download.

## Estrutura da documentação

Este conjunto de documentação está dividido em ficheiros separados:

- `README.md` — visão geral do projeto e arranque rápido
- `USER_GUIDE.md` — manual do utilizador
- `DEVELOPER_GUIDE.md` — manual técnico para programadores
- `TROUBLESHOOTING.md` — resolução de problemas
- `CHANGELOG.md` — histórico inicial do projeto

## Quick Start

Na pasta `pdf_downloader_tool`, executa:

```bat
py -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m playwright install chromium
.venv\Scripts\python.exe main.py
```

Para abrir em Streamlit:

```bat
.venv\Scripts\python.exe -m streamlit run ui\streamlit_app.py
```

## Estrutura do projeto

```text
pdf_downloader_tool/
├── app/
├── resolvers/
├── ui/
├── logs/
├── old/
├── main.py
├── requirements.txt
├── run_streamlit.bat
└── run_terminal.bat
```

## Modos de utilização

### Modo terminal
Usa:

```bat
.venv\Scripts\python.exe main.py
```

ou:

```text
run_terminal.bat
```

### Modo Streamlit
Usa:

```bat
.venv\Scripts\python.exe -m streamlit run ui\streamlit_app.py
```

ou:

```text
run_streamlit.bat
```

## Ficheiros principais

### `app/`
Núcleo da aplicação:
- configuração
- Excel I/O
- pipeline
- modelos
- deteção de resolvers
- sessões HTTP
- utilitários

### `resolvers/`
Resolvers por site:
- `base_download.py`
- `frontiers.py`
- futuros resolvers como `mdpi.py`, `springer.py`, etc.

### `ui/`
Interfaces:
- terminal
- Streamlit

## Ordem recomendada de adoção

1. Criar `.venv`
2. Instalar dependências
3. Testar `main.py`
4. Testar Streamlit
5. Validar com poucos registos
6. Só depois escalar ou adicionar resolvers

## Documentação detalhada

Consulta os restantes ficheiros desta documentação para instruções completas.
