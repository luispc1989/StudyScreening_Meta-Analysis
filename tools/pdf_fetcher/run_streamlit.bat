@echo off
setlocal

set TOOL_DIR=%~dp0
set REPO_ROOT=%TOOL_DIR%..\..\

cd /d "%REPO_ROOT%"

if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXE=.venv\Scripts\python.exe
) else if exist "venv\Scripts\python.exe" (
    set PYTHON_EXE=venv\Scripts\python.exe
) else (
    echo ERRO: nao foi encontrado um ambiente virtual em .venv ou venv
    echo Cria primeiro o ambiente virtual na raiz do projeto.
    pause
    exit /b 1
)

"%PYTHON_EXE%" -m streamlit run tools\pdf_fetcher\ui\web\app.py

pause
