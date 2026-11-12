@echo off
cd /d "%~dp0"
echo Ativando ambiente virtual e executando o pipeline...
call .venv\Scripts\activate
python desafio_um.py
pause