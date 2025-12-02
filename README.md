# Gestionale Fibra

Sistema gestionale per operazioni sul campo di telecomunicazioni (fibra ottica).

## Caratteristiche

- **Gestione Lavori**: Crea, modifica e traccia lavori con stati (aperto/in corso/in pausa/chiuso)
- **Gestione Tecnici**: Registra e gestisci i tecnici con i loro dati di contatto
- **Gestione Team**: Organizza i tecnici in team
- **Import Ordini**: Carica e analizza file PDF/WR per creare automaticamente nuovi lavori
- **Note e Foto**: Aggiungi note e foto ai lavori
- **Dashboard Statistiche**: Visualizza statistiche su lavori per giorno, operatore e team
- **Bot Telegram**: I tecnici possono ricevere notifiche, aggiornare lavori e caricare foto

## Tecnologie

- **Backend**: Python FastAPI + SQLAlchemy + PostgreSQL
- **Frontend**: HTML5 + Bootstrap 5 + Chart.js
- **Bot**: python-telegram-bot

## Installazione

### Con Docker (consigliato)

1. Clona il repository:
```bash
git clone https://github.com/your-repo/fibra.git
cd fibra
```

2. Crea il file `.env` dalla copia di esempio:
```bash
cp .env.example .env
```

3. Modifica le variabili in `.env` secondo necessità

4. Avvia i container:
```bash
docker-compose up -d
```

5. L'applicazione sarà disponibile su http://localhost:8000

### Installazione Manuale

1. Crea un ambiente virtuale Python:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oppure: venv\Scripts\activate  # Windows
```

2. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

3. Configura PostgreSQL e crea il database `fibra_db`

4. Imposta le variabili d'ambiente o crea un file `.env`

5. Avvia l'applicazione:
```bash
uvicorn app.main:app --reload
```

## Configurazione

### Variabili d'ambiente

| Variabile | Descrizione | Default |
|-----------|-------------|---------|
| DATABASE_URL | URL di connessione PostgreSQL | postgresql://postgres:postgres@localhost:5432/fibra_db |
| SECRET_KEY | Chiave segreta per l'applicazione | (da impostare) |
| DEBUG | Modalità debug | True |
| TELEGRAM_BOT_TOKEN | Token del bot Telegram | (opzionale) |
| UPLOAD_DIR | Directory per i file caricati | ./uploads |

### Configurazione Bot Telegram

1. Crea un nuovo bot con [@BotFather](https://t.me/botfather)
2. Ottieni il token del bot
3. Imposta `TELEGRAM_BOT_TOKEN` nel file `.env`
4. I tecnici possono usare il comando `/start` per ottenere il loro Chat ID
5. Inserisci il Chat ID nel profilo del tecnico dal pannello web

## API Endpoints

### Teams
- `GET /api/teams/` - Lista team
- `POST /api/teams/` - Crea team
- `GET /api/teams/{id}` - Dettaglio team
- `PUT /api/teams/{id}` - Modifica team
- `DELETE /api/teams/{id}` - Elimina team

### Technicians
- `GET /api/technicians/` - Lista tecnici
- `POST /api/technicians/` - Crea tecnico
- `GET /api/technicians/{id}` - Dettaglio tecnico
- `PUT /api/technicians/{id}` - Modifica tecnico
- `DELETE /api/technicians/{id}` - Elimina tecnico

### Jobs
- `GET /api/jobs/` - Lista lavori (con filtri opzionali)
- `POST /api/jobs/` - Crea lavoro
- `GET /api/jobs/{id}` - Dettaglio lavoro
- `PUT /api/jobs/{id}` - Modifica lavoro
- `DELETE /api/jobs/{id}` - Elimina lavoro
- `POST /api/jobs/{id}/notes` - Aggiungi nota
- `GET /api/jobs/{id}/notes` - Lista note
- `POST /api/jobs/{id}/photos` - Carica foto
- `GET /api/jobs/{id}/photos` - Lista foto

### Upload
- `POST /api/upload/workorder` - Carica file ordine lavoro (PDF/WR/TXT)

### Statistics
- `GET /api/statistics/` - Statistiche dashboard

## Licenza

MIT License - vedi file [LICENSE](LICENSE)
