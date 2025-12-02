# FTTH Management System

Sistema di gestione per lavori FTTH (Fiber To The Home) per installazione modem e attivazione linee su rete Open Fiber.

## Funzionalità

- Caricamento e parsing di bolle di lavoro (WR) da PDF, immagini o testo
- Assegnazione lavori ai tecnici
- Compilazione bolle via app mobile (Telegram Bot)
- Statistiche settimanali/mensili
- Dashboard per backoffice
- Sicurezza con nftables e fail2ban

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
7. Avvia backend: `uvicorn app.main:app --host 0.0.0.0 --port 5030`
8. Avvia bot: `python app/bot.py`

## API Routes

### Works
- `POST /works/upload`: Carica bolla
- `GET /works/`: Lista lavori
- `PUT /works/{id}/assign/{tech_id}`: Assegna lavoro
- `PUT /works/{id}/status`: Aggiorna stato

### Technicians
- `GET /technicians/`: Lista tecnici
- `POST /technicians/`: Crea tecnico

### Teams
- `GET /teams/`: Lista squadre
- `POST /teams/`: Crea squadra

### Stats
- `GET /stats/weekly`: Statistiche settimanali

## Telegram Bot Comandi

- `/start`: Avvio
- `/miei_lavori`: Lista lavori assegnati
- `/accetta <WR>`: Accetta lavoro
- `/rifiuta <WR>`: Rifiuta lavoro

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

- Porta 5030 protetta con nftables
- fail2ban attivo
- API key per autenticazione
- Crittografia dati sensibili

### Uso della API key

Le rotte amministrative (creazione team, tecnici, upload WR, assegnazioni) richiedono la API key inviata nell'header `X-API-Key`.

Esempio con curl:

```
export API_KEY=your_api_key_here
curl -X POST -H "X-API-Key: $API_KEY" "http://localhost:5030/teams/?nome=TeamX"
```

Per la produzione raccomando di abilitare logging su file (ad esempio `logs/ftth.log`) e un jail `fail2ban` per monitorare tentativi ripetuti sospetti. Ho aggiunto un semplice logger rotante all'app (`logs/ftth.log`) che può essere usato per questo scopo.