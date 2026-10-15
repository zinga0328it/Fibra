# Lia Fibra MCP - Stato e diario operativo

Aggiornato: 2026-10-16.
Questa nota serve a riprendere il lavoro senza rifare domande gia' risolte.
Aggiornarla dopo verifiche, decisioni e modifiche significative. Non inserire segreti.

## Ripresa della prossima sessione

- Leggere prima l'aggiornamento corrente sotto, poi la cronologia solo se serve.
  Non richiedere nuovamente topologia, chiavi o autorizzazioni gia' documentate.
- Workspace gestionale: /home/aaa/fibra, branch main. MCP corrente:
  /home/aaa/ftth-lia-mcp, branch mcp/http-adapter-validation, repository distinto
  con destinazione GitHub aaa-mcp nello stesso zinga0328it/Fibra. La cartella MCP/ del
  gestionale e la sua guida PUBLIC_DEPLOYMENT.md descrivono l'esperimento precedente.
- L'utente ha confermato esplicitamente: main e' AAA. Ha richiesto il nuovo ramo
  aaa-mcp per il progetto Rust, non un nuovo repository GitHub. I due checkout
  locali restano separati e aaa-mcp ha albero e cronologia propri: niente merge
  nel gestionale. Gli altri rami appartengono agli altri PC: non toccarli.
  Push solo con destinazioni esplicite; vietati force, mirror, --all e cancellazioni.
- Istruzioni automatiche .github/copilot-instructions.md presenti in entrambi
  i repository e collegate a questo diario. Le credenziali non vanno versionate.
- Prossimo limite operativo noto: MCP e tunnel sono processi avviati da terminale;
  l'avvio automatico dopo reboot non e' stato configurato in questo intervento.
  Non considerare gli identificativi di processo registrati una prova di stato futuro.
- Git: salvare soltanto i cambiamenti dell'intervento. Nel gestionale esistono
  numerose modifiche precedenti e file locali sensibili: niente git add globale.
  I commit delle correzioni API devono escludere il delta preesistente al backup.
- Verifiche gia' effettuate: 77 test Rust, Clippy, 4 regressioni API isolate,
  tutti i 17 GET e i 6 helper reali; catalogo ChatGPT aggiornato. Nessuna scrittura
  di collaudo sui dati reali. Rilanciare solo i controlli pertinenti alle nuove modifiche.

## Pubblicazione GitHub verificata il 2026-10-16

- Repository: https://github.com/zinga0328it/Fibra.
- main (AAA): pubblicati ad01d40 per le correzioni API e 0afb5b7 per le istruzioni
  sui rami. Questo diario viene aggiornato separatamente dopo la verifica del push.
- aaa-mcp: creato e pubblicato fino a ef1fbbb, incluso e7abb91 con il MCP completo.
  Il checkout Rust locale resta su mcp/http-adapter-validation e traccia
  origin/aaa-mcp. Nessuna fusione dei due alberi o delle due cronologie.
- Confrontati i riferimenti remoti prima e dopo: gli altri sei rami sono invariati.
  Nessun force push, merge, cancellazione o modifica ai rami degli altri PC.
- Prima pubblicazione MCP: controllo di tutte le 45 versioni di file nella
  cronologia contro credenziali locali note e formati comuni di segreti PASS.
- Servizi e dati reali non modificati dalla pubblicazione. Il lavoro precedente
  non committato nel gestionale resta locale e non e' stato incluso nel push.

## Cronologia: salvataggio locale del 2026-10-16

- MCP: commit e7abb91 sul branch mcp/http-adapter-validation, con profilo live,
  adattamento contratto, test e istruzioni di continuita'. Working tree pulito
  alla verifica successiva al commit. Nessun remoto configurato, nessun push.
- Gestionale: commit mirato con sole correzioni API rispetto al backup iniziale,
  quattro regressioni, questo diario e istruzioni automatiche. Le modifiche
  precedenti negli stessi file sono state escluse dall'indice, non annullate.
  Riferimento consultabile con git log -1 --oneline --
  obsidian/MCP-Lia-Fibra/STATO-E-DIARIO.md dalla directory del gestionale.
