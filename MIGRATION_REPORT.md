# Rapporto: 32 Actions, adattatore HTTP e sviluppo in lettura

## Stato effettivo

Aggiornamento 2026-10-16: l'utente ha richiesto esplicitamente l'abilitazione delle
scritture. --live collega tutte le 32 Actions e i 6 helper; --live-read-only
mantiene il blocco delle sole scritture. 77 test Rust e Clippy superati.
Verificati sul backend reale, tramite MCP: tutti i 17 GET e tutti i 6 helper,
inclusi fetch di lavoro/ONT/modem, senza errori o casi saltati. Nessuna scrittura
reale di collaudo. Profilo operativo attivo su 16033; istanza 16035 chiusa.
Catalogo ChatGPT aggiornato e verificato nella scheda Lia Fibra TEST:
updateWork e createManualWork descrivono scritture API REALE, helper operativi.
L'utente ha poi autorizzato correzioni mirate delle API, backup e riavvio del
solo ftth.service. Quattro regressioni Python PASS; riavvio effettuato
dall'utente alle 00:58 CEST del 2026-10-16, servizio active/running.
Health e OpenAPI via ingresso GPT verificati, inclusi i quattro campi corretti.
MCP definitivo ricaricato su 16033: ripetuti tutti i 17 GET e i 6 helper,
tutti HTTP 200, simulated=false, live_read_write. Tunnel readiness HTTP 200.

- Fonte locale: /home/aaa/fibra/obsidian/appunti_gpt_s/gpt_s.md, OpenAPI 3.1.0.
- 32 operationId univoci: 17 GET e 15 operazioni di scrittura/azione.
- Profilo --mock-actions: 38 tool, con nomi originali delle 32 Actions e i sei
  helper search, fetch, cerca_wr, stato_wr, stato_api, riepilogo_wr.
- Profilo --mock: conserva i sei tool originali e i relativi test.
- Dati sintetici in memoria, orologio simulato fisso 2026-10-15T12:00:00Z.
- Nessun accesso diretto a database. Profilo --live attivo sul servizio locale
  usato dal tunnel; tutte le letture MCP verificate con HTTP 200 e simulated=false.
  Credenziale client solo in memoria.
- Lia Fibra TEST collegata a ChatGPT tramite Secure MCP Tunnel; 38 strumenti
  aggiornati al profilo reale lettura/scrittura. La chiamata stato_api da ChatGPT
  era stata verificata nel precedente profilo live_read_only; dopo il ricaricamento
  verificati catalogo ChatGPT e chiamate reali dal client MCP locale.
- Nei mock le notifiche aggiungono eventi in memoria e i documenti sono fittizi.
  In --live le notifiche sono reali e possono inviare messaggi Telegram.
- --dev-read espone project_read e project_diff solo via stdio, sulla directory
  MCP fissata in compilazione. Non espone scrittura, shell, test o commit.
- HttpActionsTestServer collega 32 tool MCP a HttpTestAdapter, usato soltanto
  dal banco di prova con server HTTP loopback e credenziali fittizie.
- Il runner OS isolato non e' installato. Nessuna interfaccia swarm ALE verificata
  o utilizzata; ALEX e' distinto da ALE. Host di sviluppo rilevato: aaa-aaa.

Copertura dei nomi e delle chiamate simulate: 32/32 Actions, piu' 6 helper.
Traduzione MCP -> HTTP locale: 32/32 Actions, metodo/path/query/body/header.
Verificati in produzione tramite MCP: tutti i 17 GET e i sei helper.
Equivalenza funzionale completa delle 32 Actions e dei sei helper: NON verificata.
Questo rapporto NON dichiara conclusa la migrazione e non autorizza lo spegnimento
del GPT esistente. La copia locale deve ancora essere confrontata con il GPT attivo.

## Adattamento del contratto

Il contratto originale e i simulatori restano immutati. Il profilo reale applica
src/live_contract.rs, verificato con OpenAPI pubblico del backend e funzioni
Python: campi nullable, date locali ISO senza fuso inventato, stati apparati in
inglese, statistiche annuali con date YYYY-MM, alias tecnico_assegnato tradotto
in tecnico_assegnato_id. Metadati della creazione manuale mantenuti annidati.
Difetti backend riprodotti e corretti dopo autorizzazione: updateWork ignorava
extra_fields, telefono_cliente, modem_sn e note_chiusura; manual/works non salvava
Work.note e annidava erroneamente i metadati. Quattro test su SQLite temporaneo
ora provano persistenza, omissioni/null e rifiuto degli input invalidi.
Nessuna migrazione DB: tutte le colonne esistevano gia'.

Le sezioni seguenti sulla fedelta' dell'esportazione descrivono il contratto
originale e i profili simulati, non annullano gli adattamenti live sopra indicati.

