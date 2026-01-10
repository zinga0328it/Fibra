# 📚 FTTH Management System - Obsidian Documentation

## 🎯 Sistema di Programmazione Modulare AiVigilanza

Questa cartella contiene la documentazione interattiva del sistema FTTH Management, implementata secondo la filosofia **Obsidian Canvas modulare**.

## 🆕 **AGGIORNAMENTO GENNAIO 2026 - Nuove Funzionalità**

### 🚀 **Endpoint API Unificati**
- **Porta Unica**: Tutto sulla porta 6030 via Yggdrasil
- **Ingest Endpoints**: `/works/ingest/work` e `/works/ingest/bulk`
- **Autenticazione**: API Key per endpoint equipment
- **Web Interface**: Pagine HTML servite direttamente dalla root

### 📡 **Tracciamento Equipaggiamento Completo**
- **Modem Lifecycle**: Assegnazione → Consegna → Installazione → Note
- **ONT Management**: Gestione completa del ciclo di vita
- **Stati Equipment**: available → assigned → installed
- **Note Tecniche**: installation_notes, technician_notes, configuration_notes

### 🔧 **Flusso Operativo Installazione**
```
1. Crea Lavoro → 2. Assegna Equipment → 3. Segna Consegna → 4. Installa → 5. Aggiungi Note
```

### 🧪 **Testing Framework**
- **Comandi Curl**: Test completi documentati
- **Health Checks**: Verifica automatica dello stato sistema
- **API Validation**: Test di tutti gli endpoint
- **Equipment Tracking**: Verifica stato dell'inventario

## 🗂️ Struttura della Documentazione

### Canvas Principali

- **`FTTH-Index.canvas`** - Centro di comando principale
  - Architecture overview
  - Daily workflow aggiornato
  - Troubleshooting guidato
  - Link a tutti i moduli

### Canvas Modulari

- **`FTTH-Backend-Module.canvas`** - FastAPI e API REST
  - Nuovi endpoint ingest
  - Autenticazione API Key
  - Database schema aggiornato
- **`FTTH-Yggdrasil-Module.canvas`** - Sicurezza VPN mesh
  - Porta 6030 unificata
  - Firewall rules aggiornate
- **`FTTH-Database-Module.canvas`** - PostgreSQL/SQLite layer
  - Nuove colonne equipment
  - Schema sincronizzato
- **`FTTH-ONT-Modem-Project.canvas`** - **NUOVO** Equipment tracking
  - Flusso completo modem/ONT
  - Stati e transizioni
  - Note e configurazioni

### Documenti Markdown

- **`FTTH-Daily-Workflow.md`** - Checklist operativo aggiornato
  - Nuovi controlli API
  - Equipment tracking
  - Testing procedures
- **`FTTH-Troubleshooting.md`** - Guida risoluzione problemi
  - Problemi API comuni
  - Database desync
  - Equipment issues
  - Comandi test rapidi
- **`FTTH-API-Reference.md`** - **NUOVO** Riferimento API completo
  - Tutti gli endpoint documentati
  - Esempi curl funzionanti
  - Codici errore e risposte
- **`FTTH-Equipment-Workflow.md`** - **NUOVO** Guida operativa equipment
  - Flusso completo tracciamento
  - Stati e transizioni modem/ONT
  - Comandi operativi verificati

## 🚀 Come Utilizzare

### 1. Apri il Centro di Comando
```bash
# Apri sempre da qui
obsidian FTTH-Index.canvas
```

### 2. Navigazione Guidata
- **Architecture**: Vista generale del sistema aggiornato
- **Daily Workflow**: Operazioni quotidiane con nuovi controlli
- **Troubleshooting**: Risoluzione problemi con guide specifiche
- **Equipment Tracking**: Nuovo canvas per gestione modem/ONT

### 3. Workflow Operativo
```
Centro di Comando → Canvas Modulare → Configurazione Specifica → Test con Curl
```

## 🎨 Filosofia del Sistema

### Separazione delle Responsabilità
- **Un canvas = Un modulo**
- **Un modulo = Una responsabilità**
- **Ogni problema = Una soluzione documentata**

### Testing Integrato
- **Ogni funzionalità = Comandi test documentati**
- **Ogni problema = Soluzioni verificate**
- **Ogni endpoint = Esempi curl funzionanti**

## 📊 Metriche Sistema

### Disponibilità
- **API Uptime**: 99.9% target
- **Database**: Sempre disponibile
- **Yggdrasil**: Connessione stabile
- **Web Interface**: Accessibile 24/7

### Performance
- **API Response**: <500ms
- **Database Queries**: Ottimizzate
- **Memory Usage**: Monitorato
- **Equipment Tracking**: Real-time

### Sicurezza
- **API Keys**: Rotazione regolare
- **Firewall**: Regole Yggdrasil specifiche
- **Logs**: Audit completo
- **Backup**: Giornaliero automatico

## 🔧 Comandi Essenziali

### Avvio Sistema
```bash
# Backend
PYTHONPATH=/home/aaa/fibra python3 -m uvicorn app.main:app --host "200:421e:6385:4a8b:dca7:cfb:197f:e9c3" --port 6030

# Test completo
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/health/"
```

### Testing API
```bash
# Health check
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/health/"

# Lista risorse
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/"
curl -s "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/modems/" -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU="
```

### Equipment Tracking
```bash
# Assegna modem
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/46/modem/2" -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU="

# Segna consegna
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/46/equipment/delivered?modem_delivered=true" -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU="
```

## 📞 Supporto

- **Documentazione**: Sempre aggiornata in Obsidian
- **Testing**: Comandi curl verificati
- **Troubleshooting**: Guide passo-passo
- **Emergency**: Procedure documentate

---

**Ultimo Aggiornamento**: Gennaio 2026
**Versione Sistema**: 2.0 - Unified API + Equipment Tracking