- Verifica del contenuto esatto in staging: copia isolata delle sorgenti tracciate
  app/, tests/test_app.py e telegram_endpoints.py, quattro test PASS e quattordici
  deselected. Nessun accesso al DB di produzione o invio di notifiche.
- Controllo dei segreti nel delta di entrambi i repository PASS, senza stampare
  valori. Non inclusi backup, database, log, credenziali o dati dei clienti.
- In questa prima fase nessun push eseguito; la pubblicazione e' stata poi
  autorizzata sui rami indicati sopra. Il working tree del gestionale resta intenzionalmente
  modificato per il lavoro preesistente; non ripulirlo automaticamente.

## Aggiornamento 2026-10-16: profilo operativo completo

L'utente ha richiesto esplicitamente di abilitare le scritture e leggere le API.
Aggiunto --live: 32 Actions originali, comprese le 15 scritture, e tutti i 6 helper.
--live-read-only rimane disponibile. Nessuna scrittura reale di prova.
Successivamente l'utente ha autorizzato correzioni mirate alle API e il riavvio
del solo servizio API dopo backup e test isolati. Bot, DB, chiavi e rete intatti.

Letti i file allegati e OpenAPI reale attraverso /gestionale-gpt/openapi.json:
il backend raggiunto e' FTTH Management System, non l'altra API Yggdrasil.
Compatibilita' nel solo MCP: nullable, stati apparati inglesi, date ISO locali
senza fuso aggiunto, statistiche annuali date YYYY-MM, alias tecnico_assegnato
-> tecnico_assegnato_id; extra_fields resta annidato, con backend corretto.

WR: /works/ non ha filtri. Cerca/stato/riepilogo usano l'elenco API completo,
con limite 16 MiB dichiarato nei tool, confronto stringa esatto e rifiuto dei
duplicati. search consulta lavori/ONT/modem e restituisce massimo 20 risultati,
senza credenziali degli apparati. fetch usa work_ID, ont_ID, modem_ID: gli ID
dei due inventari non vanno confusi e material_ID del mock non identifica un
materiale reale. I risultati includono api_id/work_id per le Actions successive.

Verifiche: 77 test Rust PASS; Clippy senza avvisi; test completo delle 32 Actions
nel profilo live contro server locale, piu' 135 casi errore/timeout sulle 15
scritture senza retry. Risposte write_outcome completed/rejected/unknown;
unknown richiede verifica, non una nuova scrittura automatica.

Collaudo reale del profilo --live su 16035: tutti i 17 GET e tutti i 6 helper
HTTP 200, simulated=false, live_read_write; fetch lavoro/ONT/modem verificati.
Zero errori e zero casi saltati, senza stampare dati clienti o credenziali.
Profilo --live attivo su 16033; istanza temporanea 16035 chiusa.
Ultimo eseguibile ricaricato dopo il riavvio API: ripetuti sul processo definitivo
tutti i 17 GET e i 6 helper, tutti HTTP 200, simulated=false, live_read_write.
Catalogo locale: 38 strumenti, 15 scritture, quattro campi corretti in updateWork.
Tunnel readiness HTTP 200, senza riavviare o riconfigurare il tunnel.
Browser nuovamente disponibile: Aggiorna strumenti completato in Lia Fibra TEST.
Scheda strumenti ChatGPT verificata: updateWork/createManualWork API REALE,
helper operativi. Nessuna nuova scrittura di prova o modifica al GPT originale.

Difetti riprodotti e corretti con autorizzazione esplicita tramite domanda:
updateWork ignorava extra_fields/telefono_cliente/modem_sn/note_chiusura;
la creazione manuale non salvava note e annidava i metadati. Ora le tre sorgenti
sono corrette e il MCP espone tutti i campi. Quattro regressioni aggiunte a
tests/test_app.py: prima quattro FAIL, poi quattro PASS su SQLite temporaneo.
Test Python in .tools/backend-tests, pytest solo in .tools/backend-test-venv,
librerie di produzione lette senza modificarle, log isolati e rete disabilitata.

