# Lia Fibra MCP

MCP Rust indipendente, con 32 Actions originali e 6 helper collegati alle API reali.
Il profilo --live abilita letture e scritture; --live-read-only resta disponibile.
Lia Fibra TEST usa Secure MCP Tunnel. Non sostituisce il GPT operativo.

Il piano per conservare tutte le Actions e progettare i sei tool di sviluppo
isolati e' in [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md). Sono disponibili solo
project_read e project_diff in anteprima, nel profilo separato --dev-read.
Scrittura, esecuzione e commit tramite MCP restano disabilitati.
La cartella separata e la toolchain dedicata non sono una sandbox OS.

La matrice delle 32 Actions trovate nello YAML locale e il rapporto di verifica
sono in [MIGRATION_REPORT.md](MIGRATION_REPORT.md). Il profilo --mock-actions
espone 38 tool: le 32 Actions piu' i 6 helper, con stato condiviso in memoria.
Sono simulate anche le scritture; nessuna operazione raggiunge la produzione.

## Confini

- I profili mock non accedono alla produzione. I profili live usano le API
      attraverso l'ingresso GPT verificato, mai il database. Credenziale solo in memoria.
      Verificate tutte le 17 Actions GET e i 6 helper con chiamate MCP reali autorizzate.
- Le 15 scritture sono abilitate in --live su richiesta esplicita dell'utente.
      Collaudate localmente, senza modificare record reali o inviare notifiche di prova.
- Eccezione autorizzata il 2026-10-16: correzioni mirate delle API del gestionale
      con backup e quattro regressioni su SQLite temporaneo. Vecchia cartella MCP intatta.
- Tunnel di test autorizzato; nessun cambio password o modifica Apache/firewall/Yggdrasil.
- Profili --mock e --mock-actions con HTTP solo loopback; --dev-read solo stdio.
- Nessuna dipendenza dal codice Python esistente.
- Dati applicativi mock marcati simulated=true. La WR 103579742 e' una fixture e non
  e' stata letta dalla produzione; il suo stato non descrive una WR reale.

## Funzioni

Copertura degli helper nei profili simulati:

| Tool | Copertura mock |
| --- | --- |
| search | Ricerca testuale di lavori e materiali simulati, limite comune 1-20 |
| fetch | Recupero per work_ID o material_ID, mai per numero WR |
| cerca_wr | Ricerca esatta per numero WR stringa, preservando gli zeri iniziali |
| stato_wr | Numero WR e stato, senza aggiornamenti |
| stato_api | Solo salute del backend simulato; produzione esplicitamente non verificata |
| riepilogo_wr | Conteggi dei lavori simulati per stato |

search e fetch riprendono le capacita' di lettura della vecchia prova MCP.
Il contratto di risposta e' nuovo: structuredContent contiene simulated e data.
Nel mock fetch restituisce un sottoinsieme dei campi. Nel profilo reale fetch
legge work_ID, ont_ID o modem_ID, conservando api_id e work_id numerici per le
Actions. material_ID senza tipo e' ambiguo: non identifica un materiale reale.
search legge le tre collezioni API e restituisce al massimo 20 risultati,
senza credenziali degli apparati. cerca_wr/stato_wr confrontano esattamente
numero_wr, preservando gli zeri iniziali e rifiutando i duplicati. riepilogo_wr
conta tutti i lavori restituiti, anche archiviati. L'API /works/ non ha filtro WR:
la lettura dell'elenco e' esplicita nelle descrizioni, limitata a 16 MiB.
I vecchi endpoint OAuth e gli script di configurazione non sono migrati.

E' stato trovato lo schema locale OpenAPI in
/home/aaa/fibra/obsidian/appunti_gpt_s/gpt_s.md, ma non e' verificato che coincida
con quello attualmente caricato in ChatGPT. Il contratto delle 32 Actions e'
esportato in contracts/actions.json senza esempi, descrizioni o credenziali.

## Compilazione e test

Con la toolchain dedicata gia' installata nel progetto, dalla sua directory:

```sh
export RUSTUP_HOME="$PWD/.tools/rustup"
export CARGO_HOME="$PWD/.tools/cargo"
export PATH="$CARGO_HOME/bin:$PATH"
cargo fmt --all -- --check
cargo build --locked
cargo test --locked
cargo clippy --locked --all-targets -- -D warnings
python3 -B -m unittest discover -s scripts -p test_export_contract.py -v
```

