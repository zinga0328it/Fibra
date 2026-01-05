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
```

### Sintomo: "Porta 6030 già in uso"
**Canvas**: [[FTTH-Backend-Module.canvas#troubleshooting_backend|Troubleshooting Backend]]
```
Comandi:
sudo ss -lntp | grep :6030
sudo kill -9 $(sudo lsof -t -i:6030)
sudo systemctl restart ftth
```

### Sintomo: "Errore database connection"
**Canvas**: [[FTTH-Database-Module.canvas#postgresql_config|Database Config]]
```
Verifica: cat .env | grep DATABASE_URL
Test: psql "$DATABASE_URL" -c "SELECT 1;"
Soluzione: sudo systemctl restart postgresql
```

---

## 🕸️ Problemi Yggdrasil Network

### Sintomo: "Impossibile raggiungere backend"
**Canvas**: [[FTTH-Yggdrasil-Module.canvas#connectivity_test|Connectivity Test]]
```
Test: ping6 200:421e:6385:4a8b:dca7:cfb:197f:e9c3
Verifica: ip addr show ygg0
Restart: sudo systemctl restart yggdrasil
```

### Sintomo: "Yggdrasil non si connette"
**Canvas**: [[FTTH-Yggdrasil-Module.canvas#yggdrasil_config|Yggdrasil Config]]
```
Status: sudo systemctl status yggdrasil
Config: sudo cat /etc/yggdrasil.conf
Regenerate: yggdrasil -genconf > /etc/yggdrasil.conf
```

### Sintomo: "Firewall blocca Yggdrasil"
**Canvas**: [[FTTH-Security-Module.canvas#nftables_config|Firewall Rules]]
```
Verifica: sudo nft list ruleset | grep ygg
Aggiungi: sudo nft add rule inet filter input iifname "ygg0" accept
Reload: sudo systemctl restart nftables
```

---

## 🌐 Problemi Apache Frontend

### Sintomo: "Sito web non carica"
**Canvas**: [[FTTH-Apache-Module.canvas#apache_config|Apache Config]]
```
Test: curl -I https://servicess.net/fibra/
Status: sudo systemctl status apache2
Log: sudo tail -f /var/log/apache2/error.log
```

### Sintomo: "Certificato SSL scaduto"
**Canvas**: [[FTTH-Apache-Module.canvas#ssl_certificates|SSL Certificates]]
```
Verifica: openssl s_client -connect servicess.net:443
Rinnova: sudo certbot renew
Reload: sudo systemctl reload apache2
```

### Sintomo: "502 Bad Gateway" (Non dovrebbe succedere!)
**Canvas**: [[FTTH-Apache-Module.canvas#security_measures|Security Measures]]
```
Questo errore indica tentativo di proxy al backend!
Verifica config: sudo cat /etc/apache2/sites-available/fibra.conf
Rimuovi proxy pass se presente!
```

---

## 🗄️ Problemi Database

### Sintomo: "PostgreSQL non si avvia"
**Canvas**: [[FTTH-Database-Module.canvas#postgresql_config|PostgreSQL Setup]]
```
Status: sudo systemctl status postgresql
Log: sudo tail -f /var/log/postgresql/postgresql-*.log
Start: sudo systemctl start postgresql
```

### Sintomo: "Connessione rifiutata"
**Canvas**: [[FTTH-Database-Module.canvas#troubleshooting_db|Troubleshooting DB]]
```
Test: psql "postgresql://user:pass@localhost/ftth" -c "SELECT 1;"
Verifica: cat .env | grep DATABASE_URL
Permessi: sudo -u postgres psql -c "GRANT ALL ON DATABASE ftth TO ftth_user;"
```

### Sintomo: "Database SQLite corrotto"
**Canvas**: [[FTTH-Database-Module.canvas#sqlite_config|SQLite Config]]
```
Backup: cp ftth.db ftth_backup.db
Ricrea: rm ftth.db && python -c "from app.database import engine; from app.models import models; models.Base.metadata.create_all(bind=engine)"
Restore: cp ftth_backup.db ftth.db
```

---

## 📱 Problemi Telegram Bot

### Sintomo: "Bot non risponde"
**Canvas**: [[FTTH-Telegram-Module.canvas#bot_configuration|Bot Configuration]]
```
Test token: curl "https://api.telegram.org/bot$TOKEN/getMe"
Status: sudo systemctl status telegram-bot
Log: sudo journalctl -u telegram-bot -f
```

### Sintomo: "Notifiche non arrivano"
**Canvas**: [[FTTH-Telegram-Module.canvas#notification_system|Notification System]]
```
Verifica polling: cat .env | grep TELEGRAM_POLLING
Test manuale: python telegram_bot.py (temporaneo)
Webhook: curl "https://api.telegram.org/bot$TOKEN/getWebhookInfo"
```

### Sintomo: "Comandi non funzionano"
**Canvas**: [[FTTH-Telegram-Module.canvas#systemd_service|Systemd Service]]
```
Set commands: python scripts/set_bot_commands.py
Restart: sudo systemctl restart telegram-bot
Test: Invia /start al bot
```

---

## 🔐 Problemi Sicurezza

### Sintomo: "Accesso negato al backend"
**Canvas**: [[FTTH-Security-Module.canvas#access_control|Access Control]]
```
Verifica IP: Solo 201:27c:546:5df7:176:95f3:c909:6834 può accedere
Test da PC alex: curl "http://[backend-ip]:6030/works"
Firewall: sudo nft list ruleset | grep 6030
```

### Sintomo: "Fail2Ban blocca indirizzi legittimi"
**Canvas**: [[FTTH-Security-Module.canvas#fail2ban_integration|Fail2Ban Integration]]
```
Status: sudo fail2ban-client status
Unban: sudo fail2ban-client set apache-noscript unbanip IP
Log: sudo tail -f /var/log/fail2ban.log
```

### Sintomo: "Regole firewall non applicate"
**Canvas**: [[FTTH-Security-Module.canvas#nftables_config|NFTables Config]]
```
Verifica: sudo nft list ruleset
Ricarica: sudo systemctl restart nftables
Persistente: sudo nft list ruleset > /etc/nftables/fibra.conf
```

---

## 📊 Problemi Monitoraggio

### Sintomo: "Log non vengono scritti"
**Canvas**: [[FTTH-Monitoring-Module.canvas#logging_system|Logging System]]
```
Permessi: sudo chown ftth:www-data logs/
Dimensione: ls -lh logs/ftth.log
Rotazione: Verifica logrotate config
```

### Sintomo: "Servizi cadono senza avviso"
**Canvas**: [[FTTH-Monitoring-Module.canvas#alert_system|Alert System]]
```
Systemd: sudo systemctl status --failed
Journal: sudo journalctl --failed
Monitoring: Verifica script di health check
```

### Sintomo: "Performance lente"
**Canvas**: [[FTTH-Monitoring-Module.canvas#performance_metrics|Performance Metrics]]
```
CPU: top -p $(pgrep ftth)
Memory: free -h
Disk: iotop
Database: Verifica query lente
```

---

## 🚨 Procedure di Emergenza

### Sistema Completamente Giù
**Canvas**: [[FTTH-Index.canvas#troubleshooting|Troubleshooting Index]]
```
1. Verifica hardware: uptime, free -h, df -h
2. Check servizi: sudo systemctl --failed
3. Vedi log recenti: sudo journalctl --since "1 hour ago"
4. Restart selettivo: sudo systemctl restart ftth
5. Recovery completo se necessario
```

### Data Breach Sospetto
**Canvas**: [[FTTH-Security-Module.canvas#zero_trust_principles|Zero Trust Principles]]
```
1. Isola sistema: Disconnetti internet
2. Analizza log: grep "suspicious" logs/*.log
3. Cambia credenziali: Tutti i token e password
4. Aggiorna regole firewall
5. Report incidente
```

### Perdita Dati
**Canvas**: [[FTTH-Database-Module.canvas#backup_system|Backup System]]
```
1. Stop servizi: sudo systemctl stop ftth
2. Identifica perdita: Confronta con backup
3. Restore: psql ftth < backup.sql
4. Verifica integrità: Test funzionalità
5. Restart servizi
```

---

## 📞 Contatto Supporto

Quando tutto fallisce:

1. **Raccogli info**: `uname -a`, versioni software, status servizi
2. **Archivia log**: `tar -czf logs_$(date +%Y%m%d).tar.gz logs/`
3. **Contatta**: pepeAlessandro@proton.me
4. **Includi**: Sintomi, azioni tentate, log rilevanti

---

*Questa guida è viva e cresce con il sistema. Ogni nuovo problema risolto aggiunge una sezione!*