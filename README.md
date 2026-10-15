# Lia Fibra MCP

Prototipo Rust indipendente, esclusivamente con dati simulati. Non e' ancora
un plugin collegato a ChatGPT e non sostituisce il GPT operativo.

Il piano per conservare tutte le Actions e progettare i sei tool di sviluppo
isolati e' in [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md). Questi ultimi non sono
ancora implementati o abilitati. La cartella separata non e' una sandbox OS.

## Confini

- Nessun accesso a database, API, file .env o credenziali del gestionale.
- Nessuna modifica a /home/aaa/fibra, inclusa la vecchia cartella MCP.
- Nessun deploy, tunnel, cambio password, modifica Apache/firewall/Yggdrasil.
- Avvio consentito soltanto con --mock; HTTP soltanto su indirizzo loopback.
- Nessuna dipendenza dal codice Python esistente.
- Dati restituiti marcati simulated=true. La WR 103579742 e' una fixture e non
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
il GPT esistente non e' ancora stabilita: manca il suo schema Actions.
I vecchi endpoint OAuth e gli script di configurazione non sono migrati.

## Compilazione e test

Con Cargo nel PATH:

```sh
cargo build --locked
cargo test --locked
cargo clippy --locked --all-targets -- -D warnings
```

Sull'host corrente la toolchain gia' presente e' in
/home/aaa/.rustup/toolchains/stable-x86_64-unknown-linux-gnu/bin.
Se necessario, aggiungere temporaneamente questa directory al PATH del terminale;
non serve modificare profili di shell o servizi.

I test non richiedono credenziali. Il test HTTP usa una porta loopback libera
assegnata dal sistema e termina il server al completamento. Il test stdio avvia
un processo figlio del solo nuovo eseguibile. Nessuna chiamata alla produzione.

## Avvio locale

```sh
./target/debug/ftth-lia-mcp --mock
./target/debug/ftth-lia-mcp --mock --http 127.0.0.1:16032
```

La seconda modalita' espone /mcp. Se la porta e' occupata il processo termina:
scegliere una porta libera senza fermare servizi esistenti. Non pubblicare questo
endpoint tramite proxy: e' un ambiente mock privo di autenticazione applicativa.

Aprendo questo progetto in VS Code, .vscode/mcp.json configura lia-fibra-mock
su stdio dopo la compilazione. L'avvio resta un'azione locale esplicita.

## Architettura

Client MCP -> rmcp -> sei tool -> ReadBackend -> MockBackend in memoria.

ReadBackend espone soltanto letture. Non esiste un adattatore di produzione.
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

Lo schema YAML e' nel configuratore del GPT e sara' fornito dall'utente.
Non e' stato disattivato alcun GPT, schema o servizio. Non esiste uno script
automatico di disattivazione. I test mock NON autorizzano il passaggio.

Prima di sostituire le Actions devono risultare verificati tutti questi punti:

- [ ] Inventario delle operationId dello YAML e corrispondenza con i tool MCP.
- [ ] Eventuali azioni di scrittura identificate e trattate separatamente;
      il presente prototipo non le supporta e non puo' sostituirle.
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