Backup delle versioni preesistenti, incluse le modifiche precedenti dell'utente:
/home/aaa/ftth-lia-mcp/.tools/backups/backend-20261015T224157Z.
Servizio: ftth.service, app.main:app, porta 6030, runtime
/home/aaa/fibra/venv/bin/uvicorn. L'utente ha riavviato ftth.service dopo il blocco
sudo non interattivo: avvio 2026-10-16 00:58:42 CEST, MainPID 3622019,
active/running. Health e OpenAPI verificati via ingresso GPT, inclusi extra_fields,
telefono_cliente, modem_sn e note_chiusura. Nessuna installazione nel runtime.
MCP su terminale f8d187c1-14a4-4688-b53a-33ad897e0590, porta 16033;
non e' installato come servizio persistente. Il vecchio terminale MCP e' chiuso.
Scritture verificate con test isolati, non con mutazioni dei dati reali.

Questo aggiornamento prevale sui blocchi storici riportati qui sotto.

## Cronologia 2026-10-15: ingresso GPT trovato

La configurazione Apache di ALEX fornita successivamente dall'utente distingue:

- `/gestionale/`: rotta umana legacy, allowlist IP e iniezione della chiave legacy.
  Il 403 rilevato in precedenza era su questa rotta: non usarla per il nuovo MCP.
- `/gestionale-gpt/`: rotta GPT dedicata, proxy verso ZINGA:6032/gestionale/;
  ALEX aggiunge X-Relay-Key senza sovrascrivere la chiave client X-API-Key.
- Il proxy fornito usa l'indirizzo Yggdrasil di ZINGA. Le vecchie note "solo
  ZeroTier" sono un piano di hardening, non la descrizione di quel blocco attivo.
  Nessuna rete o configurazione Apache e' stata modificata per uniformarle.

Endpoint fisso del nuovo ProductionAdapter: `https://servicess.net/gestionale-gpt/`.
API_GPTS viene letta dalla configurazione locale dentro il processo di avvio,
senza copiarne il valore dalla chat o scriverlo nei file, e passata come FTTH_API_KEY.
Non vengono acquisite chiavi relay/interne nel MCP.

Verifiche riuscite: preflight reale HTTP 200; client MCP locale -> 38 strumenti ->
stato_api e getWeeklyStats entrambi HTTP 200, simulated=false, mode=live_read_only.
Per le statistiche verificati i campi interi closed_this_week e suspended, senza
stampare dettagli di clienti. Nessun test di scrittura reale.

Correzione client: solo getHealth normalizza in RFC 3339 il timestamp naive UTC
prodotto dal backend tramite datetime.utcnow().isoformat(). Gli altri schemi
restano rigorosi. Ultima suite completa: 72 test Rust, Clippy e Rustfmt PASS.

Il servizio mock sulla porta 16033 e' stato sostituito con --live-read-only;
il tunnel e il GPT operativo non sono stati fermati o riconfigurati. L'istanza
temporanea di collaudo sulla porta 16035 e' stata chiusa. Chiamata da ChatGPT
stato_api({}) RIUSCITA: HTTP 200, simulated=false, mode=live_read_only, status=ok.
Confermata anche l'attivita' "Verificato lo stato dell'API Lia Fibra TEST".
Aggiornamento strumenti dell'app confermato:
la scheda mostra API REALE, non SIMULAZIONE LOCALE, e descrive i blocchi degli helper.
Conversazione di collaudo reale: https://chatgpt.com/c/6ad14f6f-b720-83eb-bab7-4c8dbc79988a.
La prima richiesta ha inviato soltanto la menzione dell'app per un problema di input
del browser; interrotta. Reinviato e verificato il testo che richiede solo stato_api.

Limiti espliciti: 15 scritture bloccate; search/cerca_wr/stato_wr/riepilogo_wr e
fetch materiali non mappati e restituiscono errore. Nessuna promessa di parita'
completa. Il resto della nota conserva fonti e cronologia: questo stato prevale
sui precedenti blocchi relativi al 403, alla CLI assente o al tunnel ancora mock.

## Obiettivo e confini

Costruire il sostituto MCP Rust di Lia Fibra, conservando le 32 Actions e i 6 helper.
Codice nuovo: `/home/aaa/ftth-lia-mcp`, separato dal gestionale `/home/aaa/fibra`.
Il GPT operativo deve restare funzionante durante la migrazione.
Il lavoro sul gestionale, sui servizi, sulle chiavi e sulla rete non e' autorizzato:
questa cartella di documentazione e' stata richiesta esplicitamente dall'utente.
Nessuna modifica a database, Apache, firewall, Yggdrasil o broker.

