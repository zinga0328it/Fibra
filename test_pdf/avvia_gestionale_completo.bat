@echo off
REM Avvio Gestionale FTTH Completo - Versione Desktop Locale
REM Applicazione completa con tutte le funzionalità web convertite per locale

echo ===========================================
echo   GESTIONALE FTTH COMPLETO LOCALE
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

REM Verifica che il file esista
if not exist "gestionale_ftth_completo.py" (
    echo ERRORE: File gestionale_ftth_completo.py non trovato!
    echo Assicurati che tutti i file siano nella stessa cartella.
    pause
    exit /b 1
)

echo Avvio applicazione completa...
echo.
echo ===========================================
echo ISTRUZIONI RAPIDE:
echo ===========================================
echo • Carica PDF: "Carica PDF WR" per estrarre dati automaticamente
echo • Nuovo Lavoro: Tab "Nuovo Lavoro" per inserimento manuale
echo • Dashboard: Statistiche e lavori recenti
echo • Lavori: Ricerca, modifica, elimina lavori
echo • Tecnici: Gestione squadra tecnici
echo.
echo Database locale: gestionale_ftth.db (nella stessa cartella)
echo ===========================================
echo.

REM Avvia l'applicazione
python gestionale_ftth_completo.py

echo.
echo Applicazione chiusa.
echo Database salvato automaticamente.
pause