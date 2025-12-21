# Guida Installazione - Sistema FTTH Management

## Prerequisiti di Sistema

### Requisiti Minimi
- **CPU**: 2 core (4 core raccomandati)
- **RAM**: 4GB (8GB raccomandati)
- **Storage**: 20GB SSD
- **OS**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+

### Software Richiesto
- Python 3.9+
- PostgreSQL 13+ (o SQLite per test)
- Apache 2.4+ con mod_ssl
- Yggdrasil Network
- Git

## Installazione Automatica (Raccomandata)

### Script di Installazione

```bash
# Scarica lo script di installazione
wget https://raw.githubusercontent.com/zinga0328it/fibra/main/scripts/install.sh
chmod +x install.sh

# Esegui installazione
sudo ./install.sh
```

### Cosa fa lo script:
1. ✅ Installa dipendenze di sistema
2. ✅ Configura PostgreSQL
3. ✅ Installa Yggdrasil
4. ✅ Configura Apache con SSL
5. ✅ Crea servizi systemd
6. ✅ Configura firewall
7. ✅ Inizializza database

## Installazione Manuale

### 1. Preparazione Sistema

```bash
# Aggiorna sistema
sudo apt update && sudo apt upgrade -y

# Installa dipendenze di base
sudo apt install -y curl wget git python3 python3-pip postgresql apache2 certbot

# Installa Yggdrasil
sudo add-apt-repository ppa:neilalexander/yggdrasil
sudo apt update && sudo apt install -y yggdrasil
```

### 2. Configurazione Database

```bash
# Avvia PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Crea database e utente
sudo -u postgres psql -c "CREATE DATABASE ftth;"
sudo -u postgres psql -c "CREATE USER ftth_user WITH PASSWORD 'your_secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ftth TO ftth_user;"
```

### 3. Configurazione Yggdrasil

```bash
# Genera configurazione
sudo yggdrasil -genconf > /etc/yggdrasil.conf

# Modifica configurazione se necessario
sudo nano /etc/yggdrasil.conf

# Avvia servizio
sudo systemctl start yggdrasil
sudo systemctl enable yggdrasil

# Verifica indirizzo IPv6
ip addr show ygg0
```

### 4. Configurazione Apache

```bash
# Abilita moduli necessari
sudo a2enmod ssl proxy proxy_http rewrite headers

# Crea certificato SSL auto-firmato (per test)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/ssl-cert-snakeoil.key \
  -out /etc/ssl/certs/ssl-cert-snakeoil.pem

# Configura sito (vedi configurazione nel README principale)
sudo nano /etc/apache2/sites-available/fibra.conf
sudo a2ensite fibra.conf
sudo systemctl reload apache2
```

### 5. Installazione Applicazione

```bash
# Clona repository
git clone https://github.com/zinga0328it/fibra.git
cd fibra

# Crea ambiente virtuale
python3 -m venv venv
source venv/bin/activate

# Installa dipendenze
pip install -r requirements.txt

# Configura ambiente
cp .env.example .env
nano .env  # Modifica con le tue configurazioni
```

### 6. Inizializzazione Database

```bash
# Crea tabelle
python -c "from app.database import engine; from app.models import models; models.Base.metadata.create_all(bind=engine)"

# Crea utente amministratore (opzionale)
python scripts/create_admin.py
```

### 7. Configurazione Servizi Systemd

```bash
# Copia file servizio
sudo cp deploy/systemd/ftth.service /etc/systemd/system/
sudo cp deploy/systemd/telegram-bot.service /etc/systemd/system/

# Ricarica systemd
sudo systemctl daemon-reload

# Abilita e avvia servizi
sudo systemctl enable ftth telegram-bot
sudo systemctl start ftth telegram-bot
```

### 8. Configurazione Firewall

```bash
# Installa nftables se non presente
sudo apt install -y nftables

# Copia configurazione
sudo cp deploy/nftables/fibra.conf /etc/nftables/

# Applica regole
sudo systemctl restart nftables
```

## Verifica Installazione

### Test Backend
```bash
# Verifica servizio attivo
sudo systemctl status ftth

# Test API locale
curl "http://localhost:6030/health"
```

### Test Yggdrasil
```bash
# Ping indirizzo backend
ping6 200:421e:6385:4a8b:dca7:cfb:197f:e9c3

# Test API via Yggdrasil
curl "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works"
```

### Test Frontend
```bash
# Test HTTPS
curl -I https://your-domain.com/fibra/

# Verifica che reindirizza correttamente
curl -L https://your-domain.com/fibra/
```

## Risoluzione Problemi

### Servizio non si avvia
```bash
# Controlla log
sudo journalctl -u ftth -f

# Verifica configurazione
sudo systemctl cat ftth
```

### Database connection error
```bash
# Verifica connessione PostgreSQL
sudo -u postgres psql -d ftth -c "SELECT version();"

# Controlla variabili ambiente
cat .env | grep DATABASE_URL
```

### Yggdrasil non connesso
```bash
# Verifica stato
sudo systemctl status yggdrasil

# Controlla log
sudo journalctl -u yggdrasil -f

# Test connettività
ping6 200:421e:6385:4a8b:dca7:cfb:197f:e9c3
```

## Configurazione Produzione

### SSL con Let's Encrypt
```bash
# Ottieni certificato
sudo certbot --apache -d your-domain.com

# Rinnovo automatico già configurato
sudo systemctl status certbot.timer
```

### Backup Automatico
```bash
# Script di backup
sudo cp deploy/scripts/backup.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/backup.sh

# Aggiungi a cron
echo "0 2 * * * /usr/local/bin/backup.sh" | sudo crontab -
```

### Monitoraggio
```bash
# Installa monitoring
sudo apt install -y prometheus-node-exporter

# Configura alert manager per servizi critici
sudo nano /etc/prometheus/alert_rules.yml
```

## Aggiornamenti

### Aggiornamento Automatico
```bash
# Script di update
cd /opt/ftth
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Riavvia servizi
sudo systemctl restart ftth telegram-bot
```

### Rollback
```bash
# Se qualcosa va storto
git checkout <previous_commit>
sudo systemctl restart ftth telegram-bot
```

## Supporto

Per problemi di installazione:
- 📧 support@ftth-management.com
- 📱 Telegram: @FTTH_Support_Bot
- 📖 [Documentazione Completa](https://github.com/zinga0328it/fibra/wiki)