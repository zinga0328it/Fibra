# FTTH Management System

Sistema di gestione per lavori FTTH (Fiber To The Home) per installazione modem e attivazione linee su rete Open Fiber.

## Funzionalità

- Caricamento e parsing di bolle di lavoro (WR) da PDF, immagini o testo
- Assegnazione lavori ai tecnici
- Compilazione bolle via app mobile (Telegram Bot)
- Statistiche settimanali/mensili
- Dashboard per backoffice
- Sicurezza con nftables e fail2ban

### Presentation Demo Note

For demos, the repository includes systemd service files and simple scripts in `deploy/systemd/` to install or uninstall the services that launch the backend and the Telegram bot at system boot. These are intended only for short-lived presentation environments.

Please remove the demo services from the target host after the demonstration using:

  cd deploy/systemd && sudo ./uninstall_demo_services.sh

This disables the services and removes their unit files. Avoid leaving these services enabled on production hosts unless properly maintained and secured.

## Struttura Progetto

- `app/`: Codice backend FastAPI
  - `main.py`: App principale
  - `database.py`: Configurazione DB
  - `models/`: Modelli SQLAlchemy
  - `routes/`: API routes
  - `bot.py`: Telegram Bot
- `web/publica/`: File statici frontend
- `.env`: Variabili ambiente
- `requirements.txt`: Dipendenze Python

## Installazione

1. Clona il repo
2. Crea ambiente virtuale: `python -m venv venv`
3. Attiva: `source venv/bin/activate`
4. Installa dipendenze: `pip install -r requirements.txt`
5. Configura `.env` con DATABASE_URL, TELEGRAM_BOT_TOKEN, etc.
6. Crea DB: `python -c "from app.database import engine; from app.models import models; models.Base.metadata.create_all(bind=engine)"`
7. Avvia backend: `uvicorn app.main:app --host 0.0.0.0 --port 6030`
8. Avvia bot: `python app/bot.py`

## Modifica Lavori dalla UI (inline o modal)

Nel frontend (`web/publica/index.html`) è disponibile un bottone "Modifica" per ogni lavoro nella lista.
- Cliccando "Modifica" si apre un form inline all'interno della riga che permette di modificare direttamente i campi principali: `numero_wr`, `nome_cliente`, `indirizzo`, `operatore`, `tipo_lavoro`, `tecnico_assegnato` e `stato`.
- Il pulsante "Salva" invia una richiesta `PUT /works/{id}` con payload JSON per aggiornare il record nel DB. Esempio (curl):

```
curl -X PUT -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" \ 
  -d '{"stato":"in_corso", "tecnico_assegnato_id": 3}' \ 
  http://localhost:6030/works/42
```

- È anche disponibile la modale di dettaglio/modifica se preferisci un editor più completo (apre campi aggiuntivi e funzioni di stato come Sospendi/Riapri/Chiudi).

Le azioni aggiornano il DB immediatamente e generano eventi di audit (WorkEvent) salvati in tabella per cronologia delle modifiche.

## API Routes

### Works
- `POST /works/upload`: Carica bolla (CSV) — carica uno o più record via CSV; il server fa upsert per `numero_wr` normalizzato
- `POST /works/`: Crea un novo lavoro (API manuale)
 - `POST /manual/works`: Inserimento manuale di un Work (UI: `manual_entry.html`)
   - Questo endpoint è pensato per inserire manualmente il contenuto della bolla quando non è possibile usare il bot o il parsing automatico. È protetto: richiede header `X-API-Key` o `Authorization: Bearer <token>` con un utente `admin`/`backoffice`.
   - Campi principali supportati (JSON): `numero_wr`, `nome_cliente`, `indirizzo`, `operatore`, `tipo_lavoro`, `stato`, `data_inizio`, `data_fine`, `tecnico` (nome o id), `telefono_cliente`, `numero_impianto`.
   - I campi aggiuntivi non mappati verranno salvati in `extra_fields` (JSON) per compatibilità.

   Esempio via curl (usando X-API-Key):

