# 🔌 FTTH API Endpoints Reference - Gennaio 2026

## 📋 Riferimento Completo Endpoint API

Documentazione tecnica degli endpoint FastAPI con esempi curl funzionanti.

---

## 🏥 Health & Status

### GET /health/
**Descrizione**: Verifica stato del sistema
**Autenticazione**: No
**Risposta**: `{"status": "ok", "timestamp": "..."}`

```bash
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/health/"
```

---

## 📝 Gestione Lavori (Works)

### GET /works/
**Descrizione**: Lista tutti i lavori
**Autenticazione**: No
**Risposta**: Array di oggetti Work

```bash
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/" | jq '.'
```

### POST /works/
**Descrizione**: Crea nuovo lavoro
**Autenticazione**: No
**Body richiesto**:
```json
{
  "numero_wr": "TEST-001",
  "operatore": "Fastweb",
  "indirizzo": "Via Roma 123, Milano",
  "nome_cliente": "Mario Rossi",
  "tipo_lavoro": "attivazione",
  "stato": "aperto"
}
```

```bash
curl -X POST "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/" \
  -H "Content-Type: application/json" \
  -d '{
    "numero_wr": "TEST-001",
    "operatore": "Fastweb",
    "indirizzo": "Via Roma 123",
    "nome_cliente": "Mario Rossi",
    "tipo_lavoro": "attivazione",
    "stato": "aperto"
  }'
```

### GET /works/{work_id}
**Descrizione**: Dettagli lavoro specifico
**Autenticazione**: No

```bash
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/46"
```

### PUT /works/{work_id}/modem/{modem_id}
**Descrizione**: Assegna modem a lavoro
**Autenticazione**: API Key richiesta
**Effetto**: Modem status → "assigned", work.requires_modem → true

```bash
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/46/modem/2" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU="
```

### PUT /works/{work_id}/equipment/delivered
**Descrizione**: Segna consegna equipaggiamento
**Autenticazione**: API Key richiesta
**Parametri**: `ont_delivered=true/false`, `modem_delivered=true/false`

```bash
# Segna consegna modem
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/46/equipment/delivered?modem_delivered=true" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU="

# Segna consegna ONT
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/46/equipment/delivered?ont_delivered=true" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU="
```

### GET /works/{work_id}/equipment
**Descrizione**: Stato equipaggiamento del lavoro
**Autenticazione**: API Key richiesta
**Risposta**: Stato consegna e dettagli equipment

```bash
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/46/equipment" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" | jq '.'
```

### POST /works/ingest/work
**Descrizione**: Importa singolo lavoro da sistema esterno
**Autenticazione**: API Key richiesta
**Body**:
```json
{
  "numero_wr": "EXT-001",
  "stato": "aperto",
  "descrizione": "Lavoro importato",
  "tecnico": "Mario Rossi",
  "indirizzo": "Via Import 123",
  "cliente": "Cliente Esterno",
  "ont_sn": "ONT-EXT-001",
  "modem_sn": "MODEM-EXT-001"
}
```

```bash
curl -X POST "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/ingest/work" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" \
  -d '{
    "numero_wr": "EXT-001",
    "stato": "aperto",
    "indirizzo": "Via Import 123",
    "cliente": "Cliente Esterno"
  }'
```

### POST /works/ingest/bulk
**Descrizione**: Importa lavori multipli
**Autenticazione**: API Key richiesta
**Body**: `{"works": [array di oggetti WorkIngest]}`

---

## 📱 Gestione Modem

### GET /modems/
**Descrizione**: Lista tutti i modem
**Autenticazione**: API Key richiesta

```bash
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" | jq '.'
```

### POST /modems/
**Descrizione**: Crea nuovo modem
**Autenticazione**: API Key richiesta
**Body**:
```json
{
  "serial_number": "MODEM-001",
  "model": "Technicolor TG800",
  "type": "vdsl",
  "manufacturer": "Technicolor",
  "location": "Magazzino Milano"
}
```

