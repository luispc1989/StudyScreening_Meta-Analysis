# User Guide

## 1. Objetivo

Este guia explica como usar o PDF Fetcher no estado atual do projeto, com foco no modo terminal e no `S.C.O.U.T.`.

## 2. O que a ferramenta faz

O PDF Fetcher:

- le um workbook Excel;
- enriquece DOIs em falta;
- tenta descarregar PDFs automaticamente;
- usa resolvers especializados para publishers especificos;
- guarda o estado do workflow em workbooks por fase;
- permite revisao manual posterior no `S.C.O.U.T.`.

## 3. Requisitos

Antes de comecar, deves ter:

- Windows
- Python instalado
- o repositorio completo
- dependencias instaladas no `.venv`
- Chromium instalado via Playwright

## 4. Instalacao inicial

Na raiz do repositorio:

```bat
py -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m playwright install chromium
```

## 5. Como abrir o terminal

Na raiz do repositorio:

```bat
.venv\Scripts\python.exe -m tools.pdf_fetcher.ui.terminal.main
```

## 6. Session start

Ao abrir o terminal, o sistema pode mostrar:

- `Start new run from Input workbook`
- `Continue previous run from saved phase workbooks`

### Quando escolher `Start new run`

Escolhe esta opcao quando queres:

- comecar o workflow desde o workbook de input;
- recriar a `Phase 0` desde o inicio;
- testar uma corrida nova.

### Quando escolher `Continue previous run`

Escolhe esta opcao quando ja tens workbooks de fase guardados e queres:

- continuar o workflow de onde paraste;
- voltar a correr uma fase sobre o workbook ja gerado dessa fase;
- manter continuidade operacional entre sessoes.

## 7. Estrutura de ficheiros usada pela app

Dentro do projeto ativo, o PDF Fetcher usa principalmente:

- `PDF Fetcher/Excel/Input`
- `PDF Fetcher/Excel/Current`
- `PDF Fetcher/Excel/Final`
- `PDF Fetcher/PDFs`
- `PDF Fetcher/Reports/Phase 0`
- `PDF Fetcher/Reports/Phase 1`
- `PDF Fetcher/Reports/Phase 2`
- `PDF Fetcher/Reports/SCOUT`
- `PDF Fetcher/Checkpoints/Phase 0`
- `PDF Fetcher/Checkpoints/Phase 1`
- `PDF Fetcher/Checkpoints/Phase 2`
- `PDF Fetcher/Checkpoints/SCOUT`

Os ficheiros principais de trabalho por fase sao:

- `wos_workbook_current_phase_0.xlsx`
- `wos_workbook_current_phase_1.xlsx`
- `wos_workbook_current_phase_2.xlsx`

## 8. Fluxo recomendado

### Phase 0

Entrada:

- `PDF Fetcher/Excel/Input/wos_workbook_input.xlsx`

Saida:

- `PDF Fetcher/Excel/Current/wos_workbook_current_phase_0.xlsx`

### Phase 1

Entrada:

- `wos_workbook_current_phase_0.xlsx`

Saida:

- `wos_workbook_current_phase_1.xlsx`

### Phase 2

Entrada:

- `wos_workbook_current_phase_1.xlsx`

Saida:

- `wos_workbook_current_phase_2.xlsx`

### S.C.O.U.T.

Entrada:

- `wos_workbook_current_phase_2.xlsx`

O SCOUT gera uma sessao propria com os casos ainda por rever manualmente.

## 9. Menus principais do terminal

No menu inicial podes tipicamente:

- correr `Phase 0`
- correr `Phase 1`
- correr `Phase 2`
- correr diagnosticos
- abrir o `S.C.O.U.T.`
- sair da aplicacao

As opcoes concretas dependem do estado atual do projeto.

## 10. Interromper uma fase

Durante as fases, o terminal aceita:

- `P` - pause
- `V` - back to menu
- `S` - exit app

Se saires com `S`, a app tenta gravar um checkpoint para recuperacao.

## 11. Reports e checkpoints

Os reports ficam organizados por fase:

- `Reports/Phase 0`
- `Reports/Phase 1`
- `Reports/Phase 2`
- `Reports/SCOUT`

Os checkpoints tambem:

- `Checkpoints/Phase 0`
- `Checkpoints/Phase 1`
- `Checkpoints/Phase 2`
- `Checkpoints/SCOUT`

## 12. Como usar o S.C.O.U.T.

O `S.C.O.U.T.` e a camada manual de revisao depois da `Phase 2`.

No SCOUT podes:

- abrir `DOI Link`
- usar `Search Engine`
- enviar pedido por email ao autor
- inserir ou limpar `DOI Link` / `Source Link`
- atribuir decisao manual
- escrever notas

O SCOUT tambem:

- deteta downloads feitos a partir do browser;
- mostra o estado em `PDF Status`;
- preserva a memoria da revisao ate ao `Finalize To Workbook`;
- mostra o estado visual do artigo (`Pending Review` / `Reviewed`);
- permite `Erase PDF` quando um PDF errado foi guardado;
- devolve o caso a `Pending Review` quando esse PDF e apagado.

## 13. Continuidade de sessao no SCOUT

O SCOUT mantem memoria propria da revisao. Isso significa que:

- se fechares a app a meio;
- se o browser cair;
- ou se reabrir a sessao depois;

deves retomar o estado da revisao sem perder o trabalho ja registado.

## 14. O que fazer se quiseres recomecar do zero

Se quiseres recomecar o pipeline:

1. escolhe `Start new run from Input workbook`
2. corre novamente a `Phase 0`
3. continua o fluxo ate `Phase 2`

Isto recria os workbooks por fase a partir do input.

## 15. Notas importantes

- A `Phase 0` agora distingue entre valores originais e atuais de `missing DOI` quando o baseline esta disponivel.
- A `Phase 1` e a `Phase 2` guardam workbooks proprios por fase.
- O SCOUT ja nao deve ser visto como substituto do pipeline; e uma camada de triagem manual depois da `Phase 2`.
- Na `Phase 2`, o `Sci-Hub` deve ser entendido como fallback automatico final antes da passagem para revisao manual.

## 16. Limitacao atual

O sistema ainda usa Excel como mecanismo principal de persistencia entre fases. Isso funciona bem para um workflow local, mas continua a ser mais pesado do que uma futura arquitetura com base de dados local e export/import Excel.

## 17. Direcao futura da aplicacao

O projeto ja esta a apontar para uma arquitetura mais ampla do que o PDF Fetcher isolado. A direcao futura e:

- uma app master organizada por fases da metanalise;
- uma app principal chamada `PrismaLab`, organizada por fases da metanalise;
- o `PDF Fetcher` como uma tool dentro desse ecossistema;
- uma base de dados local como memoria interna do projeto;
- Excel usado sobretudo como importacao e exportacao;
- possibilidade de reabrir e continuar projetos no futuro, incluindo por outros utilizadores.

Existe ja um primeiro prototipo visual dessa direcao em:

- `apps/prismalab`

Existe tambem agora uma primeira base tecnica para a futura persistencia local
do projeto em:

- `tools/prismalab/core`
- `tools/prismalab/docs/DATABASE_ARCHITECTURE.md`

Essa base foi pensada para receber dados bibliograficos de multiplas fontes,
preservar proveniencia, aceitar campos em falta e preparar deduplicacao e
continuidade de projeto a longo prazo.
