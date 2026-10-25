# Cose da fare - Gestionale FTTH

**Aggiornato:** 25 ottobre 2026  
**Stato:** promemoria per sviluppi futuri, **non implementati**.  
**Ambiente attuale:** demo in sviluppo con ChatGPT e connettore MCP.

Questa lista serve a non dimenticare le decisioni; **non autorizza modifiche alla produzione**. Ogni intervento richiede approvazione separata. Non inserire credenziali, token, OTP, dati dei clienti o dettagli di accesso privati in questo file.

## 1. Autenticazione con OTP Telegram (`auth_otp_telegram`)

- [ ] Associare ogni utente del gestionale a una identità Telegram verificata.
- [ ] Progettare l'invio di un **codice OTP monouso** tramite bot Telegram per confermare l'accesso o un'azione sensibile.
- [ ] Come proposta iniziale, valutare un codice di 6 cifre valido per 2 minuti; confermare i parametri prima di implementare.
- [ ] Imporre durata breve, uso singolo, numero massimo di tentativi, limiti sui reinvii e scadenza della sessione.
- [ ] Non registrare i codici in chiaro; conservare soltanto esito, data e riferimento dell'operazione.
- [ ] Verificare l'indipendenza dei fattori prima di chiamarla autenticazione a due fattori (2FA/MFA).

## 2. Ruoli e permessi utenti (`rbac_utenti`)

- [ ] Distinguere le identità e le autorizzazioni di **tecnico**, **responsabile di magazzino**, **assistente delivery** e **amministratore**.
- [ ] Concordare una matrice permessi per WR, appuntamenti, documenti, ONT, modem, seriali, magazzino e chiusure.
- [ ] Concedere solo i permessi necessari al ruolo; negare per impostazione predefinita.
- [ ] Prevedere abilitazione, sospensione, revoca e cambio ruolo senza riutilizzare le credenziali di altri utenti.
- [ ] Verificare sul server il ruolo e i permessi per ogni richiesta e per ogni risorsa, non soltanto nelle istruzioni dell'assistente.

## 3. Broker Zinga e connettore MCP

- [ ] Definire come il broker riconosce in modo attendibile l'identità individuale dell'utente che interagisce tramite ChatGPT.
- [ ] Mantenere separate le credenziali tecniche del broker dalle identità e dai permessi degli utenti.
- [ ] Applicare i controlli di autorizzazione in broker/MCP e negli endpoint backend interessati, anche all'interno della rete privata.
- [ ] Registrare un audit essenziale delle operazioni: utente, ruolo, azione, pratica, data ed esito, senza dati segreti.
- [ ] Preparare test isolati con dati fittizi: accesso corretto, accesso negato, OTP errato/scaduto, revoca del ruolo, operazioni non autorizzate.

## 4. Revisione della sicurezza applicativa

- [ ] Verificare e proteggere gli endpoint FastAPI di lettura, modifica e cancellazione delle WR e dei documenti che attualmente non dichiarano controlli applicativi espliciti.
- [ ] Riesaminare autorizzazioni degli strumenti MCP e delle funzioni Telegram/calendario prima di introdurre nuovi ruoli.
- [ ] Verificare configurazioni e valori segreti presenti negli esempi del repository; non supporre che siano credenziali operative.
- [ ] Convalidare la separazione tra accesso web Apache, rete privata e percorso ChatGPT/MCP/broker.
- [ ] Collaudare in ambiente di test, con approvazione esplicita prima di cambiare codice, server, configurazioni o database reali.

---

**Decisione attuale:** nella demo non è ancora prevista la separazione dei ruoli. Questi punti appartengono alla roadmap futura, non sono funzionalità già attive.