```bash
curl -X POST "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" \
  -d '{
    "serial_number": "MODEM-001",
    "model": "Technicolor TG800",
    "type": "vdsl",
    "manufacturer": "Technicolor",
    "location": "Magazzino Milano"
  }'
```

### PUT /modems/{modem_id}/install
**Descrizione**: Marca modem come installato
**Autenticazione**: API Key richiesta
**Effetto**: status → "installed", installed_at → timestamp

```bash
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/2/install" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU="
```

### PUT /modems/{modem_id}
**Descrizione**: Aggiorna modem (note, configurazione, etc.)
**Autenticazione**: API Key richiesta

```bash
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/2" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" \
  -d '{
    "installation_notes": "Installato in cucina, connessione VDSL stabile",
    "technician_notes": "Cliente aveva vecchio modem TIM",
    "wifi_ssid": "ClienteCasa_WiFi",
    "wifi_password": "Password123"
  }'
```

---

## 🔌 Gestione ONT

### GET /onts/
**Descrizione**: Lista tutte le ONT
**Autenticazione**: API Key richiesta

```bash
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/onts/" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" | jq '.'
```

### POST /onts/
**Descrizione**: Crea nuova ONT
**Autenticazione**: API Key richiesta

```bash
curl -X POST "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/onts/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" \
  -d '{
    "serial_number": "ONT-001",
    "model": "Huawei HG8245H",
    "manufacturer": "Huawei",
    "location": "Magazzino Milano"
  }'
```

---

## 📊 Statistiche

### GET /stats/weekly
**Descrizione**: Statistiche settimanali
**Autenticazione**: No

```bash
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/stats/weekly" | jq '.'
```

### GET /stats/equipment
**Descrizione**: Statistiche equipaggiamento
**Autenticazione**: API Key richiesta

```bash
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/stats/equipment" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" | jq '.'
```

---

## 👥 Gestione Tecnici

### GET /technicians/
**Descrizione**: Lista tecnici
**Autenticazione**: No

```bash
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/technicians/" | jq '.'
```

---

## 🌐 Pagine Web

### GET /
**Descrizione**: Pagina index principale

```bash
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/" | head -10
```

### GET /gestionale.html
**Descrizione**: Interfaccia gestionale completa

```bash
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/gestionale.html" | head -10
```

---

## 🔑 Configurazione API

### API Key
```
JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=
```

### Endpoint che richiedono autenticazione
- Tutti gli endpoint `/modems/*`
- Tutti gli endpoint `/onts/*`
- `/works/ingest/*`
- `/works/*/equipment/*`
- `/stats/equipment`

### Header per autenticazione
```bash
-H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU="
```

---

## 🔄 Flusso Completo Installazione

```bash
# 1. Crea lavoro
curl -X POST "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/" \
  -H "Content-Type: application/json" \
  -d '{"numero_wr": "INSTALL-001", "operatore": "Fastweb", "indirizzo": "Via Cliente 123", "nome_cliente": "Mario Rossi"}'

# 2. Crea modem
curl -X POST "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" \
  -d '{"serial_number": "MODEM-INSTALL-001", "model": "Technicolor TG800", "type": "vdsl"}'

# 3. Assegna modem al lavoro
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/WORK_ID/modem/MODEM_ID" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU="

# 4. Segna consegna al cliente
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/WORK_ID/equipment/delivered?modem_delivered=true" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU="

# 5. Installa modem
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/MODEM_ID/install" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU="

# 6. Aggiungi note installazione
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/MODEM_ID" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" \
  -d '{"installation_notes": "Installato correttamente", "wifi_ssid": "ClienteCasa"}'

# 7. Verifica stato finale
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/WORK_ID/equipment" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" | jq '.'
```

---

## ⚠️ Codici Errore Comuni

- **403 Forbidden**: API Key mancante o invalida
- **404 Not Found**: Risorsa non esistente
- **422 Validation Error**: Dati mancanti nel body
- **500 Internal Server Error**: Problema database (controllare colonne)

---

**Documentazione aggiornata**: Gennaio 2026
**Sistema testato**: ✅ Tutti gli endpoint funzionanti