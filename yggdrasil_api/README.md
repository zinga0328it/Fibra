# FTTH Yggdrasil API

API FastAPI che gira sulla rete privata Yggdrasil per comunicazione sicura tra PC.

## Struttura

```
yggdrasil_api/
├── main.py              # App principale FastAPI
├── routers/
│   ├── ingest.py        # Ricezione dati da fonti esterne
│   ├── jobs.py          # Gestione job in background
│   └── manual.py        # Inserimento manuale dati
├── .env.example         # Configurazione esempio
├── start.sh             # Script avvio manuale
└── ftth_ygg.service     # Systemd service
```

## Setup

### 1. Configura ambiente

```bash
cd /home/aaa/fibra/yggdrasil_api
cp .env.example .env
nano .env  # Modifica YGG_HOST e YGG_API_KEY
```

### 2. Avvio manuale (test)

```bash
chmod +x start.sh
./start.sh
```

### 3. Avvio come servizio

```bash
# Copia service file
sudo cp ftth_ygg.service /etc/systemd/system/

# Abilita e avvia
sudo systemctl daemon-reload
sudo systemctl enable ftth_ygg.service
sudo systemctl start ftth_ygg.service

# Verifica
sudo systemctl status ftth_ygg.service
```

## Endpoints

### Health Check (no auth)
- `GET /health` - Stato del servizio
- `GET /` - Info base

### Ingest (richiede X-KEY header)
- `POST /ingest/work` - Inserisci singolo lavoro
- `POST /ingest/bulk` - Inserisci multipli lavori
- `GET /ingest/status` - Stato coda ingest

### Jobs (richiede X-KEY header)
- `POST /jobs/create` - Crea job (sync, backup)
- `GET /jobs/status/{job_id}` - Stato job
- `GET /jobs/list` - Lista job
- `DELETE /jobs/clear` - Pulisci job completati

### Manual (richiede X-KEY header)
- `POST /manual/work` - Crea lavoro manuale
- `PUT /manual/work/{id}` - Modifica lavoro
- `DELETE /manual/work/{id}` - Elimina lavoro
- `POST /manual/work/{id}/status` - Cambia stato
- `POST /manual/technician` - Crea tecnico
- `GET /manual/technicians` - Lista tecnici
- `POST /manual/sync/push` - Push a server remoto
- `POST /manual/sync/pull` - Pull da server remoto

## Esempio chiamata

```bash
# Health check
curl http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6040/health

# Crea lavoro (con auth)
curl -X POST http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6040/manual/work \
  -H "X-KEY: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"numero_wr": "WR-TEST", "nome_cliente": "Test"}'
```

## Comunicazione tra PC

### PC A (Server con sito web)
- Yggdrasil: `200:xxxx:....:A`
- API: porta 6030

### PC B (Questo PC - Gestionale)
- Yggdrasil: `200:421e:6385:4a8b:dca7:cfb:197f:e9c3`
- API: porta 6040

### Configurazione comunicazione

Nel `.env` di questo PC:
```
REMOTE_YGG_HOST=200:xxxx:....:A
REMOTE_API_URL=http://[200:xxxx:....:A]:6030
```

Poi i router possono fare sync bidirezionale tramite Yggdrasil.
