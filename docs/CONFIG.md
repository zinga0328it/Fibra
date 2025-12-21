# Configurazione Ambiente - Sistema FTTH Management

## File .env.example

Copia questo file in `.env` e modifica i valori secondo le tue esigenze.

```env
# =============================================================================
# CONFIGURAZIONE AMBIENTE - SISTEMA FTTH MANAGEMENT
# =============================================================================

# Database Configuration
# SQLite (sviluppo): sqlite:///./ftth.db
# PostgreSQL (produzione): postgresql://user:password@localhost:5432/ftth
DATABASE_URL=sqlite:///./ftth.db

# Sicurezza
SECRET_KEY=your-super-secret-key-change-this-in-production
API_KEY=JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU=

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here
TELEGRAM_WEBHOOK_URL=https://your-domain.com/telegram/webhook
TELEGRAM_POLLING=false

# Yggdrasil Network Configuration
YGGDRASIL_API_KEY=ftth_ygg_secret_2025
YGGDRASIL_BACKEND_IP=200:421e:6385:4a8b:dca7:cfb:197f:e9c3
YGGDRASIL_CLIENT_IP=201:27c:546:5df7:176:95f3:c909:6834

# OpenAI GPT Configuration (Opzionale)
OPENAI_API_KEY=sk-your-openai-api-key
GPT_MODEL=gpt-4
GPT_MAX_TOKENS=2000
GPT_TEMPERATURE=0.7

# Server Configuration
HOST=200:421e:6385:4a8b:dca7:cfb:197f:e9c3
PORT=6030
WORKERS=4
RELOAD=false

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/ftth.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5

# Frontend Configuration
FRONTEND_URL=https://servicess.net/fibra/
STATIC_FILES_DIR=web/publica

# Email Configuration (Opzionale)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@ftth-management.com

# Backup Configuration
BACKUP_DIR=/opt/ftth/backups
BACKUP_RETENTION_DAYS=30
BACKUP_SCHEDULE=0 2 * * *

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=30

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Cache Configuration
CACHE_TYPE=redis
CACHE_URL=redis://localhost:6379/0
CACHE_TTL=3600

# OCR Configuration (per parsing PDF)
OCR_ENABLED=true
OCR_LANGUAGE=ita+eng
OCR_DPI=300

# GIS Configuration (per mappatura)
GIS_ENABLED=true
GIS_PROVIDER=openstreetmap
GIS_API_KEY=your-gis-api-key

# Notification Settings
NOTIFICATION_TELEGRAM=true
NOTIFICATION_EMAIL=false
NOTIFICATION_WEBHOOK=false

# Debug (solo sviluppo)
DEBUG=false
TESTING=false
```

## Configurazioni Specifiche per Ambiente

### Ambiente di Sviluppo

```env
DEBUG=true
DATABASE_URL=sqlite:///./ftth_dev.db
RELOAD=true
LOG_LEVEL=DEBUG
TELEGRAM_POLLING=true
```

### Ambiente di Produzione

```env
DEBUG=false
DATABASE_URL=postgresql://ftth_user:secure_password@localhost:5432/ftth
RELOAD=false
LOG_LEVEL=WARNING
TELEGRAM_POLLING=false
BACKUP_ENABLED=true
SSL_REDIRECT=true
```

### Ambiente di Test

```env
TESTING=true
DATABASE_URL=sqlite:///./ftth_test.db
LOG_LEVEL=DEBUG
TELEGRAM_POLLING=false
```

## Variabili Critiche

### Obbligatorie
- `DATABASE_URL`: URL completa del database
- `SECRET_KEY`: Chiave segreta per JWT (cambiala in produzione!)
- `API_KEY`: Chiave API per autenticazione amministrativa
- `TELEGRAM_BOT_TOKEN`: Token del bot Telegram

### Raccomandate
- `YGGDRASIL_API_KEY`: Chiave per API Yggdrasil
- `OPENAI_API_KEY`: Chiave OpenAI per funzionalità GPT
- `TELEGRAM_WEBHOOK_URL`: URL webhook per produzione

### Opzionali
- `SMTP_*`: Configurazione email
- `BACKUP_*`: Configurazione backup
- `CACHE_*`: Configurazione cache Redis
- `GIS_*`: Configurazione mappe

## Sicurezza

### Chiavi Segrete
- Genera `SECRET_KEY` con: `openssl rand -hex 32`
- Usa password complesse per database
- Ruota regolarmente le API keys
- Non committare mai il file `.env` reale

### Rete
- In produzione usa solo HTTPS
- Configura firewall per permettere solo porte necessarie
- Usa VPN (Yggdrasil) per comunicazioni backend
- Implementa rate limiting

## Esempi di Configurazione

### Configurazione Minima (Sviluppo)

```env
DATABASE_URL=sqlite:///./ftth.db
SECRET_KEY=dev-secret-key-12345
API_KEY=test-api-key
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### Configurazione Completa (Produzione)

```env
DATABASE_URL=postgresql://ftth_prod:SuperSecurePass2025@localhost:5432/ftth_prod
SECRET_KEY=4f8d9c2e5a7b3f6e8d4c9a1b5e7f2d8c4a6b9e1f3d7c5a8b2e4f6d9c1a3b5e7f
API_KEY=ProdApiKey_2025_Secure_Random_Generated
TELEGRAM_BOT_TOKEN=987654321:ZYXwvuTSRQpOnMLKjIhGfEdCbA
TELEGRAM_WEBHOOK_URL=https://api.ftth-management.com/telegram/webhook
YGGDRASIL_API_KEY=prod_ygg_key_2025_secure
OPENAI_API_KEY=sk-prod-1234567890abcdef
SMTP_SERVER=smtp.company.com
SMTP_PORT=587
SMTP_USERNAME=ftth@company.com
SMTP_PASSWORD=SecureEmailPass2025
BACKUP_DIR=/secure/backups/ftth
BACKUP_RETENTION_DAYS=90
SSL_REDIRECT=true
```

## Troubleshooting

### Database Connection Error
```bash
# Verifica DATABASE_URL
echo $DATABASE_URL

# Test connessione PostgreSQL
psql "$DATABASE_URL" -c "SELECT 1;"

# Per SQLite
ls -la ftth.db
```

### Telegram Bot Error
```bash
# Verifica token
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"

# Controlla webhook
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo"
```

### Yggdrasil Connection Error
```bash
# Verifica indirizzo IP
ip addr show ygg0

# Test ping
ping6 $YGGDRASIL_BACKEND_IP

# Controlla configurazione
cat /etc/yggdrasil.conf | grep Listen
```

## Migrazioni Database

Quando aggiorni il modello dati:

```bash
# Crea migrazione
alembic revision --autogenerate -m "Descrizione modifica"

# Applica migrazione
alembic upgrade head

# Verifica
python -c "from app.database import engine; from app.models import models; models.Base.metadata.create_all(bind=engine)"
```