@echo off
setlocal

cd /d "%~dp0\..\.."

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m streamlit run tools\prismalab\app.py
) else (
  py -m streamlit run tools\prismalab\app.py
)

endlocal
