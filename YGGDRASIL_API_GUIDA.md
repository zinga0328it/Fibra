# Guida API Yggdrasil - Gestione Lavori FTTH

## Panoramica

L'API Yggdrasil permette ai PC remoti connessi alla rete Yggdrasil di aggiungere e aggiornare lavori nel database centrale del sistema FTTH.

**Endpoint Base:** `http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:8600`

**Autenticazione:** Header `X-KEY: ftth_ygg_secret_2025`

## Endpoint Disponibili

### 1. Inserimento Singolo Lavoro

**Endpoint:** `POST /ingest/work`

**Descrizione:** Aggiunge o aggiorna un singolo lavoro nel database.

**Esempio richiesta:**
```json
{
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
}
```

**Esempio risposta (successo):**
```json
{
  "ok": true,
  "message": "Work WR-001 created",
  "received": 1,
  "processed": 1,
  "errors": []
}
```

### 2. Inserimento Bulk Lavori

**Endpoint:** `POST /ingest/bulk`

**Descrizione:** Aggiunge o aggiorna più lavori contemporaneamente.

**Esempio richiesta:**
```json
{
  "works": [
    {
      "numero_wr": "WR-010",
      "nome_cliente": "Sara Neri",
      "indirizzo": "Via Venezia 111, Firenze",
      "operatore": "Tecnico D",
      "tipo_lavoro": "Installazione FTTH",
      "telefono_cliente": "3337778888",
      "note": "Prima installazione",
      "extra_fields": {"priorita": "alta"}
    },
    {
      "numero_wr": "WR-011",
      "nome_cliente": "Marco Blu",
      "indirizzo": "Via Genova 222, Palermo",
      "operatore": "Tecnico E",
      "tipo_lavoro": "Manutenzione",
      "telefono_cliente": "3338889999",
      "note": "Controllo periodico",
      "extra_fields": {"priorita": "bassa"}
    }
  ],
  "source": "batch_import"
}
```

**Esempio risposta (successo):**
```json
{
  "ok": true,
  "message": "Bulk ingest from batch_import: 2 processed, 0 errors",
  "received": 2,
  "processed": 2,
  "errors": []
}
```

## Campi del Lavoro

| Campo | Tipo | Obbligatorio | Descrizione |
|-------|------|--------------|-------------|
| `numero_wr` | string | ✅ | Numero identificativo del lavoro (unico) |
| `nome_cliente` | string | ❌ | Nome del cliente |
| `telefono_cliente` | string | ❌ | Telefono del cliente (salvato in extra_fields) |
| `indirizzo` | string | ❌ | Indirizzo dell'installazione |
| `operatore` | string | ❌ | Nome dell'operatore/tecnico |
| `tipo_lavoro` | string | ❌ | Tipo di lavoro (Installazione, Manutenzione, Riparazione, etc.) |
| `note` | string | ❌ | Note aggiuntive |
| `data_appuntamento` | string | ❌ | Data appuntamento (salvata in extra_fields) |
| `extra_fields` | object | ❌ | Campi aggiuntivi personalizzati |

## Comportamento

- **Creazione:** Se `numero_wr` non esiste, viene creato un nuovo lavoro
- **Aggiornamento:** Se `numero_wr` esiste, vengono aggiornati solo i campi forniti
- **Telefono:** Salvato automaticamente in `extra_fields.telefono`
- **Stato:** I nuovi lavori vengono creati con stato "aperto"
- **Data:** La data di apertura viene impostata automaticamente al momento della creazione

## Esempi di Utilizzo

### Python Script
```python
import requests

# Configurazione
BASE_URL = "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:8600"
API_KEY = "ftth_ygg_secret_2025"

# Invio singolo lavoro
work_data = {
    "numero_wr": "WR-123",
    "nome_cliente": "Mario Rossi",
    "indirizzo": "Via Roma 123, Milano",
    "operatore": "Tecnico A",
    "tipo_lavoro": "Installazione FTTH",
    "telefono_cliente": "3331234567",
    "note": "Installazione urgente"
}

response = requests.post(
    f"{BASE_URL}/ingest/work",
    json=work_data,
    headers={"X-KEY": API_KEY}
)

print(response.json())
```

### cURL
```bash
curl -X POST "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:8600/ingest/work" \
  -H "Content-Type: application/json" \
  -H "X-KEY: ftth_ygg_secret_2025" \
  -d '{
    "numero_wr": "WR-123",
    "nome_cliente": "Mario Rossi",
    "indirizzo": "Via Roma 123, Milano",
    "operatore": "Tecnico A",
    "tipo_lavoro": "Installazione FTTH",
    "telefono_cliente": "3331234567",
    "note": "Installazione urgente"
  }'
```

## Sicurezza

- Tutti gli endpoint richiedono l'header `X-KEY` con la chiave API corretta
- La comunicazione avviene sulla rete Yggdrasil privata
- I dati vengono validati prima dell'inserimento nel database

## Troubleshooting

### Errore "Invalid API key"
- Verifica che l'header `X-KEY` sia presente e corretto

### Errore "address already in use"
- L'API potrebbe non essere in esecuzione. Riavvia il servizio Yggdrasil

### Lavoro non visibile nel database
- Verifica che l'API sia connessa al database corretto
- Controlla i log dell'API per eventuali errori
- Assicurati che il numero WR sia univoco per nuovi lavori

## Log e Monitoraggio

I log dell'API sono disponibili in `logs/yggdrasil_api.log`. Ogni richiesta viene registrata con:
- Timestamp
- IP del richiedente
- Operazione eseguita
- Esito (successo/errore)