Ogni Action mantiene operationId come nome del tool. I parametri path/query
restano campi top-level con i nomi originali. Il body JSON diventa il campo body,
obbligatorio quando richiesto dallo YAML. parameter_locations conserva la
distinzione tra query e path per l'adattatore. parameter_metadata conserva
style, explode e allowReserved quando dichiarati.

L'esportazione risolve riferimenti locali aciclici, inclusi i vincoli fratelli
del riferimento. Riferimenti esterni/ciclici bloccano l'esportazione.
Non include server URL, esempi,
descrizioni o credenziali. Conserva tipi, obbligatorieta', enum, formati e limiti
presenti nello schema, default, const e proprieta' aggiuntive. Non risultano
default dichiarati nello YAML corrente; la loro conservazione e' verificata
su fixture sintetiche. I default non vengono materializzati nella richiesta:
campo omesso e valore esplicito restano distinti. Default sensibili, anche
referenziati o annidati, bloccano l'esportazione anziche' essere cancellati.
Le estensioni nullable sono normalizzate in anyOf con null anche sui riferimenti.
Un campo opzionale non e' automaticamente nullable: note:null in updateWork
resta vietato, mentre null nelle proprieta' aggiuntive consentite e' preservato.
Non si aggiunge additionalProperties:false agli input delle Actions; le
restrizioni esplicite del body restano invariate. Gli helper restano rigorosi.

Ogni tool del profilo esteso pubblica inputSchema e outputSchema. Gli input
sono validati con JSON Schema e controllo dei formati. Le risposte di successo
delle 32 Actions sono validate contro lo schema 200 risolto prima del commit
della transazione simulata. Gli outputSchema degli helper sono generici a
livello data; la loro struttura e' verificata dai test, non interamente tipizzata.

Le risposte MCP contengono simulated=true, http_status e data oppure error.
Gli errori applicativi hanno isError=true; input malformati possono restituire
errori MCP. Nessun errore applicativo incorpora body, header o credenziali.
Nel simulatore gli status HTTP sono metadati simulati, non risposte ricevute.
Nel banco HTTP il marker e' test_http=true e http_status proviene dal server
di collaudo, oppure e' null quando manca un esito HTTP utilizzabile.

## Trasporto HTTP verificato

- Ogni Action attraversa il protocollo MCP, poi reqwest e un server di cattura
  locale. Verificati metodo, path con escaping, query, body JSON e header.
- Lo YAML dichiara ApiKeyAuth, apiKey in header X-API-Key; i test usano soltanto
  mock-api-key-not-production. L'autenticazione reale ZINGA resta da verificare.
- Nessun proxy, redirect o retry automatico. Solo IP loopback espliciti;
  nessuna risoluzione DNS di destinazioni fornite dall'utente, URL reale o
  credenziale letta dall'ambiente. Nessuna modalita' CLI di collegamento reale.
- Tutte le 15 scritture provate con 401/403/404/409/422/503, redirect e timeout:
  una sola richiesta osservata per chiamata, nessun body d'errore o chiave esposti.
- Risposte malformate, di forma errata, oltre 1 MiB e connessione indisponibile
  producono errori sanificati. Input limitato a 16 KiB, deadline per l'intera risposta.
- Il body resta identico, inclusi campi aggiuntivi e null consentiti. I parametri
  opzionali omessi non vengono aggiunti. Query scalari e array form supportati;
  oggetti query e stili non supportati vengono rifiutati esplicitamente.
- L'assenza di retry nell'adattatore NON fornisce idempotenza fra due chiamate MCP
  distinte. Dopo un timeout una scrittura puo' essere gia' avvenuta: servono
  riconciliazione e contratto idempotenza del backend prima di consentire retry.

## Matrice operazioni

Per tutte le righe: il tool MCP ha lo stesso nome dell'operationId, esiste un
test nominato nello stesso modo in tests/actions.rs e una verifica parametrizzata
MCP -> HTTP in tests/http_adapter.rs. Stato: MOCK E TRADUZIONE HTTP TESTATI,
NON VERIFICATO IN PRODUZIONE. Header da YAML: X-API-Key, valore solo fittizio.

