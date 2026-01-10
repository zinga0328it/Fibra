# 🗺️ MAPPA COMANDI PC ALEX - API YGGDRASIL FTTH
## Sistema di Gestione Lavori e Equipaggiamenti

**Endpoint Base:** `http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030`
**Autenticazione:** Header `X-KEY: ftth_ygg_secret_2025`

**✅ VERIFICATO:** La porta 6030 funziona correttamente via Yggdrasil (testato da PC Alex)
**⚠️ NOTA:** Alcuni endpoint (onts/modems/sync) potrebbero richiedere l'API Yggdrasil separata su porta diversa

---

## 📋 GESTIONE LAVORI

**⚠️ NOTA:** Gli endpoint `/ingest/work` e `/ingest/bulk` sono disponibili SOLO nell'API Yggdrasil separata (porta diversa dalla 6030). Sulla porta 6030 questi endpoint restituiscono "Not Found".

### 1. Creare/Aggiornare Lavoro Singolo (API Yggdrasil separata)
```bash
curl -X POST "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:{PORTA_YGG}/ingest/work" \
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

### 2. Creare/Aggiornare Lavori Multipli (Bulk) (API Yggdrasil separata)
```bash
curl -X POST "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:{PORTA_YGG}/ingest/bulk" \
  -H "Content-Type: application/json" \
  -H "X-KEY: ftth_ygg_secret_2025" \
  -d '{
    "works": [
      {
        "numero_wr": "WR-010",
        "nome_cliente": "Sara Neri",
        "indirizzo": "Via Venezia 111, Firenze",
        "operatore": "Tecnico D",
        "tipo_lavoro": "Installazione FTTH",
        "telefono_cliente": "3337778888",
        "note": "Prima installazione"
      },
      {
        "numero_wr": "WR-011",
        "nome_cliente": "Marco Blu",
        "indirizzo": "Via Genova 222, Palermo",
        "operatore": "Tecnico E",
        "tipo_lavoro": "Manutenzione",
        "telefono_cliente": "3338889999",
        "note": "Controllo periodico"
      }
    ],
    "source": "pc_alex_import"
  }'
```

---

## 📡 GESTIONE ONT

**⚠️ NOTA:** Questi endpoint potrebbero non essere disponibili sulla porta 6030. Se restituiscono "Not Found", utilizzare l'API Yggdrasil separata su porta diversa.

### 3. Creare Nuovo ONT
```bash
curl -X POST "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/onts/" \
  -H "Content-Type: application/json" \
  -H "X-KEY: ftth_ygg_secret_2025" \
  -d '{
    "serial_number": "ONT-ABC123456",
    "model": "Huawei HG8245H",
    "manufacturer": "Huawei",
    "pon_port": "0/1/0",
    "vlan_id": 100,
    "ip_address": "192.168.1.100",
    "location": "Magazzino Centrale"
  }'
```

### 4. Assegnare ONT a Lavoro
```bash
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/onts/{ont_id}/assign/{work_id}" \
  -H "X-KEY: ftth_ygg_secret_2025"
```

### 5. Installare ONT
```bash
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/onts/{ont_id}/install" \
  -H "Content-Type: application/json" \
  -H "X-KEY: ftth_ygg_secret_2025" \
  -d '{
    "pon_port": "0/1/0",
    "vlan_id": 100,
    "ip_address": "192.168.1.100",
    "installation_notes": "Installazione completata con successo"
  }'
```

### 6. Restituire ONT
```bash
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/onts/{ont_id}/return" \
  -H "X-KEY: ftth_ygg_secret_2025"
```

---

## 📶 GESTIONE MODEM

**⚠️ NOTA:** Questi endpoint potrebbero non essere disponibili sulla porta 6030. Se restituiscono "Not Found", utilizzare l'API Yggdrasil separata su porta diversa.

### 7. Creare Nuovo Modem
```bash
curl -X POST "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/" \
  -H "Content-Type: application/json" \
  -H "X-KEY: ftth_ygg_secret_2025" \
  -d '{
    "serial_number": "MODEM-XYZ789012",
    "model": "TIM HUB+",
    "manufacturer": "TIM",
    "wifi_ssid": "TIM-ABC123",
    "wifi_password": "password123",
    "location": "Magazzino Centrale"
  }'
```

### 8. Assegnare Modem a Lavoro
```bash
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/{modem_id}/assign/{work_id}" \
  -H "X-KEY: ftth_ygg_secret_2025"
```

### 9. Installare Modem
```bash
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/{modem_id}/install" \
  -H "Content-Type: application/json" \
  -H "X-KEY: ftth_ygg_secret_2025" \
  -d '{
    "installation_notes": "Modem installato e configurato"
  }'
```

### 10. Configurare Modem
```bash
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/{modem_id}/configure" \
  -H "Content-Type: application/json" \
  -H "X-KEY: ftth_ygg_secret_2025" \
  -d '{
    "wifi_ssid": "TIM-ABC123-NEW",
    "wifi_password": "newpassword123",
    "technician_notes": "Configurazione WiFi aggiornata"
  }'
```

### 11. Restituire Modem
```bash
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/{modem_id}/return" \
  -H "X-KEY: ftth_ygg_secret_2025"
