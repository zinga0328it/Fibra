# FTTH Yggdrasil API

API FastAPI che gira sulla rete privata Yggdrasil per comunicazione sicura tra PC e ingest di dati nel database FTTH.

## Struttura

```
yggdrasil_api/
├── main.py              # App principale FastAPI
├── routers/
│   └── ingest.py        # Ingest dati da PC remoti nel database
├── .env                 # Configurazione (YGG_HOST, YGG_PORT, YGG_API_KEY)
├── .env.example         # Template configurazione
├── start.sh             # Script avvio manuale
├── ftth_ygg.service     # Systemd service
└── README.md            # Questa documentazione
```

## Setup

### 1. Configura ambiente

```bash
cd /home/aaa/fibra/yggdrasil_api
cp .env.example .env
nano .env  # Modifica configurazione
```

File `.env`:
```properties
# Yggdrasil API Configuration
YGG_HOST=200:421e:6385:4a8b:dca7:cfb:197f:e9c3
YGG_PORT=8600
YGG_API_KEY=ftth_ygg_secret_2025
```

### 2. Avvio manuale (test)

```bash
# Dalla directory yggdrasil_api
source ../venv/bin/activate
python3 -m uvicorn main:app --host 200:421e:6385:4a8b:dca7:cfb:197f:e9c3 --port 8600
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
- `GET /` - Info API e documentazione
- `GET /health` - Stato del servizio
- `GET /docs` - Swagger UI documentazione
- `GET /openapi.json` - Schema OpenAPI

### Ingest (richiede X-KEY header)
- `POST /ingest/work` - Inserisci singolo lavoro nel database
- `POST /ingest/bulk` - Inserisci multipli lavori contemporaneamente

## Esempi di Chiamata

### Health Check
```bash
curl http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:8600/health
```

### Inserisci Singolo Lavoro
```bash
curl -X POST "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:8600/ingest/work" \
  -H "Content-Type: application/json" \
  -H "X-KEY: ftth_ygg_secret_2025" \
  -d '{
    "numero_wr": "WR-001",
    "nome_cliente": "Mario Rossi",
    "indirizzo": "Via Roma 123, Milano",
    "operatore": "Tecnico A",
    "tipo_lavoro": "Installazione FTTH",
    "telefono_cliente": "3331234567",
    "note": "Installazione urgente",
    "extra_fields": {
      "priorita": "alta",
      "data_appuntamento": "2025-01-15"
    }
  }'
```

### Inserisci Lavori Multipli
```bash
curl -X POST "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:8600/ingest/bulk" \
  -H "Content-Type: application/json" \
  -H "X-KEY: ftth_ygg_secret_2025" \
  -d '{
    "works": [
      {
        "numero_wr": "WR-010",
        "nome_cliente": "Sara Neri",
        "indirizzo": "Via Venezia 111, Firenze",
        "operatore": "Tecnico D",
        "tipo_lavoro": "Installazione FTTH"
      },
      {
        "numero_wr": "WR-011",
        "nome_cliente": "Marco Blu",
        "indirizzo": "Via Genova 222, Palermo",
        "operatore": "Tecnico E",
        "tipo_lavoro": "Manutenzione"
      }
    ],
    "source": "batch_import"
  }'
```

## Database Integration

L'API Yggdrasil scrive direttamente nel database principale del sistema FTTH (`../ftth.db`):

- **Database**: SQLite (`ftth.db`)
- **Tabella**: `works`
- **Campi supportati**: numero_wr, nome_cliente, indirizzo, operatore, tipo_lavoro, telefono_cliente (in extra_fields), note, extra_fields
- **Operazioni**: CREATE (nuovi lavori), UPDATE (lavori esistenti)

## Sicurezza

- **Rete**: Yggdrasil IPv6 mesh privata (non esposta su Internet)
- **Autenticazione**: Header `X-KEY` obbligatorio per tutti gli endpoint di scrittura
- **Chiave API**: `ftth_ygg_secret_2025` (configurata in `.env`)

## Comunicazione tra PC

### PC Frontend (servicess.net - Pubblico)
- **Yggdrasil**: `201:27c:546:5df7:176:95f3:c909:6834`
- **Apache SSL**: Proxy pass verso backend Yggdrasil
- **GPT Integration**: Può leggere/scrivere database via Yggdrasil

### PC Backend (aaa-aaa - Nascosto)
- **Yggdrasil**: `200:421e:6385:4a8b:dca7:cfb:197f:e9c3`
- **API Backend**: Porta 6030 (FastAPI principale)
- **API Yggdrasil**: Porta 8600 (Questa API)
- **Database**: SQLite condiviso

### Flusso Dati
1. PC Frontend riceve richieste (browser/GPT)
2. Apache fa proxy pass sicuro a PC Backend via Yggdrasil
3. API Yggdrasil elabora e salva nel database
4. Risposta torna al frontend attraverso Yggdrasil

## Troubleshooting

### API non risponde
```bash
# Verifica Yggdrasil attivo
yggdrasilctl getPeers

# Test connessione diretta
ping6 200:421e:6385:4a8b:dca7:cfb:197f:e9c3

# Test API
curl "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:8600/health"
```

### Errore "Invalid API key"
```bash
# Verifica chiave nel .env
cat .env | grep YGG_API_KEY

# Test con chiave corretta
curl -H "X-KEY: ftth_ygg_secret_2025" \
     "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:8600/health"
```

### Database non aggiornato
```bash
# Verifica percorso database
ls -la ../ftth.db

# Test scrittura manuale
sqlite3 ../ftth.db "INSERT INTO works (numero_wr, nome_cliente) VALUES ('TEST', 'Test');"
```

## Stato Implementazione

- ✅ API Yggdrasil funzionante
- ✅ Integrazione database SQLite
- ✅ Endpoint singolo e bulk ingest
- ✅ Sicurezza con X-KEY authentication
- ✅ Documentazione completa
- ✅ Test end-to-end verificati

**Data ultimo aggiornamento: 15 Dicembre 2025**
