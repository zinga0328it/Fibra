# Rapporto: 32 Actions, adattatore HTTP e sviluppo in lettura

## Stato effettivo

- Fonte locale: /home/aaa/fibra/obsidian/appunti_gpt_s/gpt_s.md, OpenAPI 3.1.0.
- 32 operationId univoci: 17 GET e 15 operazioni di scrittura/azione.
- Profilo --mock-actions: 38 tool, con nomi originali delle 32 Actions e i sei
  helper search, fetch, cerca_wr, stato_wr, stato_api, riepilogo_wr.
- Profilo --mock: conserva i sei tool originali e i relativi test.
- Dati sintetici in memoria, orologio simulato fisso 2026-10-15T12:00:00Z.
- Nessun accesso a database, API reali, chiavi o file .env. Nessun deploy.
- Le notifiche aggiungono eventi in memoria; non inviano messaggi Telegram.
- I documenti sono metadati fittizi, non file PDF di clienti.
- --dev-read espone project_read e project_diff solo via stdio, sulla directory
  MCP fissata in compilazione. Non espone scrittura, shell, test o commit.
- HttpActionsTestServer collega 32 tool MCP a HttpTestAdapter, usato soltanto
  dal banco di prova con server HTTP loopback e credenziali fittizie.
- Il runner OS isolato non e' installato. Nessuna interfaccia swarm ALE verificata
  o utilizzata; ALEX e' distinto da ALE. Host di sviluppo rilevato: aaa-aaa.

Copertura dei nomi e delle chiamate simulate: 32/32 Actions, piu' 6 helper.
Traduzione MCP -> HTTP locale: 32/32 Actions, metodo/path/query/body/header.
Equivalenza funzionale in produzione: NON verificata per nessuna Action.
Questo rapporto NON dichiara conclusa la migrazione e non autorizza lo spegnimento
del GPT esistente. La copia locale deve ancora essere confrontata con il GPT attivo.

## Adattamento del contratto

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

Ultima esecuzione: 66 test Rust e 8 test Python superati, zero fallimenti.
Controllo --check: 32 contratti corrispondenti allo YAML locale.
Nessun test chiama la produzione.
I server HTTP di test usano porte loopback temporanee e vengono terminati.
Rustfmt --check e Clippy --all-targets -- -D warnings: PASS.
Installazione dedicata .tools/{rustup,cargo}, esclusa da Git, senza modifiche
alla toolchain condivisa o ai profili di shell. Rustup verificato con SHA-256.
Versioni: rustc 1.91.1 (ed61e7d7e), cargo 1.91.1 (ea2d97820),
rustfmt 1.8.0-stable e clippy 0.1.91. Comandi riproducibili nel README.

## Sviluppo e pubblicazione

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
- Restano bloccati: connessione ChatGPT, broker/API reali, pubblicazione GitHub
  senza accesso e verifica della visibilita' privata, e disattivazione del GPT.
  Nessuna modifica alle chiavi.