Versioni verificate: Rust/Cargo 1.91.1, Rustfmt 1.8.0, Clippy 0.1.91.
.tools e' esclusa da Git: su una nuova copia occorre predisporre una toolchain
di sviluppo equivalente. Nessun aggiornamento della toolchain condivisa,
dei profili di shell o dei servizi. L'esportatore richiede PyYAML, non il server Rust.

I test non richiedono credenziali. Il test HTTP usa una porta loopback libera
assegnata dal sistema e termina il server al completamento. Il test stdio avvia
un processo figlio del solo nuovo eseguibile. Nessuna chiamata alla produzione.

## Avvio locale

```sh
./target/debug/ftth-lia-mcp --mock
./target/debug/ftth-lia-mcp --mock --http 127.0.0.1:16032
./target/debug/ftth-lia-mcp --mock-actions
./target/debug/ftth-lia-mcp --mock-actions --http 127.0.0.1:16033
./target/debug/ftth-lia-mcp --dev-read
./target/debug/ftth-lia-mcp --check-live
./target/debug/ftth-lia-mcp --live-read-only --http 127.0.0.1:16033
./target/debug/ftth-lia-mcp --live --http 127.0.0.1:16033
```

I comandi live richiedono FTTH_API_KEY nell'ambiente, mai negli argomenti.
Il programma non legge automaticamente il dotenv del gestionale. Nel collaudo
autorizzato la variabile e' stata alimentata da API_GPTS della configurazione locale
in memoria. Non scrivere credenziali nel repository. --check-live esegue solo health;
entrambi i profili reali rifiutano l'avvio se la health fallisce. Nessun fallback
ai mock. --live espone tutte le 32 Actions operative e i 6 helper; solo
--live-read-only blocca le 15 scritture prima della rete.

Le modalita' HTTP espongono /mcp. Se la porta e' occupata il processo termina:
scegliere una porta libera senza fermare servizi esistenti. Non pubblicare questo
endpoint senza protezione: i servizi HTTP locali non hanno autenticazione per utente.
Il tunnel autorizzato di Lia Fibra TEST e' distinto da un proxy pubblico generico.

Aprendo questo progetto in VS Code, .vscode/mcp.json configura lia-fibra-mock
su stdio dopo la compilazione. L'avvio resta un'azione locale esplicita.

## Architettura

Client MCP -> rmcp -> sei tool -> ReadBackend -> MockBackend in memoria.

Profilo esteso: client MCP -> rmcp -> 38 tool -> ActionsServer -> stato
transazionale in memoria. Ogni processo ha il proprio stato, condiviso tra le
sessioni di quel processo. Riavviare il processo ripristina le fixture.
Non e' un servizio multiutente autenticato e non deve essere pubblicato.

ReadBackend espone soltanto letture. ProductionAdapter usa esclusivamente
https://servicess.net/gestionale-gpt/, con X-API-Key in memoria, TLS verificato,
nessun proxy/redirect/retry. Le scritture richiedono il profilo esplicito --live.
LiveActionsServer lo espone via MCP.
La configurazione ALEX fornita dall'utente distingue /gestionale/ (umana, allowlist
IP, responsabile del precedente 403) da /gestionale-gpt/ (GPT, proxy verso ZINGA).
ALEX aggiunge X-Relay-Key; ZINGA aggiunge X-Internal-Key verso AAA. Il client MCP
non acquisisce queste chiavi, non contatta direttamente ZINGA/AAA e non usa SSH.
Il proxy ALEX fornito usa Yggdrasil verso ZINGA, a differenza delle precedenti
note di hardening che proponevano ZeroTier: non cambiare rete per uniformare le note.
Verificati via MCP tutti i 17 GET e i 6 helper: HTTP 200, simulated=false,
mode=live_read_write. Nessuna scrittura reale eseguita durante il collaudo.
La sola health normalizza in RFC 3339 il timestamp UTC senza fuso prodotto da
datetime.utcnow().isoformat() nel backend verificato. Le altre date ISO locali
sono validate con ftth-date-time e mantenute senza aggiungere un fuso inventato.
src/live_contract.rs documenta in codice la compatibilita' con OpenAPI effettivo
e route Python lette: nullable, stati apparati, alias tecnico e statistiche annuali.
HttpTestAdapter implementa la traduzione delle 32 Actions con reqwest, e
HttpActionsTestServer la collega al protocollo MCP nel banco di prova.
I test verificano metodo/path/query/body/header attraverso un server HTTP locale.
Questo componente non ha una modalita' CLI con URL scelto dall'utente, usa solo
una chiave fittizia e rifiuta destinazioni non-loopback, proxy, redirect e retry.
Gli errori di trasporto non provano che una scrittura non sia avvenuta:
non ripetere automaticamente notifiche o creazioni dopo un esito incerto.
Le scritture riportano write_outcome: completed, rejected o unknown. Quest'ultimo
richiede verifica dello stato prima di qualsiasi eventuale nuova richiesta.

