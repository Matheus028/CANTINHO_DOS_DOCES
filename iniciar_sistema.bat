@echo off
REM Navega para o diretório onde o script está
cd /d "%~dp0"

REM Ativa o ambiente virtual
call venv\Scripts\activate.bat

REM Inicia a aplicação Flask em segundo plano para que o navegador possa abrir
start python main.py

REM Aguarda alguns segundos para o servidor Flask iniciar (ajuste se necessário)
timeout /t 5 /nobreak

REM Abre o navegador na URL da aplicação
start "" "http://127.0.0.1:5000"

REM Você pode optar por fechar a janela do CMD automaticamente após iniciar o navegador
REM ou mantê-la aberta para ver os logs.
REM Se quiser fechar, remova ou comente a linha 'pause'.
REM pause