## I tre PC: chiarimento dell'utente

| PC | Ruolo e collegamenti |
| --- | --- |
| AAA (`aaa-aaa`) | Backend FTTH e database; comunica con ALEX e ZINGA via Yggdrasil. Host su cui stiamo lavorando. |
| ALEX | Mini PC e ingresso pubblico `servicess.net`; usa Yggdrasil per chiamare le API di AAA. |
| ZINGA | Terzo PC, ospita il broker/relay e ha il proprio collegamento Yggdrasil. |

ALE, che ospita swarm, NON e' ALEX. Nessuna interfaccia swarm verificata o usata.
SSH NON e' il trasporto applicativo e non va richiesto per questa integrazione.
Non assumere che ogni richiesta di ALEX passi da ZINGA: le note contengono anche
una catena target ALEX -> ZINGA -> AAA, non una prova del percorso attivo di ogni API.
L'utente ha richiesto di usare il broker; il percorso specifico del nuovo MCP
va verificato, senza dedurlo solo dal diagramma target o scegliere un bypass.

## Fonte ZINGA fornita dall'utente

Il 2026-10-15 l'utente ha incollato il contenuto di `~/3pc/obsidian/README.md`
dal PC ZINGA. Prima di questo messaggio erano state lette le note locali su AAA,
non questa cartella remota. Non affermare di aver letto file su ZINGA non forniti.

Le prescrizioni della nota sono:

- Il relay ZINGA deve essere esposto SOLO su ZeroTier: `172.23.16.198:6032`.
- ALEX deve autenticarsi verso il relay con `X-Relay-Key`, non con `X-API-Key`.
- AAA deve accettare solo il nodo Yggdrasil di ZINGA DOPO che il relay e' attivo.
- La configurazione Apache Fibra su AAA deve essere rivista per evitare il bypass
  descritto nella nota con la stessa `X-API-Key` verso `127.0.0.1:6030`.

Percorso del relay indicato da questa fonte:

```text
ALEX -- ZeroTier + X-Relay-Key --> ZINGA 172.23.16.198:6032
ZINGA -- Yggdrasil --> AAA backend :6030
```

La raggiungibilita' di ZINGA:6032 via Yggdrasil osservata durante la diagnostica
NON e' il percorso d'ingresso previsto da queste note e non autorizza a usarlo.
La prescrizione "solo ZeroTier" non e' ancora verificata come configurazione attiva.
Nel codice relay gia' fornito, X-API-Key puo' essere inoltrata al backend, ma NON
sostituisce X-Relay-Key per autenticarsi al relay. Le chiavi hanno ruoli distinti.
Il file Apache locale letto su AAA usa come upstream il suo IP Yggdrasil: la
variante con 127.0.0.1 descritta nella nota non e' stata osservata in quel file.

Successivamente l'utente ha fornito anche `zinga-relay-first-step.md` e `mindmap.txt`,
entrambi letti in chat. Non richiederli di nuovo. Il workspace non espone la cartella remota.

### Aggiornamento dalla mappa ZINGA e dal codice AAA

La mappa identifica esplicitamente il file `.env` del progetto `~/3pc` su ZINGA
come configurazione di RELAY_KEY, INTERNAL_KEY e AAA_URL. Questa e' la posizione
indicata dalla fonte; il file remoto non e' stato aperto da questo ambiente.
Non cercare nuovamente queste chiavi nel dotenv di Fibra su AAA.

La mappa riporta health 200, ZINGA -> AAA con Internal-Key 200 JSON e ALEX -> ZINGA
con Relay-Key 200. Sono esiti documentati dall'utente, non test appena ripetuti qui;
non trattare quei controlli come mai effettuati e non chiederli ripetutamente.
La stessa mappa indica come lavoro in corso il ProxyPass di ALEX verso
ZINGA/gestionale/ e il rafforzamento nftables su AAA.

