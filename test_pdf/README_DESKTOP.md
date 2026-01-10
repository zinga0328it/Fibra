# GESTIONALE FTTH LOCALE - Versione Desktop Windows

Applicazione standalone per la gestione completa dei lavori FTTH con estrazione automatica dei dati da PDF WR (Work Report).

## 🚀 CARATTERISTICHE

- **Estrazione Automatica**: Carica PDF WR e estrae automaticamente tutti i dati (74+ campi)
- **Database Locale**: SQLite integrato, nessun server richiesto
- **Interfaccia Intuitiva**: Ricerca, filtri e visualizzazione dettagliata
- **Gestione Completa**: Clienti, indirizzi, dati tecnici FTTH, ONT/Modem
- **Statistiche**: Report e analisi dei lavori

## 📋 PREREQUISITI

### Python 3.8+
- Scarica da: https://www.python.org/downloads/
- **IMPORTANTE**: Durante l'installazione seleziona "Add Python to PATH"

### Dipendenze Python
```
pip install pdfplumber
```

Tkinter è incluso in Python per Windows.

## 🛠️ INSTALLAZIONE

1. **Scarica i file** nella cartella del progetto
2. **Installa Python** (se non presente)
3. **Installa dipendenze**:
   ```
   pip install pdfplumber
   ```
4. **Avvia l'applicazione** facendo doppio click su `avvia_gestionale.bat`

## 📖 UTILIZZO

### Avvio Applicazione
1. Fai doppio click su `avvia_gestionale.bat`
2. L'applicazione si avvia automaticamente

### Caricamento PDF WR
1. Clicca "**📁 Carica PDF WR**"
2. Seleziona il file PDF del lavoro
3. L'applicazione estrae automaticamente tutti i dati
4. I lavori vengono salvati nel database locale

### Ricerca Lavori
- **Ricerca in tempo reale**: Digita nella casella "Cerca"
- **Filtri**: Numero WR, nome cliente, indirizzo
- **Doppio click**: Visualizza dettagli completi del lavoro

### Visualizzazione Dati
- **Tabella principale**: Elenco di tutti i lavori
- **Dettagli lavoro**: Doppio click per vedere tutti i campi
- **Statistiche**: Clicca "📊 Statistiche" per report

## 📊 DATI ESTRATTI

### Dati Principali
- Numero WR
- Cliente (nome, cognome, indirizzo)
- Tipo lavoro (attivazione, guasto, manutenzione)
- Stato (aperto, in corso, chiuso)
- Date (apertura, chiusura)
- Note e osservazioni

### Dati Tecnici FTTH (74+ campi)
- **PTE**: Nome PTE, porta PTE
- **Splitter**: Nome splitter PFS/PFP, numero porta permutatore
- **ODF**: Porta ODF, ID building
- **OLT**: Configurazione OLT, GPON
- **Rete**: Patch panel, permutatore, building info
- **Equipaggiamento**: ONT, Modem, configurazione

### Flags Automatici
- **Requires ONT**: Se il lavoro richiede ONT
- **Requires Modem**: Se il lavoro richiede modem
- **Delivery Status**: Stato consegna equipaggiamento

## 🗄️ DATABASE

### File Database
- **Nome**: `gestionale_ftth.db`
- **Tipo**: SQLite
- **Posizione**: Nella stessa cartella dell'applicazione

### Struttura Tabella
```sql
CREATE TABLE works (
    id INTEGER PRIMARY KEY,
    numero_wr TEXT UNIQUE,
    operatore TEXT,
    indirizzo TEXT,
    tipo_lavoro TEXT,
    nome_cliente TEXT,
    stato TEXT DEFAULT 'aperto',
    data_apertura TEXT,
    data_chiusura TEXT,
    note TEXT,
    requires_ont BOOLEAN,
    requires_modem BOOLEAN,
    ont_delivered BOOLEAN,
    modem_delivered BOOLEAN,
    extra_fields TEXT,  -- JSON con dati tecnici
    created_at TEXT
);
```

## 🔧 MANUTENZIONE

### Backup Database
- Copia il file `gestionale_ftth.db`
- Salvalo in luogo sicuro

### Svuota Database
- Clicca "**🗑️ Svuota Database**"
- **ATTENZIONE**: Elimina tutti i dati definitivamente

### Aggiornamento
- Sostituisci i file `.py` con le nuove versioni
- Il database rimane invariato

## 🆘 RISOLUZIONE PROBLEMI

### "Python non trovato"
- Reinstalla Python selezionando "Add to PATH"
- Riavvia il computer

### "Modulo non trovato"
```bash
pip install pdfplumber
```

### PDF non caricato
- Verifica che il PDF sia un file WR valido
- Controlla che non sia protetto da password
- Prova con un PDF più piccolo

### Applicazione si blocca
- Chiudi e riavvia
- Se persiste, svuota database e ricarica i PDF

## 📞 SUPPORTO

Per problemi o domande:
- Controlla questo README
- Verifica i log degli errori
- Contatta il supporto tecnico

## 🔄 AGGIORNAMENTI FUTURI

### Versione 1.1 (Prevista)
- Esportazione Excel/PDF
- Backup automatico
- Sincronizzazione multi-utente
- Dashboard avanzate

### Versione 1.2 (Prevista)
- Integrazione GPS per tecnici
- Notifiche automatiche
- Report personalizzati
- API per integrazioni esterne

---

**Versione**: 1.0.0
**Data**: Gennaio 2026
**Sviluppato per**: Fibra Srl