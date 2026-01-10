@echo off
REM Avvio Gestionale FTTH Intermedio - Versione con Equipment Tracking
REM Applicazione desktop con gestione essenziale modem/ONT

echo ===========================================
echo   GESTIONALE FTTH INTERMEDIO
echo   CON EQUIPMENT TRACKING
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

REM Controlla dipendenze
echo Controllo dipendenze...
python -c "import sqlite3" >nul 2>&1
if errorlevel 1 (
    echo ERRORE: sqlite3 non disponibile
    pause
    exit /b 1
)

python -c "import json" >nul 2>&1
if errorlevel 1 (
    echo ERRORE: json non disponibile
    pause
    exit /b 1
)

python -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo ERRORE: tkinter non disponibile
    echo Nota: tkinter è incluso in Python per Windows
    echo Se hai installato Python da Microsoft Store, installa la versione completa
    pause
    exit /b 1
)

python -c "import pdfplumber" >nul 2>&1
if errorlevel 1 (
    echo Installazione pdfplumber necessaria...
    pip install pdfplumber
    if errorlevel 1 (
        echo ERRORE: Impossibile installare pdfplumber
        pause
        exit /b 1
    )
)

echo.
echo ✅ Dipendenze OK
echo.
echo Avvio applicazione...
echo.
echo ===========================================
echo   FUNZIONALITÀ DISPONIBILI:
echo ===========================================
echo ✅ Estrazione PDF automatica (74+ campi)
echo ✅ Gestione completa lavori
echo ✅ Dashboard con statistiche
echo ✅ Gestione tecnici
echo ✅ Tab Equipment (MODEM/ONT)
echo ✅ Assegnazione equipment ai lavori
echo ✅ Tracciamento stati equipment
echo ✅ Note installazione e configurazione
echo ===========================================
echo.
echo Database: gestionale_ftth_intermedio.db
echo.

REM Avvia l'applicazione
python gestionale_ftth_intermedio.py

pause