# 🆘 FTTH Troubleshooting Guide - Interattivo

## 🔍 Guida alla Risoluzione Problemi

Questa guida è integrata con il sistema Obsidian Canvas. Ogni problema rimanda al canvas modulare specifico per la risoluzione guidata.

---

## 🔴 Problemi Backend (FastAPI)

### Sintomo: "API non risponde"
**Canvas**: [[FTTH-Backend-Module.canvas#systemd_service|Backend Systemd Service]]
```
Verifica: sudo systemctl status ftth
Soluzione: sudo systemctl restart ftth
Log: sudo journalctl -u ftth -f
Test: curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/health/"
```

### Sintomo: "Porta 6030 già in uso"
**Canvas**: [[FTTH-Backend-Module.canvas#troubleshooting_backend|Troubleshooting Backend]]
```
Comandi:
sudo ss -lntp | grep :6030
sudo kill -9 $(sudo lsof -t -i:6030)
sudo systemctl restart ftth
Test: curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/health/"
```

### Sintomo: "Errore database connection"
**Canvas**: [[FTTH-Database-Module.canvas#postgresql_config|Database Config]]
```
Verifica: cat .env | grep DATABASE_URL
Test: psql "$DATABASE_URL" -c "SELECT 1;"
Soluzione: sudo systemctl restart postgresql
```

### Sintomo: "Errore colonna mancante nel database"
**Problema**: Modello aggiornato ma database non sincronizzato
```
Sintomi: 500 Internal Server Error, colonne requires_ont/modems_delivered mancanti
Soluzione:
sqlite3 ftth.db "
ALTER TABLE works ADD COLUMN requires_ont BOOLEAN DEFAULT 0;
ALTER TABLE works ADD COLUMN requires_modem BOOLEAN DEFAULT 0;
ALTER TABLE works ADD COLUMN ont_delivered BOOLEAN DEFAULT 0;
ALTER TABLE works ADD COLUMN modem_delivered BOOLEAN DEFAULT 0;
ALTER TABLE works ADD COLUMN ont_cost FLOAT DEFAULT 0.0;
ALTER TABLE works ADD COLUMN modem_cost FLOAT DEFAULT 0.0;
"
Test: curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/"
```

---

## 🕸️ Problemi Yggdrasil Network

### Sintomo: "Impossibile raggiungere backend"
**Canvas**: [[FTTH-Yggdrasil-Module.canvas#connectivity_test|Connectivity Test]]
```
Test: ping6 200:421e:6385:4a8b:dca7:cfb:197f:e9c3
Verifica: ip addr show ygg0
Restart: sudo systemctl restart yggdrasil
API Test: curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/health/"
```

### Sintomo: "Yggdrasil non si connette"
**Canvas**: [[FTTH-Yggdrasil-Module.canvas#yggdrasil_config|Yggdrasil Config]]
```
Status: sudo systemctl status yggdrasil
Logs: sudo journalctl -u yggdrasil -f
Config: sudo cat /etc/yggdrasil.conf
Restart: sudo systemctl restart yggdrasil
```

### Sintomo: "Connessione Yggdrasil instabile"
**Canvas**: [[FTTH-Yggdrasil-Module.canvas#network_troubleshooting|Network Troubleshooting]]
```
Diagnosi:
ping6 -c 10 200:421e:6385:4a8b:dca7:cfb:197f:e9c3
sudo yggdrasilctl getPeers
sudo yggdrasilctl getSessions
Soluzione: Verificare configurazione peers e firewall
```

---

## 📡 Problemi API Endpoints

### Sintomo: "403 Forbidden - Invalid API Key"
**Problema**: Endpoint richiede autenticazione API key
```
Endpoint protetti: /modems/*, /onts/*, /works/ingest/*
Soluzione: Aggiungere header X-API-Key
curl -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" \
  "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/"
```

### Sintomo: "422 Validation Error"
**Problema**: Dati mancanti nella richiesta
```
Comune per: POST /works/ (mancano operatore, indirizzo, nome_cliente)
Soluzione: Verificare campi obbligatori nel body JSON
Esempio corretto:
{
  "numero_wr": "TEST-001",
  "operatore": "Fastweb",
  "indirizzo": "Via Roma 123",
  "nome_cliente": "Mario Rossi",
  "tipo_lavoro": "attivazione"
}
```

### Sintomo: "500 Internal Server Error su /works/"
**Problema**: Database desincronizzato con modello
```
Causa: Colonne mancanti nella tabella works
Soluzione: Vedi sezione "Errore colonna mancante nel database"
Test: curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/"
```

---

## 🔧 Problemi Equipment Tracking

### Sintomo: "Modem stuck in 'assigned' status"
**Problema**: Modem assegnato ma non consegnato/installato
```
Verifica stato: curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/ID" -H "X-API-Key: ..."
Soluzioni:
1. Segna consegna: PUT /works/WORK_ID/equipment/delivered?modem_delivered=true
2. Installa modem: PUT /modems/MODEM_ID/install
3. Aggiungi note: PUT /modems/MODEM_ID con installation_notes
```

### Sintomo: "Cannot assign modem - already assigned"
**Problema**: Modem già assegnato a un altro lavoro
```
Verifica: curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/" -H "X-API-Key: ..."
Trova modem available o restituisci quello esistente
```

### Sintomo: "ONT/Modem serial number already exists"
**Problema**: Tentativo di creare equipment con serial esistente
```
Verifica: curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/?serial_number=SERIAL" -H "X-API-Key: ..."
Soluzione: Usa serial number univoco o aggiorna equipment esistente
```

---

## 🌐 Problemi Web Interface

### Sintomo: "404 Not Found su pagine HTML"
**Problema**: Pagine non servite correttamente
```
URL errate: /gestionale.html (404)
URL corrette: http://[IP]:6030/gestionale.html
Verifica: curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/gestionale.html" | head -5
```

### Sintomo: "JavaScript API calls falliscono"
**Problema**: Frontend non riesce a chiamare API
```
Verifica console browser per errori CORS
Test API diretto: curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/"
Soluzione: Verificare che API sia attiva sulla porta 6030
```

---

## 📊 Problemi Ingest Endpoints

### Sintomo: "Ingest work fallisce con errore campi"
**Problema**: Campi del modello non corrispondono alla richiesta
```
L'endpoint /works/ingest/work usa campi specifici:
{
  "numero_wr": "string",
  "stato": "aperto/chiuso",
  "descrizione": "string",  // diventa note
  "tecnico": "Nome Cognome", // cerca tecnico per nome
  "indirizzo": "string",
  "cliente": "string",      // diventa nome_cliente
  "ont_sn": "string",       // va in extra_fields
  "modem_sn": "string"      // va in extra_fields
}
```

### Sintomo: "Bulk ingest parziale - alcuni lavori falliscono"
**Problema**: Errori in singoli elementi dell'array
```
Risposta include: success_count, error_count, errors[]
Verifica errori specifici e correggi dati
Esempio: Tecnico non trovato, serial number duplicato
```

---

## 🔄 Comandi di Test Rapidi

### Test Completo Sistema
```bash
# Health check
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/health/"

# Lista risorse
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/" | jq length
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/" -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" | jq length

# Test ingest
curl -X POST "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/ingest/work" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" \
  -d '{"numero_wr":"TEST-001","stato":"aperto","indirizzo":"Via Test","cliente":"Test"}'
```

### Verifica Stato Equipaggiamento
```bash
# Per un lavoro specifico
WORK_ID=46
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/$WORK_ID/equipment" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" | jq '.'
```

---

## 📞 Contatti di Supporto

- **Emergenza Backend**: Controllare logs in `/logs/ftth.log`
- **Emergenza Database**: Backup disponibile in `/opt/ftth/backups/`
- **Emergenza Network**: Contattare amministratore Yggdrasil
- **Documentazione**: Questa guida Obsidian è sempre aggiornata