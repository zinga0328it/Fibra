# GESTIONALE FTTH LOCALE COMPLETO - Versione Desktop Windows

Applicazione standalone **COMPLETA** per la gestione lavori FTTH con **tutte le funzionalità web** convertite per funzionare **in locale** senza internet.

## 🎯 CARATTERISTICHE PRINCIPALI

- **Estrazione Automatica**: Carica PDF WR e estrae automaticamente tutti i dati (74+ campi)
- **Database Locale**: SQLite integrato, nessun server richiesto
- **Interfaccia Completa**: 4 tabs principali (Dashboard, Lavori, Nuovo Lavoro, Tecnici)
- **Gestione Completa**: Clienti, indirizzi, dati tecnici FTTH, ONT/Modem, tecnici
- **Ricerca Avanzata**: Filtri per stato, ricerca in tempo reale
- **Statistiche Real-time**: Dashboard con grafici e metriche
- **Modifica/Elimina**: Gestione completa dei record esistenti

## 📋 FUNZIONALITÀ DETTAGLIATE

### 🏠 Dashboard
- **Statistiche Live**: Totale lavori, stati, equipaggiamento richiesto
- **Lavori Recenti**: Ultimi 10 lavori inseriti
- **Grafici**: Distribuzione stati lavori (placeholder per espansione futura)
- **Metriche**: ONT richiesti, Modem richiesti, ecc.

### 📋 Tab Lavori
- **Tabella Completa**: ID, WR, Cliente, Indirizzo, Tipo, Stato, Tecnico, Data, ONT, Modem
- **Ricerca Avanzata**: Cerca per WR, cliente, indirizzo
- **Filtro Stato**: Aperto, In Corso, Sospeso, Chiuso
- **Azioni**: Modifica, Elimina, Dettagli completi
- **Doppio Click**: Visualizza tutti i dettagli del lavoro

### ➕ Nuovo Lavoro
- **Form Completo**: Tutti i campi del sistema web originale
- **Sezioni Organizzate**:
  - 📋 Dati Principali (WR*, Cliente, Indirizzo, Tipo, Stato)
  - 📅 Date (Data Apertura)
  - 🔧 Equipaggiamento (ONT, Modem, consegne)
  - 📝 Note (campo testo libero)
- **Validazione**: Controlli obbligatori e formattazione
- **Carica da PDF**: Integra con estrazione automatica

### 👷 Tecnici
- **Lista Completa**: Nome, Cognome, Telefono, Telegram
- **Aggiungi Nuovo**: Form per inserimento tecnici
- **Status Telegram**: Indicatore connessione bot
- **Assegnazione**: Base per future assegnazioni automatiche

## 📊 DATI ESTRATTI AUTOMATICAMENTE

### Dati Base (sempre estratti):
- ✅ Numero WR
- ✅ Nome cliente
- ✅ Indirizzo completo
- ✅ Tipo lavoro
- ✅ Stato lavoro
- ✅ Date apertura/chiusura

### Dati Tecnici FTTH (74+ campi):
- ✅ **PTE**: Nome PTE, porta PTE
- ✅ **Splitter**: PFS/PFP, numero porta permutatore
- ✅ **ODF**: Porta ODF, ID building
- ✅ **OLT**: Configurazione OLT, GPON
- ✅ **Rete**: Patch panel, permutatore, building info
- ✅ **Equipaggiamento**: Flag ONT/Modem automatici

### Campi Extra Memorizzati:
- ✅ **JSON Storage**: Tutti i campi tecnici aggiuntivi
- ✅ **Ricerca**: Accessibili nei dettagli lavoro
- ✅ **Esportazione**: Base per future funzionalità export

## 💾 DATABASE LOCALE

### File Database
- **Nome**: `gestionale_ftth.db`
- **Tipo**: SQLite
- **Posizione**: Nella stessa cartella dell'app

### Tabelle
```sql
-- Lavori completi
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
    tecnico_assegnato_id INTEGER,
    tecnico_chiusura_id INTEGER,
    note TEXT,
    requires_ont BOOLEAN,
    requires_modem BOOLEAN,
    ont_delivered BOOLEAN,
    modem_delivered BOOLEAN,
    extra_fields TEXT,  -- JSON tecnici
    created_at TEXT
);

-- Tecnici
CREATE TABLE technicians (
    id INTEGER PRIMARY KEY,
    nome TEXT,
    cognome TEXT,
    telefono TEXT,
    telegram_id TEXT,
    created_at TEXT
);
```

### Backup
- Copia il file `gestionale_ftth.db`
- Salvalo in luogo sicuro
- Versione incrementale possibile

## 🛠️ INSTALLAZIONE SU WINDOWS (10 minuti)

### 1. Installa Python
```
Scarica da: https://www.python.org/downloads/
IMPORTANTE: Seleziona "Add Python to PATH" durante l'installazione
```

### 2. Installa Dipendenze
Apri il Prompt dei Comandi e vai nella cartella del progetto:
```cmd
cd C:\percorso\alla\tua\cartella\progetto
pip install -r requirements_desktop.txt
```