Nuovo riscontro locale del 2026-10-15: `/home/aaa/fibra/.env` contiene anche API_GPTS;
la copia `.env.bak` controllata non la contiene. Nei file `app/utils/security.py`
e `app/utils/auth.py`, il codice locale accetta sia API_KEY sia API_GPTS tramite
header X-API-Key. Questo verifica il ruolo nel codice, non che il processo di
produzione abbia caricato quelle variabili o che ALEX accetti la richiesta.

Per il client MCP la credenziale pertinente e' X-API-Key (API_GPTS e' riconosciuta
dal codice AAA), non la RELAY_KEY interna. Recuperare il valore della RELAY_KEY
non e' un prerequisito della configurazione del client MCP che passa da ALEX.
Nessun valore esposto in chat viene usato per richieste o copiato nei documenti.

### Primo hardening: contenuto ricevuto

- ALEX ZeroTier: `172.23.50.25`; ZINGA ZeroTier: `172.23.16.198`, porta `6032`.
- Bind del relay al solo IP ZeroTier; accesso alla porta consentito solo da ALEX.
- ALEX deve inoltrare `/gestionale/` a ZINGA usando X-Relay-Key e non deve
  iniettare la chiave GPT con RequestHeader set X-API-Key.
- ZINGA inoltra al backend AAA via Yggdrasil; `/fibra/auth` resta su ALEX.
- Traffico umano `/fibra/` e `/tecnico/` separato dal traffico GPT `/gestionale/`.
- Solo dopo i test della catena si restringe AAA al peer Yggdrasil di ZINGA,
  rimuovendo la regola larga 200::/7. Nessuna modifica di hardening eseguita qui.
- La nota riporta Listen 6031 commentato su AAA e un possibile bypass Apache locale:
  informazioni della fonte, non verificate ora come configurazione attiva.

La nota riporta gia' riuscite le chiamate dirette ZINGA -> AAA via Yggdrasil:
health e docs 200; works, technicians, teams, documents e calendar senza slash
finale 307; alcune radici senza endpoint specifico 404. Non significa che tutte
le API siano guaste. I path delle Actions devono restare quelli del contratto.
Questi sono esiti riportati nella nota, non test appena eseguiti dall'assistente.

Il prossimo controllo indicato dalla nota di primo hardening era la catena
ALEX -> ZINGA -> AAA; la mappa fornita successivamente riporta 200 sui due salti.
Non servono altri appunti generici. Un eventuale nuovo controllo del salto relay
deve partire da ALEX, non da AAA, e richiede una ragione diagnostica specifica.
Il testo incollato conteneva un valore di chiave: NON riprodotto, salvato o usato.
Considerarlo esposto; nessuna rotazione automatica, per non interrompere i servizi.

### Controllo di rete proposto in precedenza su ALEX

Comando conservato come riferimento, NON eseguito dall'assistente e non nuovamente
richiesto dopo aver ricevuto la mappa. Da eseguire solo se serve una nuova verifica
diagnostica specifica, nel terminale di ALEX. Legge le
credenziali esistenti con input nascosto, non le mette negli argomenti di curl,
non segue redirect, non fa scritture e stampa solo lo status HTTP.
Non incollare chiavi in chat; comunicare soltanto l'esito del controllo.

```bash
read -rsp 'RELAY_KEY esistente (input nascosto): ' relay_key; printf '\n'
read -rsp 'X-API-Key client esistente (input nascosto): ' api_key; printf '\n'
printf 'X-Relay-Key: %s\nX-API-Key: %s\n' "$relay_key" "$api_key" |
  curl --silent --show-error --noproxy '*' --connect-timeout 5 --max-time 15 \
    --header @- --output /dev/null --write-out 'HTTP %{http_code}\n' \
    'http://172.23.16.198:6032/gestionale/health/'
unset relay_key api_key
```

Un 200 prova la GET health attraverso il relay, non tutti i permessi sulle API.
Un 401/403 richiede distinguere il controllo del relay da quello del backend;
un 502 indica un errore di inoltro secondo il codice relay fornito. Non aggirare
il problema chiamando direttamente AAA o usando Yggdrasil come ingresso a ZINGA.
Questo controllo non verifica l'ingresso HTTPS pubblico di ALEX, che resta un
passaggio separato prima di dichiarare funzionante il collegamento da ChatGPT.

