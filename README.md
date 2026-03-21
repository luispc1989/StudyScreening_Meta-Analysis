# Título Provisório da Dissertação

> Estrutura-base do repositório Git da dissertação. Criado em 2025-11-07.

## Objetivos

- Descrever, de forma sucinta, o problema, o contexto e os objetivos da dissertação.
- Identificar as perguntas de investigação e as hipóteses de trabalho.
- Assegurar uma organização clara, reprodutível e auditável dos dados, scripts e resultados.

## Estrutura do repositório

```text
data/                # dados (ver secção 'Dados e LFS')
docs/                # material de escrita e elementos de submissão
models/              # modelos treinados e metadados
notebooks/           # Jupyter notebooks organizados por etapa
references/          # bibliografia (.bib) e normas
reports/             # figuras, tabelas e artefactos para o relatório
scripts/             # scripts CLI para tarefas repetíveis
src/dissertacao/     # pacote Python com código reutilizável
tests/               # testes automáticos (pytest)
configs/             # ficheiros de configuração (YAML/ENV)
.github/workflows/   # CI (lint, testes, build de relatório)
```

## Requisitos mínimos

- Python 3.10+
- (Opcional) R 4.3+
- Git LFS para ficheiros grandes

## Como começar

```bash
# 1) criar o repositório Git (na pasta raiz deste projeto)
git init
git add .
git commit -m "Bootstrap: estrutura da dissertação"

# 2) ativar Git LFS (opcional mas recomendado)
git lfs install
git lfs track "data/raw/**" "data/external/**" "models/**"

# 3) criar e ativar ambiente Python
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

# 4) pre-commit (formatadores e linters)
pre-commit install
```

## Dados e LFS

- **`data/raw/`** e **`data/external/`** devem ser tratados como diretórios de dados de origem.
- Evitar versionar ficheiros pesados (CSV/ZIP/XLSX de grande dimensão) sem Git LFS.
- Usar um `README.md` em cada subpasta de dados para documentar:
  - origem;
  - licença/condições de uso;
  - estrutura/esquema;
  - observações de pré-processamento.

## Reprodutibilidade

- Configuração em `configs/config.yaml` e variáveis sensíveis em `.env` (não versionado).
- Execução de tarefas repetíveis por linha de comando via `scripts/`.
- Código reutilizável em `src/dissertacao/`.
- Testes automáticos em `tests/`.
- Preservação de logs e artefactos intermédios relevantes para auditoria metodológica.

## Citações e bibliografia

- Usar `references/referencias.bib` e o ficheiro CSL de acordo com o estilo exigido pela faculdade.
- Manter consistência de citações no relatório e nos materiais de apoio.
- Centralizar referências e normas em `references/`.

## Pipeline de Study Screening (meta-análise)

Este repositório inclui um pipeline para preparação, limpeza, normalização e triagem inicial (*study screening*) de registos bibliográficos provenientes de múltiplas fontes:

- Web of Science (**WoS**)
- Google Scholar (**GS**) *(em desenvolvimento)*
- Grey Literature (**GL**) *(em desenvolvimento)*

### Objetivo do pipeline

Criar ficheiros de trabalho padronizados, rastreáveis e replicáveis para:

- documentar a pesquisa bibliográfica por fonte;
- consolidar e normalizar metadados;
- apoiar a triagem inicial por título e resumo;
- registar decisões de inclusão/exclusão;
- manter logs técnicos e relatórios de qualidade.

### Estado atual

- Implementado: `scripts/build_wos_workbook.py`
- Planeado: `scripts/build_gs_workbook.py`
- Planeado: `scripts/build_gl_workbook.py`
- Planeado: script de merge final (WoS + GS + GL)

### Outputs principais por execução (source-level)

Cada execução do script gera uma pasta de execução (*run folder*) com, pelo menos:

- `01_merged_cleaned.xlsx`
- `02_quality_report.xlsx`
- `03_duplicates_log.xlsx`
- `run_log.json`

Podem também ser gerados ficheiros CSV auxiliares (consoante a configuração do script).

### Documentação detalhada

Ver:

- `docs/README_pipeline.md`

## Convenções gerais do workflow (resumo)

- O processamento é feito **por fonte** (WoS, GS, GL) antes do merge final.
- A triagem inicial é feita em folhas de trabalho do tipo `*_screening_view`.
- A rastreabilidade é assegurada por identificadores e metadados de proveniência (ex.: `source_record_id`, `source`, `run_id`).
- Logs e relatórios devem ser preservados para suporte metodológico e auditoria.

## Licença

Indicar aqui a licença escolhida (ex.: `CC BY-NC 4.0`) ou **"All rights reserved"** até à submissão.