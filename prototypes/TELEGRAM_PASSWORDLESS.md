# Telegrammino — Login senza password (prototipo isolato)

> **Non attivo nel gestionale.** Questo ramo non cambia `main`, non invia messaggi Telegram, non registra utenti, non espone API, non emette JWT e non avvia agenti o servizi.

## Scelta di prodotto

Per Lia Adaptive Swarm, accesso **passwordless tramite Telegram**, non password + Telegram.

Un solo canale di autenticazione (account Telegram gia' verificato), quindi **non chiamarlo autenticazione a due fattori**. Per un secondo fattore indipendente serviranno ad esempio WebAuthn/passkey in aggiunta, in una fase separata.

## Flusso dell'accesso

1. Durante l'onboarding, un amministratore autorizzato collega `tenant_id/user_id` a un ID Telegram tramite un flusso di **verifica del possesso dell'account**, avviato dall'utente con `/start` e una sfida di collegamento monouso; non basta salvare manualmente `telegram_id`. Ogni utente deve prima aprire la chat privata col bot.
2. Il browser chiede accesso via HTTPS; il backend risolve il profilo verificato senza fidarsi di identita' o ruoli dichiarati dal client. Anti-enumerazione, limiti per account/IP, CSRF e anti-abuso devono essere applicati dal gateway.
3. Il backend crea un identificatore casuale, un segreto legato al browser originale e un codice visivo di confronto a sei cifre. La richiesta scade in 120 secondi.
4. Il bot manda una **richiesta privata** al Telegram gia' associato, con lo stesso codice visualizzato sul browser e pulsanti **Conferma** e **Rifiuta**. Non inviare segreti di sessione, password o dati personali. L'utente confronta i codici e conferma solo se sta accedendo in quel momento.
5. Il gateway verifica davvero l'origine webhook Telegram (secret token + verifica a livello rete/configurazione), `callback_query.from.id`, ID e tipo di chat privata, richiesta pendente e scadenza. I dati provenienti da MCP/ChatGPT/browser non costituiscono prova Telegram.
6. Solo il **browser che ha iniziato** la richiesta e possiede il suo segreto puo' riscuotere una **volta** la conferma. Il backend crea una sessione scoped su tenant/utente e riconosce il metodo `amr=telegram_approval`.
7. Se la richiesta viene negata, scade, l'invio fallisce, e' gia' consumata, o una nuova richiesta invalida la precedente, l'accesso fallisce. Nessun fallback silenzioso alle vecchie password.

## Codice disponibile

- `prototypes/telegram_passwordless.py`: macchina a stati in memoria, nessuna dipendenza da bot, DB o web server.
- `prototypes/test_telegram_passwordless.py`: 7 test sintetici offline, senza rete e senza servizi reali.

Per verificarlo localmente:

```bash
python3 -m unittest discover -s prototypes -p 'test_telegram_passwordless.py' -v
```

Questi test sono stati eseguiti con Python 3.13 nella copia isolata di lavoro: 7 test superati. Sul server AAA / nel CI del progetto non sono stati eseguiti.

## Integrazione ancora necessaria (BLOCCANTE)

- **Associare l'account Telegram in modo comprovato.** La tabella `technicians.telegram_id` da sola non e' un attestato di identita', e il vecchio endpoint di link non basta.
- Store transazionale e centralizzato (es. PostgreSQL), TTL, lock atomico, unicita' delle richieste e consumo singolo anche con workers concorrenti. L'in-memory prototype **non** garantisce queste proprieta' in produzione.
- Integrare callback query nel webhook verificato, gestire `answerCallbackQuery` e bottoni inline, e verificare invio Bot API effettivo. Non abilitare webhooks di test in produzione.
- Endpoint di `start/status/redeem` con protezione abuso, cookies `Secure`, `HttpOnly`, `SameSite`, scadenza e revoca sessioni.
- **Chiudere il percorso JWT attuale**: al momento `app/routes/auth.py` emette access/refresh token dopo la password e il refresh non richiede Telegram. Il nuovo canale di login e i controlli delle API devono essere coerenti prima del passaggio, senza forzare la disconnessione degli utenti in produzione.
- Autorizzazioni obbligatorie lato API e oggetto WR. `X-API-Key` condivisa nel codice corrente non prova l'identita dell'umano che effettua l'accesso.
- Sessioni sensibili: controllo step-up ulteriore opzionale per operazioni amministrative, notifiche accesso, dispositivo rubato, revoca binding, recupero controllato senza Telegram e log senza token.
- Verificare comportamento di phishing dell'approvazione: richiesta proveniente da altro browser, confronto visivo, origine leggibile, nessuna approvazione automatica.
- Non considerare l'SSO Telegram un MFA indipendente; protezione dell'account Telegram dell'utente e del bot sono parte del modello di rischio.
- Test end-to-end su ambiente non produttivo con chat e account di prova, contro webhook falsi, duplicati, replay, clock skew e multi-processo.

## Esempio di testo del bot

Lia Fibra — Richiesta di accesso

Codice sullo schermo: `123456` (solo esempio, **mai usare codici statici**)

Conferma **solo** se hai avviato tu l'accesso e il codice coincide.

Pulsanti: `Conferma accesso` | `Rifiuta`

## Regole per gli sciami

- **Piumino** prepara una richiesta di login anonima.
- **Telegrammino** consegna la domanda all'account verificato, senza emettere sessioni.
- **Guardiana** valida la provenienza e il consenso, blocca le ripetizioni.
- **Rustino** emette una proposta di grant monouso, mai un accesso globale.
- **Lia** fa vedere solo moduli e WR autorizzati da controlli server-side.

Le creature del racconto sono un'analogia: nessun agente autonomo prende oggi decisioni di autenticazione e l'unica fonte di verita' sara' il backend verificato.