### 3. Avvia Applicazione
**Doppio click su `avvia_gestionale_completo.bat`**

### 4. Primo Avvio
- Database creato automaticamente
- Interfaccia pronta all'uso
- Carica PDF per iniziare

## 🎯 UTILIZZO GIORNALIERO

### Workflow Tipico:
1. **Avvia**: Doppio click su `avvia_gestionale_completo.bat`
2. **Carica PDF**: "📁 Carica PDF WR" → Seleziona file → Estrazione automatica
3. **Verifica**: Controlla Dashboard per statistiche
4. **Gestisci**: Tab "Lavori" per ricerca/modifica
5. **Aggiungi**: Tab "Nuovo Lavoro" per inserimenti manuali
6. **Chiudi**: Dati salvati automaticamente

### Ricerca Lavori:
- **Tabella**: Scorri e ordina per colonna
- **Cerca**: Scrivi nella casella "Cerca" (tempo reale)
- **Filtro**: Usa combo "Stato" per filtrare
- **Dettagli**: Doppio click su riga per info complete

### Modifica Lavori:
- Seleziona lavoro in tabella
- Click "✏️ Modifica" o doppio click
- Finestra modifica con tutti i campi
- Salva automaticamente nel database

## 🔧 MANUTENZIONE

### Aggiornamento Database
- Nuovo avvio = database aggiornato automaticamente
- Migrazione dati trasparente

### Pulizia Database
- Click "**🗑️ Svuota DB**" per reset completo
- **ATTENZIONE**: Elimina tutti i dati

### Backup Regolare
- Chiudi applicazione
- Copia `gestionale_ftth.db`
- Salva in cartella sicura

## 🆘 RISOLUZIONE PROBLEMI

### "Python non trovato"
- Reinstalla Python con "Add to PATH"
- Riavvia computer

### "Modulo pdfplumber mancante"
```cmd
pip install pdfplumber
```

### PDF non caricato
- Verifica PDF non protetto
- Controlla formato WR valido
- Prova PDF più piccolo

### Database corrotto
- Elimina `gestionale_ftth.db`
- Riavvia applicazione (ricreato automaticamente)

### Applicazione non si avvia
- Verifica file nella stessa cartella
- Controlla Prompt dei Comandi per errori
- Riavvia computer

## 📊 PRESTAZIONI

### Capacità
- **Database**: SQLite (fino a milioni di record)
- **PDF**: Processamento veloce (< 5 secondi)
- **Ricerca**: Tempo reale su migliaia di record
- **Memoria**: Leggera, funziona su PC base

### Limitazioni
- Database locale (no multi-utente nativo)
- Backup manuale richiesto
- No notifiche automatiche (base per espansione)

## 🚀 ESPANSIONI FUTURE

### Versione 2.1 (Prevista)
- **Esportazione Excel/CSV**
- **Report PDF automatici**
- **Backup programmati**
- **Import/Export dati**

### Versione 2.2 (Prevista)
- **Mappe integrate** (Leaflet)
- **Assegnazione automatica tecnici**
- **Notifiche desktop**
- **Sincronizzazione multi-PC**

### Versione 3.0 (Futuro)
- **Multi-utente** con server locale
- **API REST** per integrazioni
- **Mobile app** companion
- **Machine Learning** per previsioni

## 📞 SUPPORTO

### Auto-diagnosi
- Esegui `python test_logica_pdf.py` per test estrazione
- Verifica `gestionale_ftth.db` esiste
- Controlla spazio disco (> 100MB liberi)

### Contatti
- **Documentazione**: Questo file README
- **Log Errori**: Controlla finestra Prompt Comandi
- **Backup**: Copia sempre il database prima di modifiche

## 🔄 CONFRONTO CON VERSIONE WEB

| Funzionalità | Web (FastAPI) | Desktop (Tkinter) |
|-------------|----------------|-------------------|
| Estrazione PDF | ✅ API | ✅ Locale |
| Database | ✅ PostgreSQL | ✅ SQLite |
| Interfaccia | ✅ Browser | ✅ Desktop App |
| Installazione | 🔴 Server | ✅ Doppio click |
| Internet | 🔴 Richiesto | ✅ Offline |
| Costi | 🔴 Hosting | ✅ Zero |
| Backup | 🔴 Complesso | ✅ Copia file |
| Accesso | 🔴 Qualsiasi PC | ✅ PC locale |

## ✅ PRONTO PER PRODUZIONE

Il gestionale è **completamente funzionale** e pronto per l'uso immediato in produzione:

- ✅ **Estrazione automatica** da PDF funzionante
- ✅ **Database stabile** con tutte le tabelle
- ✅ **Interfaccia completa** con tutte le funzionalità web
- ✅ **Gestione errori** e validazioni
- ✅ **Backup semplice** (copia file)
- ✅ **Performance ottimali** per uso quotidiano

---

**🚀 IL GESTIONALE È PRONTO!**

**Installa, avvia e inizia a lavorare immediatamente.**

*Versione 2.0.0 - Gennaio 2026*