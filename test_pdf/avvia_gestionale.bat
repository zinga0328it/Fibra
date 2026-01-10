@echo off
REM Avvio Gestionale FTTH Desktop per Windows
REM Questo script avvia l'applicazione desktop locale

echo ===========================================
echo    GESTIONALE FTTH LOCALE - Avvio
echo ===========================================
echo.

REM Controlla se Python è installato
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRORE: Python non è installato o non è nel PATH
    echo.
    echo Installa Python da: https://www.python.org/downloads/
    echo Assicurati di selezionare "Add Python to PATH" durante l'installazione
    pause
    exit /b 1
)

REM Controlla se le dipendenze sono installate
echo Controllo dipendenze...
python -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo Installazione tkinter necessaria...
    pip install tk
)

python -c "import pdfplumber" >nul 2>&1
if errorlevel 1 (
    echo Installazione pdfplumber necessaria...
    pip install pdfplumber
)

echo.
echo Avvio applicazione...
echo.

REM Avvia l'applicazione
python gestionale_ftth_desktop.py

echo.
echo Applicazione chiusa.
pause