# User Guide

## 1. Objetivo

Este guia explica como usar o PDF Fetcher no estado atual do projeto, com foco no modo terminal e no `S.C.O.U.T.`.

## 2. O que a ferramenta faz

O PDF Fetcher:

- lê um workbook Excel;
- enriquece DOIs em falta;
- tenta descarregar PDFs automaticamente;
- usa resolvers especializados para publishers específicos;
- guarda o estado do workflow em workbooks por fase;
- permite revisão manual posterior no `S.C.O.U.T.`.

## 3. Requisitos

Antes de começar, deves ter:

- Windows
- Python instalado
- o repositório completo
- dependências instaladas no `.venv`
- Chromium instalado via Playwright

## 4. Instalação inicial

Na raiz do repositório:

```bat
py -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m playwright install chromium
```

## 5. Como abrir o terminal

Na raiz do repositório:

```bat
.venv\Scripts\python.exe -m tools.pdf_fetcher.ui.terminal.main
```

## 6. Session start

Ao abrir o terminal, o sistema pode mostrar:

- `Start new run from Input workbook`
- `Continue previous run from saved phase workbooks`

### Quando escolher `Start new run`

Escolhe esta opção quando queres:

- começar o workflow desde o workbook de input;
- recriar a `Phase 0` desde o início;
- testar uma corrida nova.

### Quando escolher `Continue previous run`

Escolhe esta opção quando já tens workbooks de fase guardados e queres:

- continuar o workflow de onde paraste;
- voltar a correr uma fase sobre o workbook já gerado dessa fase;
- manter continuidade operacional entre sessões.

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

Os ficheiros principais de trabalho por fase são:

- `wos_workbook_current_phase_0.xlsx`
- `wos_workbook_current_phase_1.xlsx`
- `wos_workbook_current_phase_2.xlsx`

## 8. Fluxo recomendado

### Phase 0

Entrada:

- `PDF Fetcher/Excel/Input/wos_workbook_input.xlsx`

Saída:

- `PDF Fetcher/Excel/Current/wos_workbook_current_phase_0.xlsx`

### Phase 1

Entrada:

- `wos_workbook_current_phase_0.xlsx`

Saída:

- `wos_workbook_current_phase_1.xlsx`

### Phase 2

Entrada:

- `wos_workbook_current_phase_1.xlsx`

Saída:

- `wos_workbook_current_phase_2.xlsx`

### S.C.O.U.T.

Entrada:

- `wos_workbook_current_phase_2.xlsx`

O SCOUT gera uma sessão própria com os casos ainda por rever manualmente.

## 9. Menus principais do terminal

No menu inicial podes tipicamente:

- correr `Phase 0`
- correr `Phase 1`
- correr `Phase 2`
- correr diagnósticos
- abrir o `S.C.O.U.T.`
- sair da aplicação

As opções concretas dependem do estado atual do projeto.

## 10. Interromper uma fase

Durante as fases, o terminal aceita:

- `P` — pause
- `V` — back to menu
- `S` — exit app

Se saíres com `S`, a app tenta gravar um checkpoint para recuperação.

## 11. Reports e checkpoints

Os reports ficam organizados por fase:

- `Reports/Phase 0`
- `Reports/Phase 1`
- `Reports/Phase 2`
- `Reports/SCOUT`

Os checkpoints também:

- `Checkpoints/Phase 0`
- `Checkpoints/Phase 1`
- `Checkpoints/Phase 2`
- `Checkpoints/SCOUT`

## 12. Como usar o S.C.O.U.T.

O `S.C.O.U.T.` é a camada manual de revisão depois da `Phase 2`.

No SCOUT podes:

- abrir `DOI Link`
- usar `Search Engine`
- enviar pedido por email ao autor
- inserir ou limpar `DOI Link` / `Source Link`
- atribuir decisão manual
- escrever notas

O SCOUT também:

- deteta downloads feitos a partir do browser;
- mostra o estado em `PDF Status`;
- preserva a memória da revisão até ao `Finalize To Workbook`.

## 13. Continuidade de sessão no SCOUT

O SCOUT mantém memória própria da revisão. Isso significa que:

- se fechares a app a meio;
- se o browser cair;
- ou se reabrir a sessão depois;

deves retomar o estado da revisão sem perder o trabalho já registado.

## 14. O que fazer se quiseres recomeçar do zero

Se quiseres recomeçar o pipeline:

1. escolhe `Start new run from Input workbook`
2. corre novamente a `Phase 0`
3. continua o fluxo até `Phase 2`

Isto recria os workbooks por fase a partir do input.

## 15. Notas importantes

- A `Phase 0` agora distingue entre valores originais e atuais de `missing DOI` quando o baseline está disponível.
- A `Phase 1` e a `Phase 2` guardam workbooks próprios por fase.
- O SCOUT já não deve ser visto como substituto do pipeline; é uma camada de triagem manual depois da `Phase 2`.

## 16. Limitação atual

O sistema ainda usa Excel como mecanismo principal de persistência entre fases. Isso funciona bem para um workflow local, mas continua a ser mais pesado do que uma futura arquitetura com base de dados local e export/import Excel.
