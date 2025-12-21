# Troubleshooting - Sistema FTTH Management

## Problemi Comuni e Soluzioni

### 🔴 Backend Non Si Avvia

#### Sintomo
```bash
sudo systemctl status ftth
# Active: failed (Result: exit-code)
```

#### Possibili Cause e Soluzioni

**1. Porta già in uso**
```bash
# Verifica cosa usa la porta 6030
sudo ss -lntp | grep :6030

# Kill processi orfani
sudo kill -9 $(sudo lsof -t -i:6030)

# Riavvia servizio
sudo systemctl restart ftth
```

**2. Errore database**
```bash
# Verifica connessione
python -c "from app.database import engine; print('Connessione OK' if engine else 'Errore')"

# Controlla DATABASE_URL
cat .env | grep DATABASE_URL

# Per PostgreSQL
sudo -u postgres psql -d ftth -c "SELECT 1;"
```

**3. Dipendenze mancanti**
```bash
# Riinstalla dipendenze
source venv/bin/activate
pip install -r requirements.txt --force-reinstall

# Verifica Python path
which python
python --version
```

#### Log di Debug
```bash
# Vedi log servizio
sudo journalctl -u ftth -f -n 50

# Log applicazione
tail -f logs/ftth.log
```

### 🔴 Yggdrasil Non Connette

#### Sintomo
```bash
ping6 200:421e:6385:4a8b:dca7:cfb:197f:e9c3
# No response
```

#### Soluzioni

**1. Servizio Yggdrasil non attivo**
```bash
sudo systemctl status yggdrasil
sudo systemctl restart yggdrasil
```

**2. Configurazione errata**
```bash
# Verifica configurazione
sudo cat /etc/yggdrasil.conf | grep -A5 -B5 "Listen\|Peers"

# Rigenera configurazione
sudo yggdrasil -genconf > /tmp/yggdrasil.conf
sudo cp /tmp/yggdrasil.conf /etc/yggdrasil.conf
sudo systemctl restart yggdrasil
```

**3. Firewall blocca**
```bash
# Verifica regole nftables
sudo nft list ruleset | grep ygg

# Aggiungi regola se mancante
sudo nft add rule inet filter input iifname "ygg0" accept
```

**4. Indirizzo IP cambiato**
```bash
# Controlla indirizzo attuale
ip addr show ygg0

# Aggiorna configurazione se necessario
sudo nano /etc/nftables/fibra.conf
sudo systemctl restart nftables
```

### 🔴 API Non Risponde

#### Sintomo
```bash
curl "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/works"
# Connection refused o timeout
```

#### Soluzioni

**1. Backend non ascolta su Yggdrasil**
```bash
# Verifica dove ascolta FastAPI
ss -lntp | grep :6030

# Se ascolta su 127.0.0.1, modifica servizio
sudo nano /etc/systemd/system/ftth.service
# Cambia: --host 127.0.0.1 → --host 200:421e:6385:4a8b:dca7:cfb:197f:e9c3
sudo systemctl daemon-reload
sudo systemctl restart ftth
```

**2. Firewall blocca traffico Yggdrasil**
```bash
# Verifica regole
sudo nft list ruleset | grep 6030

# Aggiungi regola mancante
echo 'iifname "ygg0" ip6 saddr 201:27c:546:5df7:176:95f3:c909:6834 tcp dport 6030 accept' | sudo tee -a /etc/nftables/fibra.conf
sudo systemctl restart nftables
```

**3. Yggdrasil non instrada correttamente**
```bash
# Test connettività base
ping6 200:421e:6385:4a8b:dca7:cfb:197f:e9c3

# Verifica tabella routing
ip -6 route show | grep ygg
```

### 🔴 Frontend Non Carica

#### Sintomo
```bash
curl -I https://servicess.net/fibra/
# 404 Not Found o 502 Bad Gateway
```

#### Soluzioni

**1. Apache non proxy correttamente**
```bash
# Verifica configurazione
sudo cat /etc/apache2/sites-available/fibra.conf

# Test proxy manualmente
curl "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030/"

# Reload Apache
sudo systemctl reload apache2
```

**2. Certificato SSL scaduto**
```bash
# Verifica certificato
openssl s_client -connect servicess.net:443 -servername servicess.net < /dev/null 2>/dev/null | openssl x509 -noout -dates

# Rinnova con certbot
sudo certbot renew
```

**3. Permessi file statici**
```bash
# Verifica permessi
ls -la /var/www/fibra/
sudo chown -R www-data:www-data /var/www/fibra/
```

### 🔴 Database Error

