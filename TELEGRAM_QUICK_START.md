# 📱 Quick Start: Telegram per Tecnici

## In 3 Passi

### 1️⃣ Ottieni il Telegram ID

Il tecnico deve:
1. Aprire Telegram
2. Cercare: **@userinfobot**
3. Inviare: `/start`
4. Copiare l'**ID numerico** (es: 123456789)

### 2️⃣ Aggiungi/Aggiorna il Tecnico

**Nuovo tecnico:**
```bash
python add_technician_telegram.py
```

**Tecnico esistente (solo aggiornare Telegram ID):**
```bash
python update_technician_telegram.py
```

### 3️⃣ Il Tecnico Usa il Bot

Il tecnico deve:
1. Cercare il bot su Telegram (vedi nome con: `python get_bot_info.py`)
2. Inviare `/start`
3. Usare i comandi:
   - `/miei_lavori` - Vedi lavori assegnati
   - `/accetta WR123` - Accetta lavoro
   - `/rifiuta WR123` - Rifiuta lavoro  
   - `/chiudi WR123` - Chiudi lavoro completato

## ✅ Test

```bash
# Verifica bot attivo
ps aux | grep bot

# Test notifica
python test_bot.py
```

## 📚 Comandi Bot

| Comando | Descrizione |
|---------|-------------|
| `/start` | Avvia bot e mostra menu |
| `/help` | Lista comandi |
| `/miei_lavori` | Mostra lavori assegnati |
| `/accetta <WR>` | Accetta lavoro |
| `/rifiuta <WR>` | Rifiuta lavoro |
| `/chiudi <WR>` | Chiude lavoro |

## 🔧 Troubleshooting

**Bot non risponde?**
```bash
sudo systemctl restart ftth-telegram-bot
journalctl -u ftth-telegram-bot -f
```

**Tecnico non riceve notifiche?**
- Verifica Telegram ID corretto
- Il tecnico deve aver inviato `/start` al bot
- Controlla che il bot sia in esecuzione

## �� Documentazione Completa

Vedi: `TELEGRAM_SETUP.md`