## Indirizzi e contratto conosciuti

- AAA: `200:421e:6385:4a8b:dca7:cfb:197f:e9c3`, backend sulla porta `6030`.
- ALEX: `201:27c:546:5df7:176:95f3:c909:6834`, ingresso HTTPS `servicess.net`.
- ZINGA Yggdrasil: `200:ed19:e37f:e950:589b:3b1f:8e9:cead`.
- Ingresso relay prescritto su ZINGA: SOLO ZeroTier `172.23.16.198:6032`.
- Lo schema Actions locale indica `https://servicess.net/gestionale` e `X-API-Key`.
- Nel codice relay fornito dall'utente, `/gestionale/{path}` verifica `X-Relay-Key`,
  inoltra verso `AAA_URL`, preserva `X-API-Key` e aggiunge `X-Internal-Key`.
- Secondo il modello delle note, ALEX aggiunge la chiave relay e ZINGA quella interna.
  Non acquisire queste chiavi nel MCP per aggirare un ingresso non funzionante.
- La chiave API locale non e' stata dimostrata equivalente a quella del GPT operativo.
- Nessun valore di chiavi, token o password deve essere scritto nelle note o nel codice.

### Ricerca delle configurazioni delle chiavi

Su richiesta esplicita dell'utente, il 2026-10-15 e' stata verificata la presenza
delle variabili, senza stampare o salvare valori:

- `/home/aaa/fibra/.env`: API_KEY presente e valorizzata; RELAY_KEY e INTERNAL_KEY
  assenti o vuote. La API_KEY locale puo' essere caricata automaticamente in memoria:
  non chiedere all'utente di ricordarla o incollarla. Resta non provata la sua
  equivalenza con la chiave client del GPT operativo.
- Verifica successiva: API_GPTS presente e valorizzata nel dotenv attuale,
  assente nel backup .env.bak. API_GPTS e API_KEY sono entrambe riconosciute dal
  codice locale dei due verificatori di X-API-Key; non sono chiavi del relay.
- Nessun riferimento a RELAY_KEY/X-Relay-Key trovato nei file accessibili .conf,
  .service, .env e *.env controllati in /etc/apache2, /etc/systemd/system e
  /home/aaa/fibra. Ricerca limitata alle configurazioni, non ai segreti nelle note.
- Nessuna directory 3pc trovata nella ricerca locale limitata a quattro livelli
  sotto /home/aaa, /mnt e /media. Questo non equivale a una ricerca sul PC ZINGA.
- Il codice relay fornito usa load_dotenv() e la variabile RELAY_KEY: la prima
  posizione da verificare sul PC ZINGA e' ~/3pc/.env, ma il file non e' stato letto
  da questo ambiente. Non dichiarare trovata la RELAY_KEY finche' non verificata.
- Non usare la API_KEY di AAA al posto della RELAY_KEY e non usare il valore
  incollato in chat per aggirare l'assenza della configurazione relay locale.
- Ricerca estesa successiva: riferimenti trovati solo nelle due note locali
  FTTH-GPT-Relay-Architecture e nel presente diario, non in docs, MCP, scripts
  o nelle configurazioni Apache controllate. Le assegnazioni nelle due note
  appartengono agli esempi di configurazione target e ai comandi di esempio;
  non sono state confrontate con la configurazione del relay attivo.
- Nessuna corrispondenza nei file testuali di configurazione/documentazione
  controllati in Backup, backups, Documenti, Scaricati, Scrivania, recovery-backups
  e nelle due cartelle system-recovery di agosto sotto /home/aaa. Archivi compressi
  non estratti o ispezionati; file non leggibili esclusi dal risultato.
- Nessuna assegnazione relay individuata dal controllo mirato dei due file di
  cronologia bash locali. Nessun comando della cronologia o valore segreto stampato.
- Esito aggiornato: API_KEY e API_GPTS locali individuate; posizione di RELAY_KEY
  indicata dalla mappa nel dotenv del progetto 3pc su ZINGA, valore non acquisito.
  Non ripetere la ricerca su AAA e non chiedere di trasferire chiavi interne al MCP.

## Verifiche effettuate il 2026-10-15

