# 🤖 Guida Test Bot Telegram FTTH

## 📱 Bot: @Flowers007bot

## ✅ Test Rapidi

### 1️⃣ Verifica Bot Attivo
```bash
sudo systemctl status ftth_bot.service
```
**Risultato atteso:** `Active: active (running)`

---

### 2️⃣ Ottieni Info Bot
```bash
cd /home/aaa/fibra
source venv/bin/activate
python get_bot_info.py
```

---

### 3️⃣ Testa Bot su Telegram

**Sul tuo telefono:**
1. Apri Telegram
2. Cerca: `@Flowers007bot`
3. Invia: `/start`
   - ✅ Dovresti ricevere "Benvenuto nel bot FTTH!" con tastiera comandi
4. Invia: `/help`
   - ✅ Dovresti ricevere lista comandi disponibili
5. Invia: `/miei_lavori`
   - ⚠️ Se non sei nel database: "Tecnico non trovato. Contatta l'admin."
   - ✅ Se sei nel database: Lista dei tuoi lavori

---

### 4️⃣ Ottieni il TUO Telegram ID

**Dopo aver inviato /start al bot:**

```bash
cd /home/aaa/fibra
source venv/bin/activate
python get_bot_updates.py
```

**Output esempio:**
```
👤 Utente:
   Nome: Mario Rossi
   Username: @mariorossi
   🎯 TELEGRAM ID: 123456789

💬 Messaggio: /start
```

Copia il **TELEGRAM ID** (es: 123456789)

---

### 5️⃣ Aggiungi Telegram ID al Database

**Aggiorna un tecnico esistente:**

```bash
sqlite3 /home/aaa/fibra/ftth.db "UPDATE technicians SET telegram_id = '123456789' WHERE id = 1;"
```

Sostituisci:
- `123456789` con il TUO telegram ID
- `1` con l'ID del tecnico nel database

**Verifica:**
```bash
sqlite3 /home/aaa/fibra/ftth.db "SELECT id, nome, cognome, telegram_id FROM technicians;"
```

---

### 6️⃣ Test Completo con Script

```bash
cd /home/aaa/fibra
source venv/bin/activate
python test_bot.py
```

**Risultato atteso:**
```
✅ Token trovato
✅ Connessione database OK
✅ Tecnico selezionato per test: Mario Rossi
✅ Messaggio inviato con successo!
```

---

### 7️⃣ Monitora Log in Tempo Reale

```bash
sudo journalctl -u ftth_bot.service -f
```

**Cosa vedere:**
- `🚀 Avvio Bot Telegram FTTH...`
- `✅ Token Telegram caricato correttamente`
- `✅ Bot FTTH attivo e in ascolto! 🎉`
- `HTTP Request: POST .../getUpdates` ogni 10 secondi

Premi `Ctrl+C` per uscire

---

### 8️⃣ Test da Web Interface

1. Apri: http://93.57.240.131:6031/static/manual_entry.html
2. Compila form:
   - Numero WR: `TEST001`
   - Nome Cliente: `Test Cliente`
   - Stato: `aperto`
   - **Assegna Tecnico:** Seleziona un tecnico dal menu
   - **✅ Spunta:** "📱 Invia notifica Telegram al tecnico"
3. Clicca: **✅ Crea Lavoro**
4. Il tecnico dovrebbe ricevere notifica su Telegram!

**Messaggio atteso:**
```
Ciao Mario, ti è stato assegnato il lavoro 
WR TEST001 - indirizzo: N/A - Appuntamento: N/A
```

---

## 🔧 Comandi Bot Disponibili

| Comando | Descrizione | Esempio |
|---------|-------------|---------|
| `/start` | Menu principale con tastiera | `/start` |
| `/help` | Mostra aiuto e comandi | `/help` |
| `/miei_lavori` | Lista lavori assegnati | `/miei_lavori` |
| `/accetta <WR>` | Accetta lavoro (stato → in_corso) | `/accetta 15699897` |
| `/rifiuta <WR>` | Rifiuta lavoro (stato → aperto) | `/rifiuta 15699897` |
| `/chiudi <WR>` | Chiudi lavoro completato | `/chiudi 15699897` |

---

## 🐛 Troubleshooting

### ❌ "Tecnico non trovato"
- Il tuo telegram_id non è nel database
- Esegui: `python get_bot_updates.py` per ottenere il tuo ID
- Aggiorna database con: `UPDATE technicians SET telegram_id = 'TUO_ID' WHERE id = X;`

### ❌ "Lavoro non trovato"
- Il numero WR non esiste o non è assegnato a te
- Usa `/miei_lavori` per vedere i tuoi lavori

### ❌ Bot non risponde
- Verifica bot attivo: `sudo systemctl status ftth_bot.service`
- Riavvia bot: `sudo systemctl restart ftth_bot.service`
- Controlla log: `sudo journalctl -u ftth_bot.service -n 50`

### ❌ "Error 400 Bad Request" 
- Telegram ID non valido nel database
- Verifica formato: deve essere un numero (es: `123456789`)
- NON deve essere una stringa vuota o testo

---

## 📊 Verifica Stato Sistema

```bash
# Status servizi
sudo systemctl status ftth_bot.service
sudo systemctl status ftth.service

# Log bot ultimi 50 messaggi
sudo journalctl -u ftth_bot.service -n 50

# Log bot da ultimo boot
sudo journalctl -u ftth_bot.service -b

# Database - lista tecnici
sqlite3 /home/aaa/fibra/ftth.db "SELECT * FROM technicians;"

# Database - lavori aperti
sqlite3 /home/aaa/fibra/ftth.db "SELECT id, numero_wr, stato, nome_cliente, tecnico_assegnato_id FROM works WHERE stato != 'chiuso';"
```

---

## ✅ Checklist Test Completo

- [ ] Bot attivo: `sudo systemctl status ftth_bot.service`
- [ ] Info bot: `python get_bot_info.py`
- [ ] Bot trovato su Telegram: cerca `@Flowers007bot`
- [ ] `/start` funziona - ricevi benvenuto
- [ ] `/help` funziona - vedi lista comandi
- [ ] Telegram ID ottenuto: `python get_bot_updates.py`
- [ ] Telegram ID aggiunto al database
- [ ] `/miei_lavori` funziona - vedi lavori (o messaggio nessun lavoro)
- [ ] Test notifica da web: crea lavoro con checkbox notifica
- [ ] Notifica ricevuta su Telegram
- [ ] `/accetta <WR>` testato con lavoro reale
- [ ] `/chiudi <WR>` testato con lavoro completato
- [ ] Log bot visibili: `sudo journalctl -u ftth_bot.service -f`

---

**🎉 Se tutti i test passano, il bot è completamente funzionante!**
