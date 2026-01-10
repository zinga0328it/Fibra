# 📡 FTTH Equipment Tracking Workflow - Guida Operativa

## 🎯 Flusso Completo di Tracciamento Equipaggiamento

Guida dettagliata per la gestione del ciclo di vita dei modem e ONT durante le installazioni.

---

## 📊 Stati dell'Equipaggiamento

### Modem States
- **`available`**: In magazzino, pronto per assegnazione
- **`assigned`**: Assegnato a un lavoro, in consegna
- **`installed`**: Installato presso cliente
- **`faulty`**: Guasto, da riparare o sostituire

### ONT States
- **`available`**: In magazzino, pronto per assegnazione
- **`assigned`**: Assegnato a un lavoro, in consegna
- **`installed`**: Installato presso cliente
- **`returned`**: Restituito in magazzino

---

## 🔄 Workflow Standard Installazione

### Fase 1: Preparazione (Ufficio/Magazzino)
```bash
# Verifica equipment disponibile
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" | jq '.[] | select(.status == "available")'

# Crea lavoro se necessario
curl -X POST "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/" \
  -H "Content-Type: application/json" \
  -d '{
    "numero_wr": "INSTALL-001",
    "operatore": "Fastweb",
    "indirizzo": "Via Cliente 123, Milano",
    "nome_cliente": "Mario Rossi",
    "tipo_lavoro": "attivazione"
  }'
```

### Fase 2: Assegnazione Equipment
```bash
# Assegna modem al lavoro
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/WORK_ID/modem/MODEM_ID" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU="

# Verifica assegnazione
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/WORK_ID/equipment" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" | jq '.'
```

**Cosa cambia:**
- Modem status: `available` → `assigned`
- Work flag: `requires_modem = true`
- Modem collegato al work_id specifico

### Fase 3: Consegna al Cliente (In loco)
```bash
# Segna consegna effettuata
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/WORK_ID/equipment/delivered?modem_delivered=true" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU="
```

**Cosa cambia:**
- Work flag: `modem_delivered = true`
- Storico consegna registrato
- Modem rimane `assigned` (non ancora installato)

### Fase 4: Installazione (In loco)
```bash
# Marca modem come installato
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/MODEM_ID/install" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU="
```

**Cosa cambia:**
- Modem status: `assigned` → `installed`
- Timestamp: `installed_at = now()`
- Modem pronto per configurazione

### Fase 5: Configurazione e Note (In loco)
```bash
# Aggiungi dettagli installazione
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/MODEM_ID" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" \
  -d '{
    "installation_notes": "Installato in sala, connessione VDSL 50Mbps stabile",
    "technician_notes": "Cliente aveva vecchio modem TIM, sostituzione completata",
    "wifi_ssid": "ClienteCasa_2.4GHz",
    "wifi_password": "PasswordCliente123",
    "admin_username": "admin",
    "admin_password": "password_admin"
  }'
```

**Cosa viene registrato:**
- Note tecniche dettagliate
- Configurazioni WiFi
- Credenziali amministratore
- Osservazioni del tecnico

---

## 🔍 Verifica Stati in Tempo Reale

### Controllo Stato Equipment di un Lavoro
```bash
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/WORK_ID/equipment" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" | jq '.'
```

**Risposta attesa:**
```json
{
  "work_id": 46,
  "requires_ont": false,
  "requires_modem": true,
  "ont_delivered": false,
  "modem_delivered": true,
  "modem": {
    "id": 2,
    "serial_number": "DEMO-MODEM-001",
    "status": "installed",
    "model": "Technicolor TG800",
    "installation_notes": "Installato in sala...",
    "wifi_ssid": "ClienteCasa_2.4GHz"
  }
}
```

### Controllo Inventario Generale
```bash
# Modem disponibili
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" | jq '.[] | select(.status == "available")'

# Modem installati oggi
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" | jq '.[] | select(.status == "installed" and (.installed_at | contains("2026-01-05")))'
```

---

## ⚠️ Scenari di Errore Comuni

### Modem già assegnato
**Sintomo:** Errore "Modem is not available"
```bash
# Verifica stato modem
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/MODEM_ID" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" | jq '.status'

# Se assigned, controlla a quale lavoro
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/MODEM_ID" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" | jq '.work_id'
```

### Serial number duplicato
**Sintomo:** Errore "Serial number already exists"
```bash
# Cerca modem esistente
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" | jq '.[] | select(.serial_number == "SERIAL_DUPLICATO")'
```

### Lavoro senza equipment assegnato
**Sintomo:** `requires_modem = false`
```bash
# Verifica e assegna equipment
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/WORK_ID/modem/MODEM_ID" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU="
```

---

## 🔄 Operazioni di Manutenzione

### Restituzione Equipment
```bash
# Per modem non più necessario
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/MODEM_ID/return" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU="
```

### Aggiornamento Configurazione
```bash
# Modifica configurazione esistente
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/MODEM_ID/configure" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" \
  -d '{"wifi_ssid": "NuovoNome", "wifi_password": "NuovaPassword"}'
```

### Marcatura Guasto
```bash
# Segna equipment come guasto
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/MODEM_ID" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" \
  -d '{"status": "faulty", "technician_notes": "Guasto rilevato: no sync"}'
```

---

## 📊 Report e Statistiche

### Statistiche Equipment
```bash
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/stats/equipment" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" | jq '.'
```

### Report Installazioni Giornaliere
```bash
# Modem installati oggi
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" | \
  jq '[.[] | select(.status == "installed" and (.installed_at | startswith("2026-01-05")))] | length'
```

### Equipment per Stato
```bash
# Conteggio per stato
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" | \
  jq 'group_by(.status) | map({(.[0].status): length}) | add'
```

---

## 🎯 Best Practices

### Per Tecnici sul Campo
1. **Sempre verificare stato** prima di partire
2. **Segnare consegna** appena arrivati dal cliente
3. **Installare equipment** solo dopo test di funzionamento
4. **Documentare tutto** con note dettagliate
5. **Verificare configurazione** prima di andar via

### Per Ufficio Magazzino
1. **Controllare disponibilità** prima di assegnare
2. **Verificare serial numbers** per evitare duplicati
3. **Monitorare stati** per identificare colli di bottiglia
4. **Mantenere inventario aggiornato** in tempo reale

### Per Coordinamento
1. **Usare API per monitoraggio** real-time
2. **Controllare consegne** giornaliere
3. **Identificare problemi** di equipment rapidamente
4. **Ottimizzare processi** basandosi sui dati

---

## 🔧 Troubleshooting Equipment

### Equipment non si aggiorna
```bash
# Forza refresh stato
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/MODEM_ID" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" | jq '.'
```

### Stati inconsistenti
```bash
# Verifica work.equipment vs modem.status
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/WORK_ID/equipment" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" | jq '.'
```

### Note non salvate
```bash
# Verifica salvataggio
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/MODEM_ID" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" | jq '.installation_notes'
```

---

**Workflow implementato**: Gennaio 2026
**Sistema testato**: ✅ Flusso completo funzionante
**Documentazione**: Comandi curl verificati