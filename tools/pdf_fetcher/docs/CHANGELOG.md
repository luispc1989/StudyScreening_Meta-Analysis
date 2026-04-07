# CHANGELOG.md

## [0.1.0] - Inicial

### Adicionado
- arquitetura modular com `app/`, `resolvers/` e `ui/`
- suporte a execucao em terminal
- suporte a execucao em Streamlit
- pipeline central reutilizavel
- resolver base de download
- resolver especializado Frontiers
- leitura e escrita de workbook Excel
- dashboard terminal
- componentes Streamlit
- scripts `.bat` de arranque

### Objetivo desta versao
Disponibilizar uma base funcional, leve e extensivel para:
- descarregar PDFs;
- atualizar estados num workbook;
- suportar novos resolvers no futuro.

## [Proximos passos sugeridos]
- logging persistente
- argumentos CLI
- mais resolvers especializados
- testes automaticos
- robustez acrescida no Streamlit

## [Development Notes - 2026-04-06]

### Reorganizacao e arquitetura
- o `SCOUT` foi formalizado como sub-tool de `pdf_fetcher`
- a estrutura passou a distinguir melhor entre tool mae (`pdf_fetcher`) e sub-tool (`scout`)
- os launchers foram alinhados com a nova organizacao
- os ficheiros locais gerados pelo browser passaram a ser excluidos do repositorio

### SCOUT
- a interface do `SCOUT` foi simplificada para reduzir controlos redundantes
- a navegacao passou a incluir `Advanced navigation` com `First`, `Last`, `Go to case` e `Go to first pending`
- o botao `Open article link` foi movido para a sidebar
- o fluxo de review ficou centrado em autosave, removendo botoes manuais redundantes
- a organizacao visual do `SCOUT` passou a servir como referencia para futuras semi-assisted tools

### Fase 2 - Specialized resolvers
- o resolver `wiley` foi integrado na app ativa
- a detecao Wiley passou a aceitar melhor subdominios reais
- a Phase 2 passou a refrescar o terminal artigo a artigo
- os specialized resolvers passaram a registar detalhe de falha em `pdf_checked_at`

### Wiley - problemas observados
- paginas institucionais ou legacy que nao expunham diretamente o PDF
- viewers Wiley que abriam mas ficavam em estado vazio (`0 of 0` / `0 de 0`)
- casos em que o PDF aparecia no viewer mas nao atraves de um link HTML reutilizavel
- interferencia de banners de cookies e camadas de consentimento

### Wiley - respostas implementadas
- reintroducao de validacao de readiness do viewer
- reintroducao de extracao de candidates do viewer via DOM e JavaScript
- distincao explicita entre viewer vazio e viewer com PDF real
- fallback para o botao nativo de save/download do viewer PDF do Chromium

### Estrategia acordada
- afinar cookies e problemas de UI resolver a resolver primeiro
- so depois extrair uma funcao comum para comportamentos realmente partilhados
- manter as melhorias conservadoras, sem alterar a logica funcional central quando o objetivo for observabilidade