#### Sintomo
```
sqlalchemy.exc.OperationalError: connection failed
```

#### Soluzioni

**1. PostgreSQL non attivo**
```bash
sudo systemctl status postgresql
sudo systemctl restart postgresql
```

**2. Credenziali errate**
```bash
# Test connessione
psql "postgresql://ftth_user:password@localhost/ftth" -c "SELECT 1;"

# Verifica .env
cat .env | grep DATABASE_URL
```

**3. Database corrotto**
```bash
# Per SQLite
rm ftth.db
python -c "from app.database import engine; from app.models import models; models.Base.metadata.create_all(bind=engine)"
```

### 🔴 Telegram Bot Non Funziona

#### Sintomo
Bot non risponde ai comandi

#### Soluzioni

**1. Token errato**
```bash
# Test token
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"
```

**2. Webhook vs Polling conflitto**
```bash
# Disabilita polling se usi webhook
export TELEGRAM_POLLING=false
sudo systemctl restart telegram-bot
```

**3. Permessi bot insufficienti**
```bash
# Verifica comandi bot
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMyCommands"

# Imposta comandi
python scripts/set_bot_commands.py
```

### 🔴 Performance Lente

#### Sintomo
API risponde lentamente (>2 secondi)

#### Soluzioni

**1. Database non ottimizzato**
```bash
# Aggiungi indici
sudo -u postgres psql -d ftth -c "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_works_status ON works(status);"
sudo -u postgres psql -d ftth -c "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_works_created ON works(created_at);"
```

**2. Troppi workers**
```bash
# Riduci workers in produzione
sudo nano /etc/systemd/system/ftth.service
# Cambia: --workers 4 → --workers 2
sudo systemctl daemon-reload
sudo systemctl restart ftth
```

**3. Memoria insufficiente**
```bash
# Monitora risorse
htop
free -h

# Aumenta swap se necessario
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 🔴 Backup Fallito

#### Sintomo
```bash
# Log backup contiene errori
tail -f /var/log/ftth/backup.log
```

#### Soluzioni

**1. Permessi directory backup**
```bash
sudo mkdir -p /opt/ftth/backups
sudo chown ftth:ftth /opt/ftth/backups
sudo chmod 755 /opt/ftth/backups
```

**2. Spazio disco insufficiente**
```bash
df -h
# Libera spazio o cambia directory backup
```

**3. Database lock**
```bash
# Per PostgreSQL
sudo -u postgres psql -d ftth -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

### 🔴 Log Errori Comuni

#### "Address already in use"
```bash
# Trova processo
sudo lsof -i :6030
sudo kill -9 <PID>
```

#### "Permission denied"
```bash
# Verifica permessi
ls -la logs/
sudo chown ftth:www-data logs/
sudo chmod 755 logs/
```

#### "Module not found"
```bash
# Riinstalla ambiente virtuale
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 🆘 Contatto Supporto

Se nessuna soluzione funziona:

1. **Raccogli informazioni di sistema**
```bash
# Informazioni sistema
uname -a
lsb_release -a

# Versioni software
python --version
psql --version
apache2 -v

# Stato servizi
sudo systemctl status ftth postgresql apache2 yggdrasil
```

2. **Log completi**
```bash
# Crea archive log
sudo tar -czf logs_$(date +%Y%m%d_%H%M%S).tar.gz logs/ /var/log/apache2/ /var/log/postgresql/
```

3. **Contatta supporto**
- 📧 support@ftth-management.com
- 📱 Telegram: @FTTH_Support_Bot
- 📋 Includi: logs, configurazione, errori

## 🚨 Procedure di Emergenza

### Rollback Completo
```bash
# Stop servizi
sudo systemctl stop ftth telegram-bot apache2

# Ripristina backup
sudo cp /etc/systemd/system/ftth.service.backup_* /etc/systemd/system/ftth.service
sudo cp /etc/apache2/sites-available/fibra.conf.backup_* /etc/apache2/sites-available/fibra.conf
sudo cp /etc/nftables/fibra.conf.backup_* /etc/nftables/fibra.conf

# Restart
sudo systemctl daemon-reload
sudo systemctl restart postgresql apache2 nftables
sudo systemctl start ftth telegram-bot
```

### Recovery Database
```bash
# Stop applicazione
sudo systemctl stop ftth

# Restore da backup
sudo -u postgres pg_restore -d ftth /path/to/backup.dump

# Verifica integrità
sudo -u postgres psql -d ftth -c "SELECT COUNT(*) FROM works;"

# Restart
sudo systemctl start ftth
```