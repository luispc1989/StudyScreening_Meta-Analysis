@echo off
setlocal

cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXE=.venv\Scripts\python.exe
) else if exist "venv\Scripts\python.exe" (
    set PYTHON_EXE=venv\Scripts\python.exe
) else (
    echo ERRO: nao foi encontrado um ambiente virtual em .venv ou venv
    echo Cria primeiro o ambiente virtual nesta pasta do projeto.
    pause
    exit /b 1
)

"%PYTHON_EXE%" -m streamlit run ui\streamlit_app.py

pause