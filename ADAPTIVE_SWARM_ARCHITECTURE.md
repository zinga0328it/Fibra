# Lia Adaptive Swarm - progetto sperimentale (NON operativo)

**Stato:** specifica tecnica + prototipo di macchina a stati, isolato sul ramo `feature/lia-adaptive-swarm` derivato da `aaa-mcp`.

## Scopo

Un unico gestionale FTTH, diverse funzioni e interfacce per ogni persona. L'utente puo chiedere a Lia una funzionalita non prevista dal prodotto: uno sciame la analizza, produce una proposta di modifica, la fa verificare e la rende attivabile **solo dopo autorizzazioni e test**. La richiesta non concede agli agenti il diritto di cambiare il gestionale o i dati in autonomia.

Esempio: "Per Davide voglio una schermata che incroci le WR assegnate, l'orario, l'indirizzo e un pulsante navigatore". Se l'operazione richiede nuovo codice, lo sciame propone un modulo isolato; non fa il deploy nel sistema vivo.

## Situazione verificata nel repository (2026-10-24)

- Ramo `main`: FastAPI in `app/main.py`, utenze/ruoli in `app/models/models.py` e `app/routes/auth.py`, frontend in `web/publica/`. Gli endpoint esistenti non garantiscono ancora l'isolamento completo per utente/WR.
- Ramo `aaa-mcp`: MCP indipendente Rust, strumenti operativi esistenti, `--dev-read` con lettura/diff senza scrittura; i sei strumenti progettati per sviluppo sono descritti in `DEVELOPMENT_PLAN.md`.
- Il prototipo di questo ramo **non** cambia `main`, non installa agenti, non abilita tool live e non accede a database, rete, server o clienti.

## Due livelli di personalizzazione

1. **Adattamento configurativo:** dashboard, ordine dei pulsanti, vista calendario, layout accessibile, lingua, scorciatoie; usa componenti gia esistenti.
2. **Nuovo software su richiesta:** nuovi moduli e workflow scritti come codice versionato, eseguiti soltanto nella sandbox di sviluppo, promossi dopo review. Questo secondo livello non puo usare prompt o output LLM come fonte di autorizzazione.

## Sciame logico

| Agente | Output | Limite |
| --- | --- | --- |
| Interprete | Requisiti, destinatario, flusso desiderato | Niente comandi eseguibili |
| Progettista | Contratto di funzione, dipendenze e test | Niente accesso alla produzione |
| Sviluppatore | Diff su ramo temporaneo in sandbox | Solo percorsi approvati |
| Collaudatore | Test unitari, contratto, accessibilita, sicurezza | Evidenza vincolata al commit |
| Revisore | Rischi, permessi e riepilogo modifiche | Non puo autoapprovarsi |
| Rilascio | Feature flag per destinatario, rollback | Solo dopo approvazione umana verificata |

Gli agenti possono essere processi/modelli separati in futuro: per ora e un **workflow progettato**, non uno sciame realmente in esecuzione.

## Identita e isolamento

- Ogni richiesta associa `tenant_id`, `user_id` e `request_id` a una identita **autenticata dal backend**. Non fidarsi di identificativi forniti da ChatGPT, da tool args o dal frontend.
- Filtrare autorizzazioni a livello API e database per ogni WR e ogni campo; la sola UI personalizzata non e una barriera.
- I tecnici non possono cambiare assegnazioni, dati o seriali tramite la personalizzazione se non autorizzati dalle regole esistenti.
- Una chiave API comune non equivale a identita individuale. Richiedere un token di sessione distinto, con ruoli/scopes/tenant e controlli oggetto-per-oggetto.
- Separare dati applicativi, segreti, artefatti generati e log per tenant e utente.
- Nessun modulo generato deve leggere password modem, token, segreti GitHub o dati di altre squadre.

## Pipeline vincolante per NUOVE funzioni

1. `requested`: richiesta, identita verificata, destinatario, limiti e consenso.
2. `proposed`: specifica, capabilita richieste, diff e SHA-256 del codice candidato.
3. `awaiting_review`: test registrati e verificati dal **runner indipendente**, sullo **stesso identico hash**, assenza di errori critici, revisione accessi.
4. `approved`: approvazione umana **fuori dal modello**, monouso e legata a utente/tenant, diff hash, test hash e scadenza.
5. `released`: un servizio di deploy separato verifica approvazione e firma e abilita il modulo via feature flag per l'utente assegnato, con rollback.

Un errore, un nuovo diff o un test inconcludente torna in attesa; nessun retry cieco su azioni che possono aver scritto. Le funzioni ad alto rischio (scritture WR, fatturazione, permessi, credenziali) necessitano revisione amministrativa specifica.

## Isolamento obbligatorio del codice generato

- Runner in VM/microVM effimera, **separata** dai PC AAA/ALEX/ZINGA.
- Nessuna interfaccia di rete verso Yggdrasil, VPN, LAN o Internet; nessun segreto o token installato; dipendenze approvate e pre-caricate.
- Nessun mount del gestionale reale, DB, home, socket Docker, Git, SSH o servizi del sistema host.
- Build/test con CPU/RAM/tempo limitati e log redatti; nessun codice generato viene eseguito nel processo live del MCP.
- Rilascio con revisione dipendenze, firma artefatto, immagine isolata, policy runtime e rollback.

## Piano di integrazione per incrementi

**P0 - presente nel prototipo:** modello `FeatureDraft` in Rust per scoping e transizioni `requested -> proposed -> awaiting_review`; blocca scope errati, hash inconsistenti, test falliti o ripetizioni. Non contiene strumenti MCP pubblicati, deploy, scritture, esecuzione di codice o autenticazione.

**P1:** autenticazione utente/tenant end-to-end, permessi per singola WR, preferenze utente in schema dedicato, API read-only `GET /me/capabilities`.

**P2:** strumenti MCP `feature_request`, `feature_status`, `feature_preview` con identita verificata lato gateway e store con isolamento tenant. Tutti solo per proposte in sandbox, nessun deploy.

**P3:** sviluppo su ramo e workspace effimeri, runner indipendente con attestazione dei test, scan codice, interfaccia di review esterna, approvazione vincolata all'hash.

**P4:** esecutore di rilascio separato, flag per utente, isolamento runtime dei moduli, telemetria, rollback e test di negazione cross-user/cross-tenant.

## Verifiche preliminari richieste prima di P1

- Auditare le route FastAPI senza dipendenza di autorizzazione: per esempio `GET /technicians/`, `POST /works/upload`, `GET /calendar/`; devono controllare identita/permessi e ownership dei dati.
- Auditare il percorso chiave API condivisa in `app/utils/auth.py`: non puo autorizzare implicitamente una operazione su qualsiasi utente.
- Restringere CORS (`app/main.py` usa `allow_origins=["*"]`), secondo origini effettive e politica credenziali.
- Verificare e rimuovere in modo appropriato **dalla storia pubblica**, dopo analisi, backup `ftth.db.*` eventualmente contenenti dati personali; non pubblicare ulteriori DB/seg reti.
- Eseguire test di accesso negativo (tecnico A non vede WR del tecnico B), non solo test funzionali.

## Vincoli Git e continuita

- `main` del gestionale rimane distinto dal ramo `aaa-mcp`: niente merge incrociati o force push.
- Il prototipo lavora su ramo figlio, senza modifiche all'MCP operativo o ai servizi systemd.
- Nessuna connessione GitHub/MCP autorizza automaticamente gli sciami a cambiare software live.
- I componenti aggiunti qui sono una **base di progetto non pronta alla produzione** e necessitano test `cargo test --locked` nell'ambiente autorizzato.
