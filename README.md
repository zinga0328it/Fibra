# Gestionale Python - Sistema FTTH Avanzato

Sistema di gestione ordini fibra ottica con architettura distribuita e IA integrata

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Yggdrasil](https://img.shields.io/badge/Yggdrasil-Network-orange.svg)](https://yggdrasil-network.github.io/)

## 📋 Indice

- [🏗️ Architettura Tecnica](#-architettura-tecnica)
- [✨ Caratteristiche Principali](#-caratteristiche-principali)
- [🚀 Quick Start](#-quick-start)
- [📦 Installazione](#-installazione)
- [⚙️ Configurazione](#️-configurazione)
- [🔧 Utilizzo](#-utilizzo)
- [🔒 Sicurezza](#-sicurezza)
- [🤖 Integrazione GPT](#-integrazione-gpt)
- [📊 API Reference](#-api-reference)
- [🧪 Testing](#-testing)
- [🚀 Deployment](#-deployment)
- [📚 Documentazione](#-documentazione)
- [🤝 Contributi](#-contributi)
- [📄 Licenza](#-licenza)

---

## 🏗️ Architettura Tecnica

Il sistema è costruito con un'architettura distribuita sicura che combina tecnologie moderne per garantire massima affidabilità e prestazioni.

```
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Frontend │ │ Apache Proxy │ │ Backend API │
│ (HTML/JS) │◄──►│ (mod_proxy) │◄──►│ (FastAPI) │
│ │ │ HTTPS/WSS │ │ Python 3.9+ │
└─────────────────┘ └─────────────────┘ └─────────────────┘
        │ │ │
        ▼ ▼ ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Yggdrasil │ │ fail2ban │ │ PostgreSQL │
│ IPv6 Network │ │ + nftables │ │ Database │
│ (Sicurezza) │ │ (Firewall) │ │ (Dati) │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Componenti Principali

- **Backend FastAPI**: Framework Python asincrono per API REST ad alte prestazioni
- **Yggdrasil Network**: Overlay network IPv6 crittografata per comunicazioni sicure
- **Apache Proxy**: Reverse proxy con terminazione SSL e bilanciamento del carico
- **PostgreSQL**: Database relazionale per persistenza dati con ottimizzazioni JSONB
- **fail2ban + nftables**: Sistema di sicurezza con ban automatici e firewall avanzato
- **WebSocket Integration**: Comunicazioni real-time per aggiornamenti live

---

## ✨ Caratteristiche Principali

- ✅ **Gestione Lavori FTTH**: Workflow completo da creazione a completamento
- ✅ **Architettura Distribuita**: Backend isolato via Yggdrasil IPv6
- ✅ **Sicurezza Zero-Trust**: Nessuna esposizione pubblica del backend
- ✅ **Integrazione GPT**: AI per automazione e assistenza intelligente
- ✅ **Telegram Bot**: Comunicazione real-time con tecnici
- ✅ **Dashboard Analytics**: Reportistica avanzata con metriche operative
- ✅ **API RESTful**: Interfacce standard per integrazioni terze parti
- ✅ **Mobile-First**: Ottimizzato per dispositivi mobili

---

## 🚀 Quick Start

### Prerequisiti

- Python 3.9+
- PostgreSQL (o SQLite per sviluppo)
- Yggdrasil Network configurato
- Apache/Nginx con SSL

### Installazione Rapida

```bash
# Clona il repository
git clone https://github.com/zinga0328it/fibra.git
cd fibra

# Crea ambiente virtuale
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Installa dipendenze
pip install -r requirements.txt

# Configura ambiente
cp .env.example .env
# Modifica .env con le tue configurazioni

# Avvia il database
# Per SQLite (sviluppo):
export DATABASE_URL="sqlite:///./ftth.db"

# Per PostgreSQL (produzione):
export DATABASE_URL="postgresql://user:password@localhost/ftth"

# Crea tabelle database
python -c "from app.database import engine; from app.models import models; models.Base.metadata.create_all(bind=engine)"

# Avvia il backend
uvicorn app.main:app --host 127.0.0.1 --port 6030

# In un altro terminal, avvia il bot Telegram
python app/bot.py
```

### Accesso al Sistema

- **Frontend**: https://servicess.net/fibra/
- **API Docs**: http://localhost:6030/docs (solo rete Yggdrasil)
- **Admin Panel**: https://servicess.net/fibra/admin

---

## 📦 Installazione

### 1. Clonazione Repository

```bash
git clone https://github.com/zinga0328it/fibra.git
cd fibra
```

### 2. Ambiente Virtuale Python

```bash
# Crea ambiente virtuale
python -m venv venv

# Attiva ambiente
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### 3. Dipendenze

```bash
# Installa tutte le dipendenze
pip install -r requirements.txt

# Verifica installazione
pip list
```

### 4. Database

#### Opzione A: SQLite (Sviluppo)

```bash
export DATABASE_URL="sqlite:///./ftth.db"
```

#### Opzione B: PostgreSQL (Produzione)

```bash
# Installa PostgreSQL
sudo apt-get install postgresql postgresql-contrib  # Ubuntu/Debian

# Crea database
sudo -u postgres createdb ftth
sudo -u postgres createuser ftth_user
sudo -u postgres psql -c "ALTER USER ftth_user PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ftth TO ftth_user;"

export DATABASE_URL="postgresql://ftth_user:your_password@localhost/ftth"
```

### 5. Yggdrasil Network

```bash
# Installa Yggdrasil
# Segui le istruzioni: https://yggdrasil-network.github.io/installation.html

# Verifica connessione
ping6 200:421e:6385:4a8b:dca7:cfb:197f:e9c3
```

---

## ⚙️ Configurazione

### File .env

Crea e configura il file `.env`:

```bash
cp .env.example .env
```

Contenuto essenziale:

```env
# Database
DATABASE_URL=sqlite:///./ftth.db

# Sicurezza
SECRET_KEY=your-super-secret-key-here
API_KEY=JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=

# Telegram Bot
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_WEBHOOK_URL=https://servicess.net/telegram/webhook

# Yggdrasil
YGGDRASIL_API_KEY=ftth_ygg_secret_2025

# OpenAI GPT (opzionale)
OPENAI_API_KEY=your-openai-key
```

### Apache Configuration

#### /etc/apache2/sites-available/fibra.conf

```apache
<VirtualHost *:443>
    ServerName servicess.net
    
    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/ssl-cert-snakeoil.pem
    SSLCertificateKeyFile /etc/ssl/private/ssl-cert-snakeoil.key
    
    ProxyPreserveHost On
    RequestHeader set X-API-Key "JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU="
    
    ProxyPass /api http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/
    ProxyPassReverse /api http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/
    
    ProxyPass /static !
    Alias /static /var/www/fibra
    <Directory /var/www/fibra>
        Require all granted
    </Directory>
    
    RewriteEngine On
    RewriteRule ^/$ /static/index.html [R=302,L]
    
    ProxyTimeout 120
    
    ErrorLog /var/log/apache2/fibra_error.log
    CustomLog /var/log/apache2/fibra_access.log combined
</VirtualHost>
```

### Firewall (nftables)

#### /etc/nftables/fibra.conf

```nftables
# Regola specifica per PC alex via Yggdrasil
iifname "ygg0" ip6 saddr 201:27c:546:5df7:176:95f3:c909:6834 tcp dport 6030 accept
```

### Systemd Services

#### Backend Service (/etc/systemd/system/ftth.service)

```ini
[Unit]
Description=FTTH Management Service
After=network.target

[Service]
Type=simple
User=aaa
Group=www-data
WorkingDirectory=/home/aaa/fibra
Environment=PATH=/home/aaa/fibra/venv/bin
ExecStart=/home/aaa/fibra/venv/bin/uvicorn app.main:app --host 200:421e:6385:4a8b:dca7:cfb:197f:e9c3 --port 6030 --workers 4 --proxy-headers
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

#### Telegram Bot Service (/etc/systemd/system/telegram-bot.service)

```ini
[Unit]
Description=FTTH Telegram Bot
After=network.target

[Service]
Type=simple
User=aaa
WorkingDirectory=/home/aaa/fibra
Environment=PATH=/home/aaa/fibra/venv/bin
ExecStart=/home/aaa/fibra/venv/bin/python app/bot.py
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

---

## 🔧 Utilizzo

### Avvio del Sistema

```bash
# 1. Backend
sudo systemctl start ftth

# 2. Bot Telegram
sudo systemctl start telegram-bot

# 3. Verifica
sudo systemctl status ftth telegram-bot
```

### Creazione Primo Lavoro

```bash
# Via API Yggdrasil
curl -X POST "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/manual/works" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" \
  -d '{
    "numero_wr": "TEST-001",
    "nome_cliente": "Mario Rossi",
    "indirizzo": "Via Roma 123, Milano",
    "operatore": "Tecnico A",
    "tipo_lavoro": "Installazione FTTH",
    "stato": "aperto"
  }'
```

### Assegnazione a Tecnico

```bash
# Lista tecnici
curl -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" \
  "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/technicians"

# Assegna lavoro
curl -X PUT "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works/1/assign/1" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU="
```

---

## 🔒 Sicurezza

### Livelli di Sicurezza Implementati

1. **Autenticazione API**: API keys crittografate con rotazione automatica
2. **Crittografia End-to-End**: Tutte le comunicazioni protette con TLS 1.3
3. **Network Isolation**: Yggdrasil garantisce isolamento dalla rete pubblica
4. **Rate Limiting**: Protezione contro attacchi DDoS e brute force
5. **Audit Logging**: Tracciamento completo di tutte le operazioni
6. **Backup Automatici**: Snapshots crittografati con versioning

### Configurazione Firewall

```bash
# Carica regole nftables
sudo nft -f /etc/nftables.conf

# Verifica regole
sudo nft list ruleset | grep 6030
```

### Monitoraggio Sicurezza

```bash
# Log fail2ban
sudo tail -f /var/log/fail2ban.log

# Log nftables
sudo journalctl -u nftables -f
```

---

## 🤖 Integrazione GPT

### Configurazione OpenAI

```env
OPENAI_API_KEY=sk-your-openai-api-key
GPT_MODEL=gpt-4
GPT_MAX_TOKENS=2000
```

### Utilizzo GPT

```bash
# Creazione lavoro da testo naturale
curl -X POST "https://servicess.net/gestionale/gpt/process" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "create_work_order",
    "description": "Installazione fibra ottica presso cliente Mario Rossi, Via Roma 123",
    "priority": "high"
  }'
```

### Funzionalità GPT Disponibili

- **Creazione Automatica Lavori**: Generazione ordini da descrizioni testuali
- **Assegnazione Intelligente**: Suggerimenti tecnici basati su competenza
- **Report Automatici**: Generazione documentazione tecnica
- **Assistenza Virtuale**: Chatbot integrato per supporto operativo
- **Analisi Predittiva**: Previsioni sui tempi di completamento basate su dati storici

---

## 📊 API Reference

### Endpoint Principali

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/works` | GET | Lista lavori |
| `/works` | POST | Crea nuovo lavoro |
| `/works/{id}` | PUT | Aggiorna lavoro |
| `/technicians` | GET | Lista tecnici |
| `/teams` | GET | Lista squadre |
| `/stats/yearly` | GET | Statistiche annuali |
| `/documents/upload` | POST | Carica PDF bolle |

### Autenticazione

Tutti gli endpoint amministrativi richiedono:

```bash
-H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU="
```

### Esempi Completi

#### Creazione Lavoro Manuale

```bash
curl -X POST "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/manual/works" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" \
  -d '{
    "numero_wr": "WR-12345",
    "data_inizio": "2025-12-21T10:00:00",
    "data_fine": "2025-12-21T12:00:00",
    "tipo": "70 - DELIVERY OF",
    "cliente": "ROSSI MARIO",
    "indirizzo": "VIA ROMA 123 MILANO",
    "stato": "ASSEGNATA",
    "telefono_cliente": "3331234567"
  }'
```

#### Upload Documento PDF

```bash
curl -X POST "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/documents/upload" \
  -H "X-API-Key: JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=" \
  -F "files=@bolla.pdf"
```

---

## 🧪 Testing

### Test Suite

```bash
# Esegui tutti i test
python -m pytest tests/ -v

# Test specifici
python -m pytest tests/test_api.py -v
python -m pytest tests/test_yggdrasil.py -v
```

### Test Manuali

#### Test Connettività Yggdrasil

```bash
# Ping backend via Yggdrasil
ping6 200:421e:6385:4a8b:dca7:cfb:197f:e9c3

# Test API via Yggdrasil
curl "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works"
```

#### Test Sicurezza

```bash
# Verifica che il backend non sia accessibile pubblicamente
curl "http://IP-PUBBLICO:6030/works"  # Dovrebbe fallire

# Test autenticazione
curl -H "X-API-Key: INVALID" "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works"
```

### Test di Carico

```bash
# Installa locust
pip install locust

# Avvia test di carico
locust -f tests/locustfile.py --host=http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030
```

---

## 🚀 Deployment

### Ambiente di Sviluppo

```bash
# Avvia tutto localmente
docker-compose up -d

# O manualmente
uvicorn app.main:app --host 127.0.0.1 --port 6030 --reload
```

### Ambiente di Produzione

#### Con Docker

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  ftth-backend:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/ftth
    networks:
      - yggdrasil
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=ftth
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - yggdrasil

networks:
  yggdrasil:
    driver: bridge
```

#### Con Kubernetes

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ftth-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ftth
  template:
    metadata:
      labels:
        app: ftth
    spec:
      containers:
      - name: ftth
        image: ftth:latest
        ports:
        - containerPort: 6030
        env:
        - name: DATABASE_URL
          value: "postgresql://user:pass@postgres:5432/ftth"
        - name: YGGDRASIL_ENABLED
          value: "true"
```

### Configurazione CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production
on:
  push:
    branches: [ main ]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Deploy to server
      run: |
        scp docker-compose.yml user@server:/opt/ftth/
        ssh user@server "cd /opt/ftth && docker-compose up -d --build"
```

---

## 📚 Documentazione

### Guide Disponibili

- [Guida Installazione](./docs/INSTALL.md)
- [API Yggdrasil](./YGGDRASIL_API_GUIDA.md)
- [Configurazione Sicurezza](./docs/SECURITY.md)
- [Troubleshooting](./docs/TROUBLESHOOTING.md)

### Architettura Dettagliata

```
Internet → Apache (443) → Yggdrasil → FastAPI (6030) → PostgreSQL
    ↓              ↓              ↓              ↓
 HTTPS     Proxy Pass     IPv6 Mesh     REST API     Database
```

### Flussi di Sicurezza

1. **Accesso Pubblico**: Solo HTTPS 443, certificato Let's Encrypt
2. **Proxy Sicuro**: Apache inietta X-API-Key automaticamente
3. **Isolamento Backend**: FastAPI ascolta solo su interfaccia Yggdrasil
4. **Autenticazione**: API Key richiesta per operazioni amministrative
5. **Crittografia**: Tutto il traffico protetto end-to-end

---

## 🤝 Contributi

### Come Contribuire

1. Fork il progetto
2. Crea un branch per la tua feature (`git checkout -b feature/AmazingFeature`)
3. Commit delle modifiche (`git commit -m 'Add some AmazingFeature'`)
4. Push del branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request

### Linee Guida per il Codice

- Segui PEP 8 per Python
- Aggiungi test per nuove funzionalità
- Aggiorna la documentazione
- Usa commit messages descrittivi

### Segnalazione Bug

Usa il template GitHub Issues per segnalare bug:

```markdown
**Descrivi il bug**
Una descrizione chiara del bug

**Riprodurre**
Passi per riprodurre:
1. Vai su '...'
2. Clicca su '....'
3. Scrolla giù a '....'
4. Vedi errore

**Comportamento atteso**
Una descrizione di cosa ti aspettavi

**Screenshots**
Se applicabile, aggiungi screenshots
```

---

## 📄 Licenza

Questo progetto è distribuito sotto licenza MIT. Vedi il file `LICENSE` per maggiori dettagli.

---

## 📞 Supporto

- **Email**: support@ftth-management.com
- **Telegram**: @FTTH_Support_Bot
- **Documentazione**: https://github.com/zinga0328it/fibra/wiki
- **Forum**: https://community.ftth-management.com

---

## 🎯 Roadmap

### ✅ Completato (Dicembre 2025)
- ✅ Architettura distribuita Yggdrasil
- ✅ Backend FastAPI con API RESTful
- ✅ Frontend responsive con Bootstrap
- ✅ Integrazione Telegram Bot
- ✅ Sicurezza multi-livello
- ✅ Database PostgreSQL con JSONB
- ✅ Integrazione GPT per automazione

### 🚧 In Sviluppo
- 🔄 Dashboard analytics avanzata
- 🔄 Mobile app nativa
- 🔄 Integrazione GIS per mappatura
- 🔄 Sistema di notifiche push
- 🔄 API GraphQL
- 🔄 Multi-tenancy per operatori

### 🔮 Pianificato
- 📅 Integrazione IoT per tracking
- 📅 AI predittiva per ottimizzazione
- 📅 Blockchain per audit trail
- 📅 Realtà aumentata per tecnici

---

*Sistema FTTH Management - Trasformiamo la gestione fibra in un'esperienza digitale eccezionale*