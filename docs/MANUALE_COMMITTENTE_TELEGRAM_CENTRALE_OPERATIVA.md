# Manuale Sintetico Committente
## Sistema FTTH: Telegram Bot + Centrale Operativa Web

**Versione:** 1.0
**Data:** 8 Marzo 2026

---

## 1) Cosa è stato realizzato
È stato implementato un flusso unico tra:
- **Pagina web di centrale**: `centrale_operativa.html`
- **Bot Telegram tecnico**
- **Segreteria/backoffice** (ricezione chiusure su Telegram)
- **GPTs operativo** per inserimento lavori da file YAML
- **VPN Yggdrasil** per protezione della comunicazione tra nodi

Obiettivo: rendere semplice e veloce la gestione lavoro sul campo e la registrazione finale su portali esterni (es. **One.it**).

---

## 1-bis) Inserimento lavori con GPTs + YAML (semplice)
Il sistema usa anche un **GPTs dedicato** per aiutare l'inserimento lavori.

Funzionamento base:
1. si prepara un file **YAML** con i dati del lavoro (WR, cliente, indirizzo, note tecniche)
2. il GPTs legge il file e struttura correttamente i campi
3. il lavoro viene inserito nel gestionale in modo coerente

Vantaggio: meno errori manuali e inserimento più veloce.

---

## 1-ter) Sicurezza rete con VPN Yggdrasil
La comunicazione tra i sistemi avviene su rete protetta con **Yggdrasil VPN**.

In pratica:
- i servizi non sono esposti in chiaro su rete pubblica
- i nodi comunicano su rete privata cifrata
- si riduce il rischio di accessi non autorizzati

Vantaggio: maggiore sicurezza operativa per dati clienti e stato lavori.

---

## 2) Come funziona (in 5 passaggi)

### Passo 1 — Assegnazione lavoro
Il lavoro viene creato/assegnato dal gestionale.

### Passo 2 — Tecnico riceve e apre il lavoro su Telegram
Il tecnico usa:
- `/miei_lavori` → vede i lavori assegnati
- `/accetta <WR>` → prende in carico il lavoro

Dopo `/accetta`, il tecnico riceve subito:
- indirizzo cliente
- eventuale equipaggiamento (ONT/Modem)
- **note tecniche del lavoro** (splitter, porta, PTE, GPON, ecc.)

### Passo 3 — Supporto operativo durante intervento
Il tecnico può usare:
- `/istruzioni` → istruzioni operative rapide
- `/posizione` → invio GPS alla centrale
- `/sos` / `/fine_sos` → emergenza e chiusura emergenza

### Passo 4 — Chiusura lavoro da Telegram
Il tecnico chiude con:
- `/chiudi <WR> <note tecniche finali>`

Le note sono **obbligatorie** e vengono salvate nel database come tracciabilità tecnica.

### Passo 5 — Invio automatico alla segreteria
Alla chiusura, il sistema invia automaticamente alla segreteria (ID Telegram configurato):
- WR
- tecnico
- operatore
- cliente
- indirizzo
- data chiusura
- note tecnico

La segreteria usa queste informazioni per registrare rapidamente la chiusura su **One.it** (e altri portali in subappalto).

---

## 3) Ruolo della pagina `centrale_operativa.html`
La pagina centrale operativa serve per controllo in tempo reale:
- stato tecnici (disponibile / occupato / sos / offline)
- posizione GPS
- eventi SOS con gestione visuale e chiusura SOS

In pratica: il web è la vista operativa centrale, Telegram è lo strumento pratico del tecnico sul campo.

---

## 4) Vantaggi per il committente
- meno errori nella trascrizione delle chiusure
- tempi più rapidi di registrazione pratica
- tracciabilità completa (chi ha fatto cosa e quando)
- standard unico per tecnici e backoffice

---

## 5) Nota tecnica interna
Il sistema può inviare le chiusure anche a **più ID Telegram** (es. più segreterie), se richiesto.
