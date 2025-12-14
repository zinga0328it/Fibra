1)

Feature: Importazione lavori 
da PDF nel gestionale web 
Descrizione: Al momento il 
gestionale HTML non ha una 
funzione per importare i 
lavori da file PDF, ma i WR 
che riceviamo dagli 
operatori sono solo in 
formato PDF. Questo ci 
costringe a inserire i dati 
manualmente, con perdita di 
tempo ed alta probabilità 
di errore. 🎯 Obiettivo 
Aggiungere al gestionale una 
funzione "Importa WR da PDF" 
che permetta di: 1. Caricare 
uno o più file PDF delle 
bolle di lavoro (WR) 2. 
Effettuare il parsing dei 
dati principali (codice WR, 
indirizzo, data, tecnico, 
stato, note, ecc.) 3. Creare 
un nuovo lavoro oppure 
aggiornare un lavoro 
esistente nel DB 4. Mostrare 
un riepilogo dei dati 
estratti prima del 
salvataggio definitivo 
💻 Proposta di flusso 
(frontend) Aggiungere un 
pulsante nel gestionale web, 
es. in Works: Importa da PDF 
L’utente seleziona uno o 
più PDF Il backend espone 
una route tipo: POST 
/works/import-pdf Il 
sistema: processa il PDF 
restituisce i dati estratti 
salva/aggiorna i record in 
base al codice WR ✅ 
Criteri di accettazione È 
possibile caricare almeno 1 
PDF alla volta (ideale 
supportare multi-upload) Se 
il WR non esiste → viene 
creato un nuovo lavoro Se il 
WR esiste → vengono 
aggiornati i campi (senza 
perdere lo storico)
In caso di errore parsing → log + messaggio chiaro all'utente

---

## 📅 Aggiornamento 14 Dicembre 2025

### ✅ COMPLETATO - Sistema Telegram + Yggdrasil

#### Funzionalità Telegram Implementate:
- ✅ Bot Telegram attivo: `@MaioriDealsBot`
- ✅ Campo `telegram_id` aggiunto ai tecnici (database + API + frontend)
- ✅ Endpoint `PATCH /technicians/{id}` per aggiornare Telegram ID
- ✅ Modal nell'interfaccia web per gestire Telegram ID dei tecnici
- ✅ Comandi bot: `/start`, `/help`, `/miei_lavori`, `/accetta`, `/rifiuta`, `/chiudi`
- ✅ Notifiche automatiche ai tecnici quando assegnati a lavori

#### Yggdrasil Network - Accesso Remoto:
- ✅ Backend FTTH attivo su porta 6030 (con `--host ::` per IPv6)
- ✅ API Yggdrasil separata su porta 8600
- ✅ Connessione testata da PC esterno via Yggdrasil
- ✅ Integrazione Apache per servicess.net/gestionale/

#### Configurazione Attiva:
```
Indirizzo Yggdrasil: 200:421e:6385:4a8b:dca7:cfb:197f:e9c3
Backend FTTH:        porta 6030
API Yggdrasil:       porta 8600
Chiave Yggdrasil:    ftth_ygg_secret_2025
```

#### Test Superati:
- 100% test suite (API, Telegram, Yggdrasil)
- Connettività da PC esterno (alex@alex) verificata
- Notifiche Telegram funzionanti

#### Prossimi Passi:
1. Monitorare stabilità connessione Yggdrasil
2. Implementare service systemd per avvio automatico
3. Aggiungere più tecnici con Telegram ID
4. Testare workflow completo in produzione
