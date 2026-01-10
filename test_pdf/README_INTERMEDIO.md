# 📡 GESTIONALE FTTH INTERMEDIO - Versione con Equipment Tracking

Applicazione desktop **completa** per gestione lavori FTTH con **equipment tracking essenziale** (modem/ONT) - Tutto locale, zero internet.

## 🎯 VERSIONE INTERMEDIA - COSA INCLUDE

### ✅ FUNZIONALITÀ BASE (da versione completa)
- **Estrazione PDF automatica**: 74+ campi tecnici da file WR
- **Gestione lavori completa**: CRUD, ricerca, filtri, stati
- **Dashboard statistiche**: Metriche real-time, lavori recenti
- **Gestione tecnici**: Assegnazione e tracking tecnici
- **Database SQLite**: Portatile, nessun setup richiesto

### ➕ NUOVE FUNZIONALITÀ EQUIPMENT
- **Tab Equipment dedicato**: Gestione modem e ONT
- **Inventario equipment**: Aggiungi, modifica, elimina dispositivi
- **Assegnazione ai lavori**: Collega modem/ONT ai lavori specifici
- **Tracciamento stati**: available → assigned → installed → faulty
- **Note configurazione**: WiFi, installazione, tecnico
- **Statistiche equipment**: Disponibili, assegnati, installati

## 🚀 INSTALLAZIONE WINDOWS

### Prerequisiti
- **Python 3.8+**: [Scarica qui](https://www.python.org/downloads/)
  - ✅ Seleziona "Add Python to PATH" durante installazione
- **Windows 10/11**: Sistema operativo supportato

### Setup Automatico
1. **Scarica tutti i file** in una cartella dedicata
2. **Fai doppio click** su `avvia_gestionale_intermedio.bat`
3. **Attendi l'installazione** automatica delle dipendenze
4. **L'applicazione si avvia** automaticamente

### Dipendenze Installate Automaticamente
- `pdfplumber` - Estrazione PDF
- `tkinter` - Interfaccia grafica (incluso in Python)
- `sqlite3` - Database (incluso in Python)

## 📋 UTILIZZO

### 🏠 Dashboard
- **Statistiche live**: Totale lavori, stati, equipment
- **Lavori recenti**: Ultimi inserimenti
- **Metriche equipment**: Modem/ONT disponibili e assegnati

### 📋 Tab Lavori
- **Tabella completa**: WR, cliente, indirizzo, tecnico, equipment
- **Ricerca avanzata**: Filtri multi-campo
- **Azioni**: Modifica, elimina, dettagli completi
- **Doppio click**: Visualizza tutti i dettagli

### ➕ Nuovo Lavoro
- **Form completo**: Tutti i campi FTTH
- **Caricamento PDF**: Estrazione automatica
- **Validazione**: Controlli obbligatori

### 👷 Tecnici
- **Gestione completa**: CRUD tecnici
- **Assegnazione**: Base per workflow

### 📡 Equipment (NUOVO)
- **Aggiungi Modem/ONT**: Form creazione dispositivi
- **Lista equipment**: Tabella con stati e assegnazioni
- **Assegna a lavoro**: Collega dispositivi ai lavori
- **Aggiorna stati**: Tracciamento installazioni
- **Note configurazione**: WiFi, tecnico, installazione

## 🔄 WORKFLOW TIPICO

```
1. 📄 Carica PDF WR → Estrai dati automaticamente
2. ➕ Crea lavoro → Inserisci dettagli mancanti
3. 👷 Assegna tecnico → Seleziona dalla lista
4. 📡 Aggiungi equipment → Modem/ONT necessari
5. 🔗 Assegna equipment → Collega al lavoro specifico
6. 📦 Segna consegna → Aggiorna stati consegna
7. ✅ Installazione → Note configurazione e completamento
```

## 📊 STATISTICHE TRACCIATE

### Lavori
- Totale lavori per stato (aperto, in_corso, sospeso, chiuso)
- Lavori per tecnico assegnato
- Equipment richiesto vs consegnato

### Equipment
- Modem/ONT disponibili (stato: available)
- Dispositivi assegnati (stato: assigned)
- Installazioni completate (stato: installed)
- Guasti segnalati (stato: faulty)

## 🗂️ FILE DATABASE

- **Database**: `gestionale_ftth_intermedio.db`
- **Portatile**: Copia il file per backup/trasferimento
- **Auto-creazione**: Il database si crea al primo avvio

## 🆘 TROUBLESHOOTING

### "Python non trovato"
- Reinstalla Python selezionando "Add to PATH"
- Riavvia il computer dopo l'installazione

### "Modulo tkinter non disponibile"
- Usa la versione Python completa (non Microsoft Store)
- Tkinter è incluso nella distribuzione standard

### "Errore pdfplumber"
- L'installer automatico risolve il problema
- In caso contrario: `pip install pdfplumber`

### Database corrotto
- Elimina `gestionale_ftth_intermedio.db`
- Riavvia l'applicazione (si ricrea automaticamente)

## 🔧 FILE INCLUSI

- `gestionale_ftth_intermedio.py` - Applicazione principale
- `avvia_gestionale_intermedio.bat` - Installer e launcher Windows
- `requirements_desktop.txt` - Dipendenze Python
- `README_INTERMEDIO.md` - Questa documentazione

## 📈 CONFRONTO VERSIONI

| Funzionalità | Base | Intermedio | Completo |
|-------------|------|------------|----------|
| Estrazione PDF | ✅ | ✅ | ✅ |
| Gestione Lavori | ✅ | ✅ | ✅ |
| Dashboard | ✅ | ✅ | ✅ |
| Tecnici | ✅ | ✅ | ✅ |
| Equipment Tracking | ❌ | ✅ | ✅ |
| API Endpoints | ❌ | ❌ | ✅ |
| Workflow Completo | ❌ | ⚠️ Base | ✅ |
| Yggdrasil Network | ❌ | ❌ | ✅ |

**Legenda:**
- ✅ Implementato
- ⚠️ Parzialmente implementato
- ❌ Non implementato

---

**Versione**: 2.1 - Equipment Tracking Essential
**Sistema**: Windows 10/11
**Database**: SQLite locale
**Dipendenze**: Python 3.8+, pdfplumber