```

---

## 🔄 SINCRONIZZAZIONE ONT + MODEM

**⚠️ NOTA:** Questi endpoint potrebbero non essere disponibili sulla porta 6030. Se restituiscono "Not Found", utilizzare l'API Yggdrasil separata su porta diversa.

### 12. Creare Sincronizzazione
```bash
curl -X POST "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/sync/{ont_id}/{modem_id}" \
  -H "Content-Type: application/json" \
  -H "X-KEY: ftth_ygg_secret_2025" \
  -d '{
    "sync_type": "wifi_bridge",
    "notes": "Sincronizzazione ONT-Modem per bridge WiFi"
  }'
```

### 13. Completare Sincronizzazione
```bash
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/sync/{sync_id}/complete" \
  -H "X-KEY: ftth_ygg_secret_2025"
```

---

## 📊 STATISTICHE E MONITORAGGIO

### 14. Statistiche Settimanali
```bash
curl -X GET "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/stats/weekly" \
  -H "X-KEY: ftth_ygg_secret_2025"
```

### 15. Statistiche Equipaggiamenti
```bash
curl -X GET "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/stats/equipment" \
  -H "X-KEY: ftth_ygg_secret_2025"
```

### 16. Statistiche Installazioni
```bash
curl -X GET "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/stats/installations" \
  -H "X-KEY: ftth_ygg_secret_2025"
```

---

## 🔍 CONSULTAZIONE DATI

### 17. Lista Tutti i Lavori
```bash
curl -X GET "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/" \
  -H "X-KEY: ftth_ygg_secret_2025"
```

### 18. Dettagli Lavoro Specifico
```bash
curl -X GET "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/{work_id}" \
  -H "X-KEY: ftth_ygg_secret_2025"
```

### 19. Lista Tutti gli ONT
```bash
curl -X GET "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/onts/" \
  -H "X-KEY: ftth_ygg_secret_2025"
```

### 20. Lista Tutti i Modem
```bash
curl -X GET "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/" \
  -H "X-KEY: ftth_ygg_secret_2025"
```

---

## ⚡ COMANDI RAPIDI PYTHON

### Script Base per PC Alex (API Yggdrasil separata)
```python
import requests

# Configurazione - USA LA PORTA DELL'API YGGDRASIL SEPARATA
BASE_URL = "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:{PORTA_YGG}"
HEADERS = {
    "Content-Type": "application/json",
    "X-KEY": "ftth_ygg_secret_2025"
}

# Esempio: Creare lavoro
work_data = {
    "numero_wr": "WR-ALEX-001",
    "nome_cliente": "Cliente da PC Alex",
    "indirizzo": "Via Test 123",
    "operatore": "PC Alex",
    "tipo_lavoro": "Test Yggdrasil",
    "telefono_cliente": "3330000000",
    "note": "Lavoro creato da PC Alex via Yggdrasil"
}

response = requests.post(f"{BASE_URL}/ingest/work", json=work_data, headers=HEADERS)
print("Risposta:", response.json())
```

---

## 🧪 SCRIPT DI TEST COMPLETO

### Script Automatico per PC Alex
```bash
# Scarica ed esegui lo script di test completo
python3 test_yggdrasil_complete.py
```

**Cosa fa lo script:**
- ✅ Testa API principale (porta 6030) - health, works, stats
- 🔍 Cerca automaticamente API Yggdrasil separata su porte comuni
- 🧪 Testa ingest work quando trova l'API Yggdrasil
- 📊 Riporta risultati dettagliati per ogni endpoint

**File:** `test_yggdrasil_complete.py` (pronto per PC Alex)

---

## 🚨 NOTE IMPORTANTI

1. **Sempre includere l'header X-KEY** in ogni richiesta
2. **Usare indirizzi IPv6** per Yggdrasil: `[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]`
3. **Verificare la connettività Yggdrasil** prima di eseguire comandi
4. **I numeri WR devono essere univoci** per nuovi lavori
5. **API principale (porta 6030)**: `/works/`, `/stats/`, `/health/` - endpoint di lettura/gestione
6. **API Yggdrasil separata (porta diversa)**: `/ingest/work`, `/ingest/bulk` - per inserire dati da remoto
7. **Usare POST per creare, PUT per aggiornare, GET per leggere**

---

## 🐛 TROUBLESHOOTING

- **"Connection refused"**: Verificare che il server sia attivo sulla porta corretta
- **"Invalid API key"**: Controllare che X-KEY sia corretto
- **"Work already exists"**: Usare numero WR diverso per nuovi lavori
- **"Not Found" per /ingest/**: Questi endpoint sono SOLO nell'API Yggdrasil separata (non su porta 6030)
- **"Not Found" per /onts/, /modems/, /sync/**: Questi endpoint potrebbero essere su API Yggdrasil separata (porta diversa)
- **Timeout**: La rete Yggdrasil potrebbe essere lenta, riprovare
- **API principale (6030)**: Per lettura dati esistenti e gestione lavori
- **API Yggdrasil separata**: Per inserimento nuovi dati da PC remoti

---

*Documento creato per PC Alex - Test Yggdrasil FTTH System*

---

## Test Rapido da Terminale
```bash
# Test API principale (porta 6030)
echo "🔍 Test API principale..."
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/health/" | head -3

echo -e "\n📊 Test lista lavori..."
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/" | jq '.[0] | {numero_wr, nome_cliente, stato}' 2>/dev/null || echo "jq non disponibile"

# Test API Yggdrasil separata (prova porte comuni)
echo -e "\n🔍 Cercando API Yggdrasil..."
for port in 8600 6040 6031 8000; do
    echo "Testando porta $port..."
    if curl -s --connect-timeout 3 "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:$port/health/" > /dev/null 2>&1; then
        echo "✅ API Yggdrasil trovata su porta $port!"
        break
    fi
done
```