| Verifica | Esito e limite dell'evidenza |
| --- | --- |
| Route verso ALEX e ZINGA | Entrambe tramite `ygg0`. |
| ZINGA, GET `/health/` | HTTP 200, `{"status":"relay ok"}`. Prova solo il relay, non il backend. |
| ZINGA, GET `/gestionale/health/` senza chiave | HTTP 401, coerente con il controllo del relay. |
| ALEX, GET HTTPS `/gestionale/health/` pubblico | HTTP 403 HTML, anche con la chiave API locale. |
| Stesso ingresso ALEX via Yggdrasil | HTTP 403 HTML, con e senza chiave API locale; hostname/SNI mantenuti, TLS valido. |
| ChatGPT, Lia Fibra TEST, `stato_api({})` | Chiamata riuscita con `simulated: true`. Nessun dato reale. |

Il 403 osservato su ALEX NON dimostra un guasto del collegamento Yggdrasil ALEX -> AAA.
Non abbiamo verificato le direttive Apache attualmente attive sul PC ALEX.
Non sono state eseguite letture dirette del database o scritture reali.

### File locali di sistema letti, non modificati

`/etc/nftables.conf` include `core.conf`, che include `/etc/nftables/fibra.conf`.
Quest'ultimo autorizza su `ygg0:6030` l'indirizzo esatto di ALEX e una regola
commentata come ZINGA con suffisso `/7`: copre `200::/7`, non il solo host ZINGA.
E' una lettura della configurazione su disco, non una verifica del ruleset caricato.
Nessuna correzione o ricarica del firewall e' stata eseguita.

I file Apache locali `/etc/apache2/sites-enabled/fibra.conf` e
`/etc/apache2/sites-available/fibra.conf` descrivono il VirtualHost di AAA su
porta 6031, con proxy al backend AAA:6030. Non sono la configurazione di ALEX.

## MCP: cosa funziona e cosa no

- SDK Rust ufficiale `rmcp = 3.5.1`; toolchain dedicata nella directory `.tools`.
- `--mock-actions`: 32 Actions piu' 6 helper, stato simulato in memoria.
- `--mock`: sei helper originali. `--dev-read`: solo lettura codice e anteprima diff.
- Traduzione delle 32 Actions in richieste HTTP verificata contro server locali.
- `ProductionAdapter` e `LiveActionsServer` collegati alla CLI e al tunnel di test:
  endpoint GPT HTTPS fisso, GET soltanto, nessun proxy/redirect/retry, errori sanificati.
- Un tentativo di adattatore diretto a ZINGA e' stato rimosso: non e' una soluzione attiva.
- Profilo reale disponibile, stato_api e fetch work_ID implementati. Gli altri
  quattro helper e fetch materiali restano bloccati. Nessun fallback ai mock.
- La ricerca WR non puo' usare il numero WR come ID interno. `getWorks` non espone
  un filtro WR verificato; non inventare un filtro ne' scaricare implicitamente l'archivio.
- Le 15 scritture sono simulate e testate localmente, NON abilitate in produzione.
- Ultimo controllo: 72 test Rust superati, Clippy senza warning; 8 test Python
  superati nella precedente verifica dell'esportatore, non rieseguiti nell'ultimo controllo.

## ChatGPT, processi e pubblicazione

Lia Fibra TEST e' collegata tramite Secure MCP Tunnel al workspace `famiglia`.
Ultima configurazione avviata: MCP live read-only `127.0.0.1:16033/mcp`, salute tunnel `16034`.
I 38 strumenti sono stati verificati in ChatGPT; il GPT operativo non e' stato modificato.
La chiave OpenAI del tunnel e' distinta dalle chiavi FTTH; inserita localmente con
prompt nascosto. Non chiudere inutilmente il processo che la mantiene nell'ambiente.
Non dichiarare i processi ancora sani senza una nuova verifica quando si riprende.

Branch nuovo progetto: `mcp/http-adapter-validation`; ultimo commit noto `c7441da`.
Ci sono modifiche successive non committate all'adattatore e alla documentazione.
Destinazione richiesta: repository privato `zinga0328it/ftth-lia-mcp`.
La precedente verifica di accesso ha restituito `Repository not found`: nessun push.

## Cosa manca per il collegamento reale