Correzioni backend autorizzate: updateWork persiste extra_fields, telefono_cliente
(nei metadati), modem_sn e note_chiusura; la creazione manuale salva note nella
colonna corretta e unisce extra_fields ai metadati aggiuntivi. Quattro regressioni
prima fallivano e ora passano: persistenza, omissioni/null e input invalidi.
tecnico_assegnato viene tradotto in tecnico_assegnato_id; alias in conflitto
sono rifiutati. extra_fields resta annidato, senza promuovere metadati a campi
operativi. Servizio API riavviato dall'utente il 2026-10-16 alle 00:58 CEST;
health e OpenAPI live verificati. MCP definitivo ricaricato su 16033: tutti
i 17 GET e i 6 helper nuovamente PASS, HTTP 200 e simulated=false.
Catalogo Lia Fibra TEST aggiornato in ChatGPT: scritture API REALE confermate.
Nessuna scrittura di collaudo eseguita sui dati di produzione.

L'adattatore usa l'ingresso GPT operativo senza accesso diretto al database
o percorsi di autenticazione alternativi.
La gestione dell'identita' ChatGPT/MCP e' distinta dalle chiavi interne.

Yggdrasil protegge il trasporto, non sostituisce le autorizzazioni applicative
e non annulla il rischio delle credenziali esposte. Nessuna chiave esistente
e' stata modificata o copiata nel repository; le chiavi interne non sono state acquisite.

## Collegamento a ChatGPT

Secure MCP Tunnel e' configurato per Lia Fibra TEST nel workspace famiglia.
Il primo collaudo usava simulated=true. Il tunnel ora punta al profilo reale
sulla stessa porta 16033. Aggiornati e verificati i metadati dei 38 strumenti:
descrizioni API REALE e blocchi espliciti, nessuna descrizione SIMULAZIONE LOCALE.
Verificata anche una chiamata stato_api da ChatGPT: HTTP 200, simulated=false,
mode=live_read_only, status=ok. Confermata nell'attivita' della conversazione:
https://chatgpt.com/c/6ad14f6f-b720-83eb-bab7-4c8dbc79988a.
HTTPS pubblico e' l'alternativa; non e' stato configurato su ALEX.
Nessuna chiave ZINGA/AAA deve arrivare nei risultati o negli argomenti dei tool.
I dati delle WR richiesti tramite il servizio vengono restituiti a ChatGPT.

Riferimenti:
- https://developers.openai.com/apps-sdk/deploy/connect-chatgpt
- https://developers.openai.com/api/docs/guides/secure-mcp-tunnels
- https://github.com/modelcontextprotocol/rust-sdk

## Sostituzione del GPT operativo

Lo schema YAML locale e' stato trovato; la copia attiva del GPT resta da confermare.
Non e' stato disattivato alcun GPT, schema o servizio. Non esiste uno script
automatico di disattivazione. I test mock NON autorizzano il passaggio.

Prima di sostituire le Actions devono risultare verificati tutti questi punti:

- [x] Inventario locale: 32 operationId e corrispondenza con i tool MCP.
- [x] 15 scritture/azioni abilitate in --live su richiesta esplicita, testate localmente.
- [x] Ingresso GPT e percorso broker verificati; nessuna chiave interna nel MCP.
- [x] Ricerca WR tramite elenco API, dichiarata e limitata, distinta dall'ID interno.
- [ ] Copertura di tutti i campi necessari e dei materiali sulle API effettive.
- [ ] Autenticazione MCP, permessi per utente/WR, scadenze e dinieghi verificati.
- [x] Timeout, limiti di risposta e rimozione dei segreti dagli errori e dai log.
- [ ] Connessione reale a ChatGPT e prove positive/negative per ogni funzione.
- [ ] Confronto dei risultati reali GPT/MCP su casi concordati e autorizzati.
- [ ] Copia ripristinabile dello schema e della configurazione GPT preesistente.
- [ ] Conferma dei criteri di passaggio e procedura di ripristino verificata.

Solo dopo questi controlli si potra' attuare la sostituzione richiesta,
senza cancellare il vecchio collegamento prima che il nuovo sia verificato.