| operationId / tool MCP | Metodo e path |
| --- | --- |
| getHealth | GET /health/ |
| getWorks | GET /works/ |
| getWorkById | GET /works/{work_id} |
| updateWork | PUT /works/{work_id} |
| deleteWork | DELETE /works/{work_id} |
| createManualWork | POST /manual/works |
| getTechnicians | GET /technicians/ |
| getTeams | GET /teams/ |
| getWeeklyStats | GET /stats/weekly |
| getClosedByOperator | GET /stats/closed_by_operator |
| getClosedByTechnician | GET /stats/closed_by_technician |
| getDailyClosedStats | GET /stats/daily_closed |
| getYearlyStats | GET /stats/yearly |
| getDocuments | GET /documents/ |
| getModems | GET /modems/ |
| createModem | POST /modems/ |
| getModemById | GET /modems/{modem_id} |
| updateModem | PUT /modems/{modem_id} |
| installModem | PUT /modems/{modem_id}/install |
| assignModemToWork | PUT /works/{work_id}/modem/{modem_id} |
| getWorkEquipment | GET /works/{work_id}/equipment |
| markEquipmentDelivered | PUT /works/{work_id}/equipment/delivered |
| getONTs | GET /onts/ |
| createONT | POST /onts/ |
| getONTById | GET /onts/{ont_id} |
| updateONT | PUT /onts/{ont_id} |
| installONT | PUT /onts/{ont_id}/install |
| assignONTToWork | PUT /works/{work_id}/ont/{ont_id} |
| notifyWorkAssignment | POST /works/{work_id}/notify |
| assignTechnicianToWork | PUT /works/{work_id}/assign/{technician_id} |
| getCalendar | GET /calendar/ |
| updateAppointment | PUT /calendar/{work_id} |

Il dettaglio strutturale per ogni riga (parametri, body, risposte e status
dichiarati) e' in contracts/actions.json. source_sha256 identifica la fonte
senza copiarne gli esempi. Il comando --check rileva modifiche della fonte:

```sh
python3 scripts/export_contract.py /percorso/schema-locale.md --check
cargo test --locked
```

## Test implementati

- 7 test originali del nucleo: identificativi, ricerche, limiti, duplicati,
  dinieghi e indisponibilita' simulati, stabilita' delle letture.
- 32 regressioni nominate: successo e schema output per ogni Action;
  parametri obbligatori assenti rifiutati e argomenti aggiuntivi consentiti.
- 8 test aggiuntivi: inventario, diniego/scadenza/outage su tutte le Actions,
  lifecycle WR/statistiche, apparati/conflitti, calendario, atomicita'/isolamento
  tra istanze, tipi/date/enum/dimensioni, coerenza tra Actions e sei helper.
- 6 test di protocollo/avvio: tool mock su stdio e HTTP, profilo sviluppo via
  stdio, input invalidi, schemi/annotazioni, tool vietati e bind non-loopback.
- 7 test HTTP: catena MCP e cattura per tutte le 32 Actions, zero retry sulle
  15 scritture, errori/timeout, escaping, null/omissioni, limiti e destinazioni.
- 6 test filesystem: allowlist, traversal, symlink interni/esterni, hardlink,
  race, root fissata al descrittore, file speciali/binari/grandi, hash e no-write.
- 8 test Python: default, proprieta' applicative, nullable, vincoli, riferimenti,
  default sensibili, override dei parametri e annotazioni escluse.

Ultima esecuzione Rust: 77 test superati, inclusi undici test del profilo reale:
32 Actions attraverso MCP/HTTP, 135 casi senza retry delle 15 scritture,
alias/campi ignorati, esiti incerti, sei helper e collisioni ID/WR duplicati,
prefisso/header sensibile, protezioni read-only, date locali e health UTC.
Le guardie CLI coprono chiave mancante, bind non-loopback e porta implicita.
Ultima esecuzione Python: 8 test superati. Nessun fallimento.
Controllo --check: 32 contratti corrispondenti allo YAML locale.
Nessun test chiama la produzione.
I server HTTP di test usano porte loopback temporanee e vengono terminati.
Rustfmt --check e Clippy --all-targets -- -D warnings: PASS.
Installazione dedicata .tools/{rustup,cargo}, esclusa da Git, senza modifiche
alla toolchain condivisa o ai profili di shell. Rustup verificato con SHA-256.
Versioni: rustc 1.91.1 (ed61e7d7e), cargo 1.91.1 (ea2d97820),
rustfmt 1.8.0-stable e clippy 0.1.91. Comandi riproducibili nel README.

## Sviluppo e pubblicazione

Diagnosi rete del 2026-10-15: il 403 iniziale riguardava /gestionale/, rotta umana
protetta da allowlist nella configurazione ALEX fornita. L'ingresso GPT dedicato
e' /gestionale-gpt/ e ha superato health e statistiche via MCP, attraverso ZINGA.
Il client invia solo X-API-Key; ALEX e ZINGA aggiungono le chiavi dei rispettivi
salti. Nessuna acquisizione di RELAY_KEY/INTERNAL_KEY nel MCP, nessun bypass
diretto verso ZINGA/AAA, nessun SSH o modifica ai servizi di produzione.
Il proxy ALEX fornito usa Yggdrasil verso ZINGA; le note ZeroTier precedenti
descrivono un piano di hardening, non un motivo per cambiare la rete funzionante.