```
API_KEY=your_api_key_here
curl -sS -X POST http://127.0.0.1:6030/manual/works \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"numero_wr":"15699897","data_inizio":"2025-12-01T11:30:00","data_fine":"2025-12-01T13:30:00","tipo":"70 - DELIVERY OF","cliente":"RAINONE DANILO","indirizzo":"VIA GIUSEPPE OBLACH 73","stato":"ASSEGNATA","telefono_cliente":"3496259508"}'
```

   - La pagina di inserimento manuale è raggiungibile dal frontend in `web/publica/manual_entry.html` (link 'Inserimento Manuale' nell'index) e offre:
     - campi principali (numero WR, cliente, indirizzo, orari, stato)
     - textarea per incollare JSON con campi extra
     - possibilità di usare `X-API-Key` o `Bearer token` per autenticazione
- `GET /works/`: Lista lavori
- `PUT /works/{id}/assign/{tech_id}`: Assegna lavoro
- `PUT /works/{id}/status`: Aggiorna stato

- `POST /documents/upload`: Carica uno o più file PDF (multipart/form-data `files`)
### Documents (PDF import)
Use this endpoint to import PDF files that contain bolle (WR): the parser will try to extract the WR number and fields and will create or update works. CSV/JSON upload features were removed because they caused confusion.
- `POST /documents/upload`: Carica uno o più file PDF (multipart/form-data `files`)
- `GET /documents/`: Lista documenti caricati
- `GET /documents/{id}`: Ottieni metadati e parsed_data del documento
- `POST /documents/{id}/parse`: Analizza il documento e popola `parsed_data`
- `POST /documents/{id}/apply`: Applica `parsed_data` per creare o aggiornare un lavoro (accetta override JSON opzionale)
 - `POST /documents/{id}/apply`: Applica `parsed_data` per creare o aggiornare un lavoro (accetta override JSON opzionale)
   - Optional query param: `selected_indices` as a comma-separated list of indices (0-based) to apply only a subset of parsed entries. Example:
     - `POST /documents/42/apply?selected_indices=0,2` will only apply entries with index 0 and 2 from the parsed results.
  - Nota: se il PDF contiene più clienti/lavori, il parser prova a rilevare tutti gli WR presenti e `parsed_data` conterrà una lista `entries`. La chiamata `POST /documents/{id}/apply` applicherà tutte le entries trovate e creerà/aggiornerà un Work per ciascuna. Verranno inseriti gli id dei lavori creati/aggiornati dentro `parsed_data.applied_work_ids` e `applied_work_id` verrà impostato sul primo id per compatibilità.
- `GET /documents/{id}/download`: Scarica il documento (binary)

Notes:
- When a document is applied, an association row is written to the `document_applied_works` table for each created/updated Work. This allows tracking which Works were created/updated by which Document and when (`applied_at`).
- The `parsed_data` JSON still contains `applied_work_ids` for backward compatibility and convenience, but the `document_applied_works` table is the canonical mapping.

### Technicians
- `GET /technicians/`: Lista tecnici
- `POST /technicians/`: Crea tecnico

### Teams
- `GET /teams/`: Lista squadre
- `POST /teams/`: Crea squadra

### Stats
 - `GET /stats/yearly`: Statistiche per anno (ultimo anno), utili per analizzare trend annui

## Telegram Bot Comandi
 - `GET /debug/db`: Endpoint di debug per leggere tabelle del DB (richiede admin/backoffice o X-API-Key), utile se serve leggere il DB manualmente
- `/start`: Avvio
- `/help`: Mostra i comandi disponibili
 - Il sistema invia notifiche ai tecnici quando ci sono aggiornamenti sui lavori assegnati, migliorando la comunicazione e la reattività.
- `/accetta <WR>`: Accetta lavoro
- `/rifiuta <WR>`: Rifiuta lavoro
- `/chiudi <WR>`: Chiudi un lavoro

Nota: Se l'app è configurata come webhook (FastAPI) il server imposta i comandi del bot all'avvio, quindi gli operatori vedranno il menu automaticamente.

Se `/help` non è visibile nel client Telegram, puoi forzare la registrazione dei comandi con gli script integrati:

 - `python scripts/set_bot_commands.py` -> Imposta i comandi del bot usando il token da `.env` o variabile d'ambiente.
 - `python scripts/get_bot_commands.py` -> Mostra i comandi attualmente registrati per il bot.

Assicurati di aver impostato `TELEGRAM_BOT_TOKEN` in `.env` o nell'ambiente prima di eseguire gli script.

### Polling vs Webhook

- Il bot può essere eseguito in due modalità: polling (il bot interroga Telegram per aggiornamenti) o webhook (Telegram invia aggiornamenti al server web).
- Se usi webhook (configura `TELEGRAM_WEBHOOK_URL`), non avviare il bot in polling per lo stesso token: Telegram non permette contemporaneamente polling e webhook.
- Per sicurezza, il servizio `bot.service` non avvierà il polling automaticamente se `TELEGRAM_WEBHOOK_URL` è configurato e `TELEGRAM_POLLING` non è esplicitamente impostato a `true`.
- Per forzare il polling (solo se non usi webhook), imposta `TELEGRAM_POLLING=true` nell'ambiente. Per disabilitarlo, imposta `TELEGRAM_POLLING=false`.

Esempio (systemd drop-in o file environment):
```
Environment=TELEGRAM_BOT_TOKEN=yourtoken
# Optional: disable polling if you use webhook
Environment=TELEGRAM_POLLING=false
# Optional: set webhook url
Environment=TELEGRAM_WEBHOOK_URL=https://your-host.example.com/telegram/webhook
```

Mobile UI: ho aggiunto alcune ottimizzazioni a `web/publica/index.html` per migliorare l'usabilità su dispositivi mobili (meta viewport, bottoni full width su mobile, dimensionamento chart responsivo). Se vuoi ulteriori modifiche (es. layout dedicato mobile), posso implementarle.

## Roadmap

1. Implementare OCR avanzato per parsing bolle
2. Aggiungere notifiche push ai tecnici
3. Dashboard con grafici (Chart.js)
4. Sistema di punteggio tecnici
5. Modalità offline per bot
6. QR Code per accesso rapido
7. Validazione automatica indirizzi/operatori
8. Timeline lavori
9. Integrazione GPS per tracking
10. Report PDF statistiche

## Sicurezza

- Porta 6030 protetta con nftables
- fail2ban attivo
- API key per autenticazione
- Crittografia dati sensibili

### Uso della API key

Le rotte amministrative (creazione team, tecnici, upload WR, assegnazioni) richiedono la API key inviata nell'header `X-API-Key`.

Esempio con curl:

```
export API_KEY=your_api_key_here
curl -X POST -H "X-API-Key: $API_KEY" "http://localhost:6030/teams/?nome=TeamX"
```

## Development & Testing: Forcing Direct Backend

While the static UI prefers same-origin requests when served on port `6031` (so Apache can inject `X-API-Key`), developers running a local backend can force the UI to call the backend directly for testing. Use the following approaches (development only):

- In the UI, the "Forza backend locale" toggle will appear when visiting the site at `localhost` or `127.0.0.1` and will set `FORCE_DIRECT_API` in `sessionStorage`.
- For a one-off override in the browser console:

  window.__API_BASE__ = 'http://127.0.0.1:6030';

Notes:
- This bypasses Apache header injection and is intended for local development only.
- In production, the backend should be reached via Apache and bound to `127.0.0.1` to prevent direct network exposure of sensitive APIs.

Per la produzione raccomando di abilitare logging su file (ad esempio `logs/ftth.log`) e un jail `fail2ban` per monitorare tentativi ripetuti sospetti. Ho aggiunto un semplice logger rotante all'app (`logs/ftth.log`) che può essere usato per questo scopo.