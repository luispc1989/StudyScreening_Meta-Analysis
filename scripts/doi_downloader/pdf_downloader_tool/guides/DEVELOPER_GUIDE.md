# DEVELOPER_GUIDE.md — Guia do Programador

## 1. Objetivo

Este guia destina-se a quem pretende manter, adaptar ou expandir a aplicação.

## 2. Arquitetura

### `app/`
Contém a lógica principal:
- `config.py`
- `excel_io.py`
- `models.py`
- `pipeline.py`
- `resolver_detector.py`
- `session_factory.py`
- `utils.py`

### `resolvers/`
Contém a lógica específica por site.

### `ui/`
Contém a camada de apresentação.

## 3. Princípios de arquitetura

- uma única pipeline
- múltiplas interfaces
- separação por responsabilidade
- um resolver por site
- UI sem lógica pesada
- pipeline sem dependência direta de terminal ou Streamlit

## 4. Fluxo interno

1. abrir workbook
2. validar colunas
3. construir `Record`
4. correr fase 1
5. escrever resultados
6. construir retry tasks
7. correr fase 2
8. guardar workbook
9. emitir eventos para UI

## 5. Modelos principais

### `Record`
Representa uma linha do Excel.

### `DownloadResult`
Representa o resultado final do processamento de um registo.

### `RetryTask`
Representa uma tarefa especializada da fase 2.

## 6. Onde alterar comportamento

| Objetivo | Ficheiro |
|---|---|
| alterar caminhos/configuração | `app/config.py` |
| alterar leitura/escrita Excel | `app/excel_io.py` |
| alterar pipeline | `app/pipeline.py` |
| alterar deteção de sites | `app/resolver_detector.py` |
| criar novos resolvers | `resolvers/` |
| alterar terminal | `ui/terminal_dashboard.py` |
| alterar Streamlit | `ui/streamlit_app.py`, `ui/components.py` |

## 7. Como adicionar um resolver

Exemplo: `mdpi`

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
Em `app/resolver_detector.py`, criar função do tipo:
```python
def is_mdpi_candidate_from_values(...):
    ...
```

### Passo 4 — integrar deteção principal
Atualizar `detect_specialized_resolver_name(...)` para devolver `"mdpi"`.

### Passo 5 — integrar na pipeline
Em `app/pipeline.py`:
```python
if resolver_name == "mdpi":
    return try_mdpi_resolver(record)
```

### Passo 6 — flag opcional
Em `app/config.py`:
```python
ENABLE_MDPI_RESOLVER = True
```

## 8. Convenções de desenvolvimento

Cada resolver deve:
- estar num ficheiro próprio;
- conhecer apenas o seu site;
- não mexer em Excel;
- não renderizar UI;
- não imprimir diretamente;
- devolver sempre `DownloadResult`.

A pipeline deve:
- manter-se independente da UI;
- comunicar por eventos;
- não usar `print()` para progresso;
- não usar `st.write()`.

A UI deve:
- apresentar estado;
- não duplicar lógica de download;
- não conter parsing de sites.

## 9. Estratégia de teste

### Teste rápido
Em `config.py`:
```python
MAX_ROWS_TO_PROCESS = 20
```

### Validar terminal
```bat
.venv\Scripts\python.exe main.py
```

### Validar Streamlit
```bat
.venv\Scripts\python.exe -m streamlit run ui\streamlit_app.py
```

### Validar output
Confirmar:
- workbook criado
- PDFs gerados
- estados escritos
- sem regressões

## 10. Evoluções futuras recomendadas

- logging estruturado em ficheiro
- argumentos CLI
- suporte a mais publishers
- testes unitários
- testes de integração
- modo background para Streamlit
