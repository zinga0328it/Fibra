# 📱 Guida: Aggiungere Tecnici con Telegram

## Panoramica
Il sistema permette ai tecnici di ricevere notifiche e gestire lavori tramite Telegram Bot.

---

## 🔧 METODO 1: Script Automatico (Consigliato)

### 1. Ottieni il Telegram ID del tecnico

**Opzione A - Usando @userinfobot:**
```
1. Il tecnico apre Telegram
2. Cerca: @userinfobot
3. Invia: /start
4. Il bot risponde con l'ID (es: 123456789)
```

**Opzione B - Usando il nostro bot:**
```bash
# 1. Il tecnico cerca il tuo bot su Telegram (vedi nome con get_bot_info.py)
# 2. Il tecnico invia /start al bot
# 3. Esegui questo comando per vedere chi ha scritto:
python scripts/get_bot_updates.py
```

### 2. Aggiungi il tecnico con lo script

```bash
python add_technician_telegram.py
```

Lo script ti chiederà:
- Nome e Cognome
- Telefono
- Squadra (mostra lista automaticamente)
- Telegram ID (opzionale)

✅ **Fatto!** Il tecnico può ora usare il bot.

---

## 🌐 METODO 2: Via Interfaccia Web

### 1. Apri il gestionale
```
http://localhost:6030/static/gestionale.html
```

### 2. Vai alla sezione "Tecnici"

### 3. Clicca "Aggiungi Tecnico"

### 4. Compila il form:
- Nome
- Cognome  
- Telefono
- Squadra
- **Telegram ID** (opzionale - vedi come ottenerlo sopra)

### 5. Salva

---

## 🔄 METODO 3: Via API (per sviluppatori)

### Endpoint
```
POST /technicians/
```

### Payload
```json
{
  "nome": "Mario",
  "cognome": "Rossi",
  "telefono": "333 1234567",
  "squadra_id": 1,
  "telegram_id": "123456789"
}
```

### Esempio curl
```bash
curl -X POST http://localhost:6030/technicians/ \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Mario",
    "cognome": "Rossi", 
    "telefono": "333 1234567",
    "squadra_id": 1,
    "telegram_id": "123456789"
  }'
```

---

## 📋 Comandi Bot Telegram Disponibili

Una volta aggiunto il Telegram ID, il tecnico può usare:

### Comandi Base
- `/start` - Avvia il bot e mostra menu
- `/help` - Mostra lista comandi

### Gestione Lavori
- `/miei_lavori` - Mostra tutti i lavori assegnati
- `/accetta <WR>` - Accetta un lavoro (es: `/accetta 15699897`)
- `/rifiuta <WR>` - Rifiuta un lavoro
- `/chiudi <WR>` - Chiude un lavoro completato

---

## 🔔 Test Notifiche

Per testare se il tecnico riceve notifiche:

### Via Web
1. Apri gestionale
2. Crea/modifica un lavoro
3. Assegna al tecnico
4. Spunta "Notifica Telegram"
5. Salva

### Via API
```bash
# Notifica per lavoro specifico
curl -X POST http://localhost:6030/works/{work_id}/notify \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## ❗ Risoluzione Problemi

### Il tecnico non riceve notifiche

1. **Verifica che il Telegram ID sia corretto:**
   ```bash
   python scripts/get_bot_updates.py
   ```

2. **Verifica che il bot sia avviato:**
   ```bash
   ps aux | grep "python.*app.bot"
   ```

3. **Controlla i log:**
   ```bash
   journalctl -u ftth-telegram-bot -f
   ```

4. **Test manuale:**
   ```bash
   python test_bot.py
   ```

### Il bot non risponde ai comandi

1. **Verifica che il webhook sia configurato** (se usi webhook invece di polling)
2. **Controlla il TOKEN** nel file `.env`
3. **Riavvia il bot:**
   ```bash
   sudo systemctl restart ftth-telegram-bot
   ```

### Tecnico non trovato con /miei_lavori

- Verifica che il `telegram_id` nel database corrisponda esattamente all'ID Telegram del tecnico
- Usa `@userinfobot` per confermare l'ID corretto

---

## 🔐 Note Sicurezza

- Il Telegram ID è un numero univoco e non cambia mai
- Non condividere il `TELEGRAM_BOT_TOKEN` pubblicamente
- Solo tecnici con `telegram_id` registrato possono usare i comandi del bot
- Le notifiche vengono inviate solo se il tecnico ha un `telegram_id` valido

---

## 📚 Script Utili

| Script | Scopo |
|--------|-------|
| `get_bot_info.py` | Info sul bot (nome, username, ID) |
| `scripts/get_bot_updates.py` | Vedi chi ha scritto al bot |
| `add_technician_telegram.py` | Aggiungi tecnico interattivamente |
| `test_bot.py` | Test notifiche Telegram |

---

## 🎯 Riepilogo Rapido

```bash
# 1. Il tecnico ottiene il suo ID
# Opzione 1: Cerca @userinfobot su Telegram
# Opzione 2: Scrive al tuo bot, poi esegui:
python scripts/get_bot_updates.py

# 2. Aggiungi il tecnico
python add_technician_telegram.py

# 3. Test notifica
python test_bot.py

# ✅ Fatto!
```
