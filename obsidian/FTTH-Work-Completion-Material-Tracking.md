# FTTH Work Completion Enhancement - Material Tracking

## Data: 7 Gennaio 2026

## Obiettivo
Implementare sistema di tracciamento materiali utilizzati durante la conclusione dei lavori FTTH, con interfaccia sia Telegram che Web.

## Requisiti Funzionali

### 1. Interfaccia Telegram per Tecnici
Quando un tecnico conclude un lavoro via Telegram, deve poter inserire:

- **Metri di cavo utilizzati** (numero intero)
- **Apparati utilizzati**:
  - Modem (selezionare da lista equipment assegnati al lavoro)
  - ONT (selezionare da lista equipment assegnati al lavoro)

### 2. Interfaccia Web
Stessa funzionalità disponibile sul sito web per:
- Completamento lavori
- Modifica dati materiali post-completamento
- Visualizzazione statistiche

### 3. Database
Nuove tabelle/campi necessari:

```sql
-- Tabella materiali lavoro completato
CREATE TABLE work_materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER NOT NULL,
    cable_meters INTEGER,
    modem_id INTEGER,
    ont_id INTEGER,
    technician_id INTEGER,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (work_id) REFERENCES works(id),
    FOREIGN KEY (modem_id) REFERENCES modems(id),
    FOREIGN KEY (ont_id) REFERENCES onts(id),
    FOREIGN KEY (technician_id) REFERENCES technicians(id)
);

-- Estensioni tabella works
ALTER TABLE works ADD COLUMN materials_completed BOOLEAN DEFAULT FALSE;
ALTER TABLE works ADD COLUMN materials_completion_date TIMESTAMP;
```

### ⚠️ **IMPORTANTE: Separazione Database**
- **Gestionale Intermedio**: Database SQLite locale dedicato (`ftth_desktop.db`)
- **Lato Web**: Database PostgreSQL/MySQL del server dedicato
- **NON mischiare i database**: Due sistemi indipendenti con sincronizzazione opzionale
- **Sincronizzazione**: Solo se richiesta esplicitamente (es. export/import manuale)

### 4. Statistiche
Dashboard con statistiche sui materiali:

- **Consumo medio cavo per tipo lavoro**
- **Utilizzo apparati per modello**
- **Statistiche per tecnico** (metri cavo posati, apparati installati)
- **Trend consumo materiali** (grafici temporali)
- **Report mensili/annuali**

### 5. Workflow
1. **Assegnazione lavoro**: Tecnico riceve lavoro con equipment
2. **Completamento lavoro**: Via Telegram/Web, tecnico inserisce materiali utilizzati
3. **Validazione**: Sistema verifica che equipment utilizzati corrispondano a quelli assegnati
4. **Aggiornamento stato**: Lavoro marcato come "materiali completati"
5. **Statistiche**: Aggiornamento automatico dashboard statistiche

## Implementazione

### Fase 1: Backend API
- Endpoint Telegram per completamento con materiali
- Endpoint Web per gestione materiali
- Validazione dati inseriti
- Aggiornamento database

### Fase 2: Frontend Web
- Form completamento lavoro con sezione materiali
- Dashboard statistiche materiali
- Report esportabili

### Fase 3: Integrazione Gestionale Intermedio
- **Database separato**: SQLite locale indipendente (`ftth_desktop.db`)
- **Nessuna sincronizzazione automatica** con server web
- Interfaccia desktop per visualizzazione materiali lavoro
- Gestione materiali locale (stessa logica del server ma DB separato)
- Export manuale dati se necessario
- Report locali basati su DB desktop

## Architettura Gestionale Intermedio

### Ristrutturazione Completa
Il gestionale intermedio deve essere completamente riscritto con architettura modulare:

```
gestionale_ftth_intermedio/
├── core.py                 # Classe principale, configurazione, init
├── database/
│   ├── __init__.py
│   ├── connection.py       # Gestione connessione DB
│   ├── models.py          # Definizioni classi dati
│   └── queries.py         # Query SQL centralizzate
├── gui/
│   ├── __init__.py
│   ├── main_window.py     # Finestra principale
│   ├── tabs/
│   │   ├── dashboard_tab.py
│   │   ├── works_tab.py
│   │   ├── technicians_tab.py
│   │   ├── equipment_tab.py
│   │   └── reports_tab.py
│   └── dialogs/
│       ├── work_dialog.py
│       ├── technician_dialog.py
│       └── equipment_dialog.py
├── business_logic/
│   ├── __init__.py
│   ├── work_manager.py    # Logica gestione lavori
│   ├── equipment_manager.py # Logica gestione equipment
│   ├── technician_manager.py # Logica gestione tecnici
│   └── pdf_parser.py      # Parsing PDF report
├── utils/
│   ├── __init__.py
│   ├── validators.py      # Validazione dati
│   ├── formatters.py      # Formattazione output
│   └── exporters.py       # Esportazione dati
└── config.py              # Configurazioni applicazione
```

### Vantaggi Architettura Modulare
- **Manutenibilità**: Ogni funzione in file separato
- **Testabilità**: Unit test per ogni modulo
- **Riutilizzo**: Logica condivisa tra componenti
- **Scalabilità**: Facile aggiunta nuove funzionalità
- **Debug**: Isolamento problemi per componente

## Priorità Implementazione
1. ✅ Completare gestione equipment nel server (DB PostgreSQL/MySQL)
2. 🔄 Implementare tracciamento materiali nel server (DB server separato)
3. 🔄 Aggiungere interfaccia web per materiali (connesso a DB server)
4. 🔄 Ristrutturare gestionale intermedio con architettura modulare (DB SQLite locale separato)
5. 🔄 Implementare logica materiali nel gestionale intermedio (stessa logica, DB separato)
6. 🔄 Testing integrazione sistemi indipendenti

## Note Tecniche
- **Database separati**: Gestionale intermedio (SQLite locale) ≠ Server web (PostgreSQL/MySQL)
- Mantenere compatibilità con database esistente di ciascun sistema
- Utilizzare pattern observer per aggiornamenti real-time nel rispettivo sistema
- Implementare logging dettagliato per audit trail in entrambi i sistemi
- Considerare validazione lato client/server per ciascun sistema
- Pianificare migration database indipendente per nuovi campi in ciascun DB
- **Nessuna sincronizzazione automatica** tra i due database

**Nota:** Il gestionale intermedio e il gestionale web devono avere database separati per garantire indipendenza e facilità di gestione.