project_read legge solo src/tests Rust, scripts Python, il contratto e i documenti
root esplicitamente autorizzati, fino a 128 KiB UTF-8. Apre ogni componente con
openat e NOFOLLOW; rifiuta symlink, hardlink multipli, file nascosti/sensibili e
file speciali. project_diff confronta il file con proposed_content dopo verifica
expected_sha256; restituisce un unified diff senza scrivere o eseguire Git.
Limite diff 128 KiB e budget algoritmo 200 ms. Questi tool leggono codice reale
del solo progetto, non dati FTTH; non sono una sandbox o un servizio multiutente.

Branch locale: mcp/http-adapter-validation, nel solo progetto ftth-lia-mcp.
Destinazione richiesta: git@github.com:zinga0328it/ftth-lia-mcp.git, privata.
Verifica SSH non interattiva: ERROR: Repository not found. Possibile assenza
del repository o mancanza di permessi; proprietario e visibilita' non verificabili.
Nessun push, nessun repository alternativo o cambio di visibilita'.
Commit locale comunicato nel riepilogo di consegna; nessun commit nel repository Fibra.

## Limiti e assunzioni da verificare

- Collegamento reale autorizzato e attivato il 2026-10-15 per Lia Fibra TEST:
  endpoint corretto https://servicess.net/gestionale-gpt/, ricavato dal proxy ALEX
  fornito dall'utente. /gestionale/ e' la rotta umana con allowlist, non il nuovo
  ingresso GPT. Nessuna modifica a proxy, broker, firewall o chiavi.
- --check-live verifica health; --live-read-only usa FTTH_API_KEY nell'ambiente,
  avvio vincolato a health valida e bind loopback. Il servizio mock del tunnel
  e' stato sostituito con quello reale, senza fermare il tunnel o il GPT operativo.
  Nessun test di scrittura reale. Nuova chiamata stato_api da ChatGPT verificata
  con HTTP 200 e simulated=false; attivita' "Verificato lo stato dell'API Lia Fibra TEST".
  Conversazione: https://chatgpt.com/c/6ad14f6f-b720-83eb-bab7-4c8dbc79988a.
- Compatibilita' health: timestamp naive UTC normalizzato soltanto per getHealth.
  Date locali delle altre risorse validate e mantenute come ricevute; verifiche
  reali di lavori, calendario, documenti e apparati riuscite.
- /works/ non ha filtri WR. Gli helper leggono l'elenco con limite 16 MiB,
  esplicitato nei metadati, e cercano la stringa esatta. Duplicati: ambiguous.
  fetch usa work_ID, ont_ID, modem_ID; material_ID senza tipo non e' un ID reale.
  search non espone credenziali degli apparati e non restituisce risultati
  parziali come completi in caso di errore di una collezione.
- Scritture con esito unknown non vanno ripetute senza riconciliazione. Tutte
  mantengono assenza di retry/redirect e annotazioni distruttive/non idempotenti.

- Lo YAML non descrive tutta la logica di business e molti campi output non sono
  required: superare lo schema non prova equivalenza con l'implementazione reale.
- Regole simulate su duplicati, conflitti, rilascio apparati dopo cancellazione,
  installazione, notifiche e aggiornamento date non sono state confrontate con AAA.
- Le statistiche usano l'orologio fisso; settimana da lunedi', conteggi giornalieri
  delle chiusure disponibili e mesi dell'anno simulato. Semantica, timezone,
  intervalli, ordinamento e archiviazione reali restano da verificare.
- I simulatori aggiungono errori difensivi 400/404/409/401/403/503 anche dove lo
  YAML non li documenta. Formato e copertura degli errori reali restano gap.
- Il simulatore non applica autenticazione HTTP/OAuth o permessi per utente/WR;
  Denied/Expired/Unavailable sono scenari locali, non token reali verificati.
- Gli schemi dei dispositivi includono wifi_password per fedelta' contrattuale:
  usare esclusivamente valori fittizi. Prima dell'integrazione reale occorre una
  policy esplicita per campi sensibili, senza perdita silenziosa di funzionalita'.
- Lo stato e' condiviso tra sessioni dello stesso processo mock. Non esporre
  questo processo a utenti reali o tramite reverse proxy/tunnel.
- Gli strumenti di scrittura/esecuzione richiedono il sistema isolato del
  DEVELOPMENT_PLAN e restano assenti. Il profilo di lettura host autorizzato
  non protegge da un processo ostile con lo stesso UID o da mount ostili.
- Restano da verificare su operazioni concordate: effetti delle scritture reali,
  campi ignorati dal backend, pubblicazione GitHub privata senza accesso e
  sostituzione del GPT operativo. Nessuna modifica alle chiavi o ai servizi FTTH.