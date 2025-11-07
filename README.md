# Título Provisório da Dissertação

> Estrutura-base para o repositório Git da dissertação. Criado em 2025-11-07.

## Objetivos
- Descrever sucintamente o problema, contexto e objetivos.
- Identificar perguntas de investigação e hipóteses.

## Estrutura do repositório
```
data/                # dados (ver secção 'Dados e LFS')
docs/                # material de escrita e elementos de submissão
models/              # modelos treinados e metadados
notebooks/           # Jupyter notebooks organizados por etapa
references/          # bibliografia (.bib) e normas
reports/             # figuras, tabelas e artefactos para o relatório
scripts/             # scripts CLI para tarefas repetíveis
src/dissertacao/     # pacote Python com código reutilizável
tests/               # testes automáticos (pytest)
config/              # ficheiros de configuração (YAML/ENV)
.github/workflows/   # CI (lint, testes, build de relatório)
```

## Requisitos mínimos
- Python 3.10+
- (Opcional) R 4.3+
- Git LFS para ficheiros grandes


## Dados e LFS
- **data/raw/** e **data/external/** são *write-only* no repositório (não versionar CSVs/ZIPs pesados sem LFS).
- Use `README.md` dentro de cada subpasta para descrever origem, licença e esquema dos dados.

## Reprodutibilidade
- Configuração em `config/config.yaml` e variáveis sensíveis em `.env` (não versionado).
- Entradas por linha de comando via `scripts/`.
- Testes em `tests/`.

## Citações e bibliografia
- Use `references/referencias.bib` e CSL de acordo com o estilo da faculdade.
- Faça citações consistentes no relatório (docs/relatorio).

