# PDF Downloader Tool — Manual Premium

> **Documento:** Manual de utilização premium  
> **Versão:** 4.0  
> **Estado:** operativo  
> **Destinatários:** utilizadores finais, utilizadores técnicos e programadores  
> **Objetivo:** instalação, utilização, validação, manutenção e extensão da aplicação

---

# Quick Start

Se queres apenas pôr a aplicação a funcionar rapidamente, segue estes passos na pasta `pdf_downloader_tool`:

```bat
py -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m playwright install chromium
.venv\Scripts\python.exe main.py
```

Para abrir a interface Streamlit:

```bat
.venv\Scripts\python.exe -m streamlit run ui\streamlit_app.py
```

---

# Índice

1. [Resumo executivo](#1-resumo-executivo)  
2. [O que a aplicação faz](#2-o-que-a-aplicação-faz)  
3. [Perfis de utilizador](#3-perfis-de-utilizador)  
4. [Estrutura do projeto](#4-estrutura-do-projeto)  
5. [Arquitetura e fluxo lógico](#5-arquitetura-e-fluxo-lógico)  
6. [Requisitos do sistema](#6-requisitos-do-sistema)  
7. [Instalação inicial passo a passo](#7-instalação-inicial-passo-a-passo)  
8. [Checklist de instalação validada](#8-checklist-de-instalação-validada)  
9. [Configuração principal da aplicação](#9-configuração-principal-da-aplicação)  
10. [Formato esperado do workbook Excel](#10-formato-esperado-do-workbook-excel)  
11. [Execução em modo terminal](#11-execução-em-modo-terminal)  
12. [Execução em modo Streamlit](#12-execução-em-modo-streamlit)  
13. [Estados de download e interpretação](#13-estados-de-download-e-interpretação)  
14. [Saídas produzidas pela aplicação](#14-saídas-produzidas-pela-aplicação)  
15. [Validação antes de produção](#15-validação-antes-de-produção)  
16. [Troubleshooting](#16-troubleshooting)  
17. [Adicionar novos resolvers](#17-adicionar-novos-resolvers)  
18. [Convenções de desenvolvimento](#18-convenções-de-desenvolvimento)  
19. [Guia rápido para utilizadores finais](#19-guia-rápido-para-utilizadores-finais)  
20. [Guia rápido para programadores](#20-guia-rápido-para-programadores)  
21. [Comandos de referência](#21-comandos-de-referência)  
22. [Fluxograma textual da aplicação](#22-fluxograma-textual-da-aplicação)  
23. [Resumo final](#23-resumo-final)  

---

# 1. Resumo executivo

A **PDF Downloader Tool** é uma aplicação local em Python que tenta descarregar automaticamente PDFs associados a registos bibliográficos guardados num workbook Excel.

A aplicação:

- lê um ficheiro Excel;
- tenta descarregar PDFs numa fase genérica;
- aplica resolvers especializados quando necessário;
- grava os resultados no workbook;
- funciona em:
  - **modo terminal**
  - **modo Streamlit**

A mesma lógica interna é reutilizada nos dois modos.  
A diferença está apenas na forma de interação e visualização.

---

# 2. O que a aplicação faz

Em termos simples, a aplicação percorre os registos do Excel e tenta responder, para cada linha, às seguintes perguntas:

- existe DOI utilizável?
- existe DOI Link utilizável?
- há PDF acessível diretamente?
- há uma página HTML que contém link para PDF?
- o site exige tratamento especializado?
- o PDF já existe na pasta local?
- qual foi o estado final do registo?

No final, a aplicação produz:

- um novo workbook com resultados atualizados;
- uma pasta com os PDFs descarregados;
- informação de progresso e diagnóstico.

---

# 3. Perfis de utilizador

## 3.1 Utilizador final
Quer apenas:
- instalar;
- correr;
- escolher workbook;
- ver progresso;
- obter o ficheiro final.

## 3.2 Utilizador técnico
Quer:
- ajustar configuração;
- validar estrutura de dados;
- fazer troubleshooting;
- testar workflows.

## 3.3 Programador
Quer:
- criar novos resolvers;
- melhorar a pipeline;
- alterar a arquitetura;
- acrescentar lógica especializada.

---

# 4. Estrutura do projeto

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

## 4.1 Função de cada zona

| Componente | Responsabilidade |
|---|---|
| `app/` | núcleo da lógica da aplicação |
| `resolvers/` | lógica específica por site/publisher |
| `ui/` | apresentação em terminal e Streamlit |
| `main.py` | entry point do modo terminal |
| `run_terminal.bat` | arranque rápido em terminal |
| `run_streamlit.bat` | arranque rápido em Streamlit |
| `requirements.txt` | dependências Python |

---

# 5. Arquitetura e fluxo lógico

## 5.1 Camadas

### Núcleo
A pasta `app/` contém:
- configuração;
- leitura/escrita de Excel;
- pipeline;
- deteção de resolvers;
- sessões HTTP;
- utilitários.

### Resolvers
A pasta `resolvers/` contém:
- lógica genérica (`base_download.py`);
- lógica especializada (`frontiers.py`, futuros `mdpi.py`, `springer.py`, etc.).

### Interface
A pasta `ui/` contém:
- dashboard de terminal;
- componentes Streamlit;
- aplicação Streamlit.

## 5.2 Princípio central
Há **uma única pipeline**.  
O terminal e o Streamlit apenas apresentam o progresso de formas diferentes.

---

# 6. Requisitos do sistema

## 6.1 Requisitos mínimos
- Windows
- Python instalado
- ligação à internet
- permissões de escrita na pasta do projeto

## 6.2 Bibliotecas usadas
As dependências estão em:

```text
requirements.txt
```

Exemplos:
- `requests`
- `openpyxl`
- `playwright`
- `streamlit`
- `urllib3`

## 6.3 Dependência adicional
O Playwright requer instalação do Chromium:

```bat
.venv\Scripts\python.exe -m playwright install chromium
```

---

# 7. Instalação inicial passo a passo

## 7.1 Abrir a pasta do projeto
Abre `pdf_downloader_tool` no Explorador do Windows.

## 7.2 Abrir a consola nessa pasta
Na barra do caminho, escreve:

```bat
cmd
```

e carrega Enter.

## 7.3 Confirmar a pasta atual

```bat
cd
```

## 7.4 Criar o ambiente virtual

```bat
py -m venv .venv
```

Se necessário:

```bat
python -m venv .venv
```

## 7.5 Confirmar que `.venv` existe

```bat
dir
```

## 7.6 Instalar dependências

```bat
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m playwright install chromium
```

## 7.7 Confirmar instalação

```bat
.venv\Scripts\python.exe -m streamlit --version
.venv\Scripts\python.exe -m playwright --version
```

---

# 8. Checklist de instalação validada

Marca cada item quando estiver concluído.

| Verificação | Estado esperado |
|---|---|
| Pasta `.venv` existe | Sim |
| `.venv\Scripts\python.exe` existe | Sim |
| `requirements.txt` instalado | Sim |
| Streamlit responde com versão | Sim |
| Playwright responde com versão | Sim |
| `main.py` arranca | Sim |
| `ui\streamlit_app.py` arranca | Sim |

---

# 9. Configuração principal da aplicação

O ficheiro principal de configuração é:

```text
app/config.py
```

## 9.1 Parâmetros críticos

| Parâmetro | Função |
|---|---|
| `EXTERNAL_WOS_DIR` | pasta base de trabalho |
| `EXCEL_INPUT_DIR` | pasta dos workbooks |
| `PDF_BASE_DIR` | pasta dos PDFs |
| `PREFERRED_WORKBOOK_PATH` | workbook preferido |
| `SHEET_NAME` | nome da folha Excel |
| `MAX_WORKERS` | número de workers paralelos |
| `MAX_ROWS_TO_PROCESS` | limite de linhas para teste |
| `ENABLE_FRONTIERS_RESOLVER` | ativa/desativa Frontiers |

## 9.2 Exemplo de ajuste seguro para teste

```python
MAX_ROWS_TO_PROCESS = 20
```

Isto é recomendado antes de correr grandes volumes de dados.

---

# 10. Formato esperado do workbook Excel

## 10.1 Colunas de entrada obrigatórias
- `record_id`
- `Title`
- `DOI`
- `DOI Link`

## 10.2 Colunas de saída obrigatórias
- `pdf_downloaded`
- `pdf_download_status`
- `pdf_file_name`
- `pdf_source_url`
- `pdf_local_path`
- `pdf_http_status`
- `pdf_checked_at`

## 10.3 Nota importante
Os nomes das colunas devem coincidir exatamente.

---

# 11. Execução em modo terminal

## 11.1 Quando usar
Usa o terminal quando:
- queres um workflow técnico;
- estás a depurar;
- queres comportamento semelhante ao script original.

## 11.2 Como arrancar

### Opção A — duplo clique
```text
run_terminal.bat
```

### Opção B — consola
```bat
.venv\Scripts\python.exe main.py
```

## 11.3 O que acontece
1. resolve o workbook;
2. abre a sheet;
3. valida colunas;
4. recolhe os registos;
5. corre fase 1;
6. corre fase 2;
7. grava o resultado;
8. mostra resumo.

---

# 12. Execução em modo Streamlit

## 12.1 Quando usar
Usa Streamlit quando:
- queres interface visual;
- queres upload manual;
- queres botão de download do resultado final.

## 12.2 Como arrancar

### Opção A — duplo clique
```text
run_streamlit.bat
```

### Opção B — consola
```bat
.venv\Scripts\python.exe -m streamlit run ui\streamlit_app.py
```

## 12.3 Funcionalidades
Na barra lateral, podes:
- escolher workbook automático;
- fazer upload manual;
- correr pipeline;
- reset da UI.

---

# 13. Estados de download e interpretação

| Estado | Significado |
|---|---|
| `downloaded` | PDF descarregado na fase base |
| `duplicate_pdf` | PDF já existia localmente |
| `invalid_doi` | DOI ausente ou inválido |
| `paywalled` | barreira de acesso |
| `not_found` | recurso não encontrado |
| `broken_link` | erro técnico de ligação |
| `metadata_only` | apenas página descritiva encontrada |
| `manual_check` | exige verificação manual |
| `downloaded_frontiers` | sucesso via resolver Frontiers |
| `not_frontiers` | a página final não corresponde a Frontiers |
| `pdf_link_not_found_frontiers` | página Frontiers sem link PDF utilizável |
| `download_failed_frontiers` | tentativa especializada falhou |

---

# 14. Saídas produzidas pela aplicação

## 14.1 Workbook final
O workbook final recebe o sufixo:

```text
_pdf_downloaded.xlsx
```

## 14.2 PDFs
Os PDFs são guardados em `PDF_BASE_DIR`.

---

# 15. Validação antes de produção

Antes de correr muitos registos, faz esta validação.

## 15.1 Validar ambiente

```bat
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe -m streamlit --version
.venv\Scripts\python.exe -m playwright --version
```

## 15.2 Validar com poucos registos
Em `config.py`:

```python
MAX_ROWS_TO_PROCESS = 20
```

## 15.3 Validar modo terminal

```bat
.venv\Scripts\python.exe main.py
```

## 15.4 Validar modo Streamlit

```bat
.venv\Scripts\python.exe -m streamlit run ui\streamlit_app.py
```

## 15.5 Verificar outputs
Confirmar:
- workbook final criado;
- PDFs na pasta correta;
- estados escritos corretamente;
- sem erros inesperados.

---

# 16. Troubleshooting

## 16.1 Tabela de problemas comuns

| Problema | Causa provável | Solução |
|---|---|---|
| ambiente virtual não encontrado | `.venv` não existe | criar `.venv` com `py -m venv .venv` |
| `No module named streamlit` | Streamlit não instalado no venv | instalar `requirements.txt` no `.venv` |
| caminho não encontrado | ficheiros/pastas em falta ou `.bat` mal localizado | confirmar estrutura do projeto |
| sheet não encontrada | `SHEET_NAME` incorreto | corrigir em `config.py` |
| colunas em falta | workbook incompatível | adicionar/alinhar colunas |
| Streamlit abre mas não processa | workbook inválido ou vazio | validar workbook, sheet e `record_id` |

## 16.2 Comandos de diagnóstico

```bat
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe -m streamlit --version
.venv\Scripts\python.exe -m playwright --version
.venv\Scripts\python.exe main.py
.venv\Scripts\python.exe -m streamlit run ui\streamlit_app.py
```

---

# 17. Adicionar novos resolvers

## 17.1 Exemplo: `mdpi`

### Passo 1 — criar ficheiro

```text
resolvers/mdpi.py
```

### Passo 2 — criar função principal

```python
from app.models import Record, DownloadResult

def try_mdpi_resolver(record: Record) -> DownloadResult:
    ...
```

### Passo 3 — criar deteção
No ficheiro `app/resolver_detector.py`, criar algo como:

```python
def is_mdpi_candidate_from_values(...):
    ...
```

### Passo 4 — integrar deteção principal
Na função `detect_specialized_resolver_name(...)`, devolver:

```python
return "mdpi"
```

### Passo 5 — integrar pipeline
Em `app/pipeline.py`, na função `process_record_phase2(...)`:

```python
if resolver_name == "mdpi":
    return try_mdpi_resolver(record)
```

### Passo 6 — flag opcional em `config.py`

```python
ENABLE_MDPI_RESOLVER = True
```

---

# 18. Convenções de desenvolvimento

## 18.1 Regras para novos resolvers
Cada resolver deve:
- estar num ficheiro próprio;
- conhecer apenas a lógica do seu site;
- não mexer em Excel;
- não fazer renderização;
- não depender de Streamlit;
- devolver sempre `DownloadResult`.

## 18.2 Regras para a pipeline
A pipeline deve:
- permanecer independente da UI;
- comunicar por eventos;
- não imprimir diretamente no terminal;
- não usar `st.write()`.

## 18.3 Regras para a UI
A UI deve:
- apenas apresentar progresso;
- não conter lógica pesada de download;
- não duplicar regras da pipeline.

---

# 19. Guia rápido para utilizadores finais

## Instalar
```bat
py -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m playwright install chromium
```

## Correr em terminal
```bat
.venv\Scripts\python.exe main.py
```

## Correr em Streamlit
```bat
.venv\Scripts\python.exe -m streamlit run ui\streamlit_app.py
```

## Melhor prática
Começar sempre com poucos registos.

---

# 20. Guia rápido para programadores

## Onde mexer

| Objetivo | Ficheiro |
|---|---|
| alterar caminhos e parâmetros | `app/config.py` |
| alterar leitura/escrita Excel | `app/excel_io.py` |
| alterar pipeline | `app/pipeline.py` |
| alterar deteção | `app/resolver_detector.py` |
| criar resolvers | `resolvers/` |
| alterar dashboard terminal | `ui/terminal_dashboard.py` |
| alterar Streamlit | `ui/streamlit_app.py`, `ui/components.py` |

---

# 21. Comandos de referência

| Objetivo | Comando |
|---|---|
| criar venv | `py -m venv .venv` |
| instalar dependências | `.venv\Scripts\python.exe -m pip install -r requirements.txt` |
| instalar Chromium | `.venv\Scripts\python.exe -m playwright install chromium` |
| correr terminal | `.venv\Scripts\python.exe main.py` |
| correr Streamlit | `.venv\Scripts\python.exe -m streamlit run ui\streamlit_app.py` |
| ver versão Streamlit | `.venv\Scripts\python.exe -m streamlit --version` |
| ver versão Playwright | `.venv\Scripts\python.exe -m playwright --version` |

---

# 22. Fluxograma textual da aplicação

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

# 23. Resumo final

A **PDF Downloader Tool** foi desenhada para ser:

- modular;
- leve;
- reutilizável;
- clara;
- extensível.

A ordem correta de utilização é:

1. instalar;
2. validar o ambiente;
3. testar com poucos registos;
4. validar outputs;
5. só depois escalar para volumes maiores ou acrescentar novos resolvers.
