# TROUBLESHOOTING.md — Resolução de Problemas

## 1. Ambiente virtual não encontrado

### Mensagem típica
```text
ERRO: nao foi encontrado um ambiente virtual em .venv ou venv
```

### Causa provável
A pasta `.venv` ainda não foi criada.

### Solução
```bat
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m playwright install chromium
```

---

## 2. `No module named streamlit`

### Causa provável
O Streamlit não está instalado no Python que está a ser usado.

### Solução
```bat
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit --version
```

---

## 3. Caminho não encontrado

### Causas prováveis
- ficheiro `.bat` fora da pasta correta
- `.venv` em falta
- `main.py` em falta
- `ui\streamlit_app.py` em falta

### Verificação
Confirmar existência de:
```text
.venv\Scripts\python.exe
main.py
ui\streamlit_app.py
```

---

## 4. Sheet não encontrada

### Causa
`SHEET_NAME` não coincide com o nome real da folha Excel.

### Solução
Verificar em `app/config.py`:
```python
SHEET_NAME = "wos_full_text"
```

---

## 5. Colunas obrigatórias em falta

### Causa
O workbook não tem todas as colunas exigidas.

### Solução
Confirmar presença de:
- `record_id`
- `Title`
- `DOI`
- `DOI Link`
- colunas de saída esperadas

---

## 6. Streamlit abre, mas não processa

### Causas prováveis
- workbook inválido
- sheet errada
- workbook vazio
- sem `record_id`
- colunas em falta

### Solução
Validar:
- workbook
- sheet
- colunas
- conteúdo útil

---

## 7. Comandos de diagnóstico rápido

```bat
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe -m streamlit --version
.venv\Scripts\python.exe -m playwright --version
.venv\Scripts\python.exe main.py
.venv\Scripts\python.exe -m streamlit run ui\streamlit_app.py
```

---

## 8. Estratégia recomendada de depuração

1. validar `.venv`
2. validar dependências
3. validar workbook e sheet
4. limitar `MAX_ROWS_TO_PROCESS`
5. testar primeiro em terminal
6. só depois testar em Streamlit
