# Lia Fibra MCP

Prototipo Rust indipendente, con API simulate e lettura del solo codice MCP. Non e' ancora
un plugin collegato a ChatGPT e non sostituisce il GPT operativo.

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

- Nessun accesso a database, API reali, file .env o credenziali del gestionale.
- Nessuna modifica a /home/aaa/fibra, inclusa la vecchia cartella MCP.
- Nessun deploy, tunnel, cambio password, modifica Apache/firewall/Yggdrasil.
- Profili --mock e --mock-actions con HTTP solo loopback; --dev-read solo stdio.
- Nessuna dipendenza dal codice Python esistente.
- Dati applicativi mock marcati simulated=true. La WR 103579742 e' una fixture e non
  e' stata letta dalla produzione; il suo stato non descrive una WR reale.

## Funzioni

| Tool | Copertura attuale |
| --- | --- |
| search | Ricerca testuale di lavori e materiali simulati, limite comune 1-20 |
| fetch | Recupero per work_ID o material_ID, mai per numero WR |
| cerca_wr | Ricerca esatta per numero WR stringa, preservando gli zeri iniziali |
| stato_wr | Numero WR e stato, senza aggiornamenti |
| stato_api | Solo salute del backend simulato; produzione esplicitamente non verificata |
| riepilogo_wr | Conteggi dei lavori simulati per stato |

search e fetch riprendono le capacita' di lettura della vecchia prova MCP.
Il contratto di risposta e' nuovo: structuredContent contiene simulated e data.
fetch restituisce un sottoinsieme esplicito dei campi, non telefoni, email,
note, prezzi o tutti i dettagli del vecchio prototipo. La parita' completa con
il GPT esistente non e' ancora stabilita: i contratti locali sono simulati,
ma comportamento reale e autenticazione non sono ancora verificati.
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
```

Le modalita' HTTP espongono /mcp. Se la porta e' occupata il processo termina:
scegliere una porta libera senza fermare servizi esistenti. Non pubblicare questo
endpoint tramite proxy: e' un ambiente mock privo di autenticazione applicativa.

Aprendo questo progetto in VS Code, .vscode/mcp.json configura lia-fibra-mock
su stdio dopo la compilazione. L'avvio resta un'azione locale esplicita.

## Architettura

Client MCP -> rmcp -> sei tool -> ReadBackend -> MockBackend in memoria.

Profilo esteso: client MCP -> rmcp -> 38 tool -> ActionsServer -> stato
transazionale in memoria. Ogni processo ha il proprio stato, condiviso tra le
sessioni di quel processo. Riavviare il processo ripristina le fixture.
Non e' un servizio multiutente autenticato e non deve essere pubblicato.

ReadBackend espone soltanto letture. Non esiste un adattatore di produzione.
HttpTestAdapter implementa la traduzione delle 32 Actions con reqwest, e
HttpActionsTestServer la collega al protocollo MCP nel banco di prova.
I test verificano metodo/path/query/body/header attraverso un server HTTP locale.
Questo componente non ha una modalita' CLI con URL scelto dall'utente, usa solo
una chiave fittizia e rifiuta destinazioni non-loopback, proxy, redirect e retry.
Gli errori di trasporto non provano che una scrittura non sia avvenuta:
non ripetere automaticamente notifiche o creazioni dopo un esito incerto.

Il futuro adattatore dovra' usare il contratto operativo di ZINGA e le API AAA,
senza accesso diretto al database o percorsi di autenticazione alternativi.
La gestione dell'identita' ChatGPT/MCP e' distinta dalle chiavi interne.

Yggdrasil protegge il trasporto, non sostituisce le autorizzazioni applicative
e non annulla il rischio delle credenziali esposte. Le chiavi esistenti non
sono state lette, copiate o modificate da questo progetto.

## Collegamento futuro a ChatGPT

Secure MCP Tunnel e' un'opzione per un collegamento privato, non e' configurato.
Richiede un client dedicato, permessi Platform e associazione al workspace.
HTTPS pubblico e' l'alternativa; non e' stato configurato su ALEX.
Nessuna chiave ZINGA/AAA deve arrivare nei risultati o negli argomenti dei tool.
I dati delle WR restituiti dal futuro servizio arriverebbero invece a ChatGPT.

Riferimenti:
- https://developers.openai.com/apps-sdk/deploy/connect-chatgpt
- https://developers.openai.com/api/docs/guides/secure-mcp-tunnels
- https://github.com/modelcontextprotocol/rust-sdk

## Blocco del passaggio operativo

Lo schema YAML locale e' stato trovato; la copia attiva del GPT resta da confermare.
Non e' stato disattivato alcun GPT, schema o servizio. Non esiste uno script
automatico di disattivazione. I test mock NON autorizzano il passaggio.

Prima di sostituire le Actions devono risultare verificati tutti questi punti:

- [x] Inventario locale: 32 operationId e corrispondenza con i tool MCP.
- [x] Identificate 15 scritture/azioni, simulate e tradotte nei test HTTP;
      nessuna scrittura reale abilitata.
- [ ] Contratto attuale del broker ZINGA, percorso di rete e autorizzazioni.
- [ ] Ricerca per numero WR attraverso API esistenti, distinta dall'ID interno;
      nessuno scaricamento implicito dell'intero archivio per aggirare il limite.
- [ ] Copertura di tutti i campi necessari e dei materiali sulle API effettive.
- [ ] Autenticazione MCP, permessi per utente/WR, scadenze e dinieghi verificati.
- [ ] Timeout, limiti di risposta e rimozione dei segreti dagli errori e dai log.
- [ ] Connessione reale a ChatGPT e prove positive/negative per ogni funzione.
- [ ] Confronto dei risultati reali GPT/MCP su casi concordati e autorizzati.
- [ ] Copia ripristinabile dello schema e della configurazione GPT preesistente.
- [ ] Conferma dei criteri di passaggio e procedura di ripristino verificata.

Solo dopo questi controlli si potra' attuare la sostituzione richiesta,
senza cancellare il vecchio collegamento prima che il nuovo sia verificato.