1. Collegamento e metadati ChatGPT CONFERMATI con stato_api reale HTTP 200.
  Il 403 e' stato spiegato dalla rotta umana; ingresso GPT e due letture MCP
  reali sono gia' verificati. Non ripetere la ricerca di chiavi relay o firewall.
2. Completare gli helper ancora bloccati solo con mapping API verificato, senza
  scaricamento implicito dell'archivio. 38 nomi non equivale a 38 funzioni operative.
3. Verificare le altre letture reali autorizzate; health/statistiche sono gia' passate.
   Le scritture richiedono verifiche separate su permessi, errori e duplicazioni;
   nessun test che modifichi dati reali senza autorizzazione specifica.

## Ripresa e fonti

Leggere questa nota prima di riprendere; aggiornare risultati e blocchi, non solo
la memoria interna dell'assistente. Le correzioni attuali dell'utente prevalgono
sulle ipotesi precedenti. Distinguere sempre osservazioni, configurazioni target
e comportamento attivo. Non ripetere tentativi SSH o chiedere chiavi in chat.

- [Architettura relay dettagliata](../FTTH-GPT-Relay-Architecture-2.md)
- [Architettura relay](../FTTH-GPT-Relay-Architecture.md)
- [Yggdrasil: problemi storici e risoluzione](../FTTH-CRITICAL-YGGDRASIL-ISSUE.md)
- [Schema Actions locale](../appunti_gpt_s/gpt_s.md) (puo' contenere dati sensibili: non copiarlo integralmente).
- Nel progetto separato: README.md e MIGRATION_REPORT.md per implementazione e test.

### Diario sintetico

- Creati simulatore, contratto 32 Actions, sei helper e test HTTP/MCP.
- Collegata Lia Fibra TEST a ChatGPT tramite tunnel; verificato solo il simulatore.
- Avviata preparazione del collegamento reale dopo richiesta esplicita dell'utente.
- Verificati 403 sull'ingresso ALEX, 200 sulla salute relay ZINGA e 401 senza chiave
  sulla rotta inoltrata. Nessuna di queste prove dimostra una lettura API reale riuscita.
- Letti gli appunti Obsidian e i file locali nftables/Apache senza modificarli.
- Correzione dell'utente: tre PC, Yggdrasil, ALEX chiama AAA; niente SSH e nessuna
  deduzione che tutte le richieste attraversino ZINGA.
- Creata questa cartella su richiesta dell'utente per rendere persistente il lavoro MCP.
- Ricevuto il README Obsidian del PC ZINGA: ingresso relay esclusivamente ZeroTier,
  X-Relay-Key da ALEX, restrizione di AAA dopo attivazione del relay e verifica dei
  bypass Apache. Salvata la distinzione tra queste prescrizioni e le prove di rete.
- Ricevuta e letta la nota zinga-relay-first-step.md: riportata riuscita ZINGA -> AAA;
  prossima prova richiesta dalla nota ALEX -> ZINGA -> AAA. Preparato il controllo
  con credenziali solo in memoria, da eseguire su ALEX. Valore di chiave incollato
  dall'utente escluso dalla documentazione e non utilizzato.
- Ricevuta e letta mindmap.txt: identifica il dotenv di ZINGA con RELAY_KEY,
  INTERNAL_KEY e AAA_URL e riporta 200 su entrambi i salti. Verificati nel codice
  locale AAA i riferimenti ad API_GPTS come alternativa a API_KEY per X-API-Key.
  Correzione: non occorre acquisire RELAY_KEY nel client MCP su AAA.
- Ricevuta configurazione Apache ALEX: identificata /gestionale-gpt/ come rotta
  corretta; /gestionale/ e' legacy umana con allowlist. Corretto il solo MCP.
- Implementati LiveActionsServer e CLI reale con preflight; normalizzata solo la
  health UTC del backend verificato. 72 test Rust, Clippy e Rustfmt superati.
- Collaudo locale MCP reale: 38 strumenti, stato_api e getWeeklyStats 200 senza mock.
- Sostituito solo il simulatore sulla porta 16033; tunnel, GPT operativo e servizi
  invariati. Strumenti ChatGPT aggiornati e stato_api reale verificato da ChatGPT.