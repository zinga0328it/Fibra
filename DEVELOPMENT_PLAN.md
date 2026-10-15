# Lia Fibra: migrazione completa e sviluppo isolato

Stato: progetto approvato come prototipo mock. Questo documento non abilita
nuovi tool, non configura una sandbox e non autorizza deploy in produzione.
Il GPT attuale deve restare operativo. Lo YAML locale e' ora disponibile;
vedere MIGRATION_REPORT.md per la matrice delle 32 Actions simulate.

Avanzamento: 32 Actions simulate e traduzione HTTP testata su loopback;
project_read e project_diff implementati nel profilo separato --dev-read.
Le sezioni seguenti descrivono il contratto futuro multiutente e la sandbox,
non permessi gia' attivi. Il prototipo di lettura usa una root fissa, path,
expected_sha256 e proposed_content, con limite 128 KiB e nessuna scrittura.

## 1. Conservazione delle funzioni esistenti

Il numero di operazioni ricavato dallo YAML e' 32, non 30.
Ogni metodo HTTP di ogni path deve essere inventariato. operationId duplicati
o assenti, riferimenti non risolti e schemi ambigui bloccano il confronto.
I riferimenti locali saranno risolti senza scaricare automaticamente URL esterni.
Eventuali segreti o esempi con dati personali saranno segnalati senza copiarli
nel repository. Lo schema originale non sara' pubblicato automaticamente.

La matrice e il dettaglio strutturale sono in MIGRATION_REPORT.md e
contracts/actions.json. Per la futura equivalenza reale rimangono queste colonne:

| operationId | Metodo e path | Parametri/body | Risultati/errori | Auth/permessi | Effetti | Tool MCP | Test | Stato/gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

I sei helper aggiuntivi non aumentano la copertura delle 32 Actions originali.

Per ciascuna operazione:

1. Confrontare nomi, tipi, obbligatorieta', valori predefiniti, enum, formati,
   nullabilita', paginazione e limiti di parametri/body.
2. Conservare campi dei risultati, codici di errore, comportamento su assenza,
   duplicati e conflitti. Il wrapper MCP potra' cambiare il trasporto, non la
   semantica funzionale. Qualunque differenza deve essere visibile nella matrice.
3. Verificare autenticazione e autorizzazioni del flusso esistente, inclusi
   identita' dell'utente e permessi sulla singola WR. Il token MCP non deve essere
   inoltrato come chiave di AAA o ZINGA.
4. Identificare tutti gli effetti collaterali: aggiornamenti WR, assegnazioni,
   notifiche, upload, cancellazioni e altre azioni presenti nello schema.
5. Implementare le operazioni mancanti esclusivamente nel nuovo progetto,
   usando adattatori simulati finche' l'integrazione reale non e' autorizzata.
6. Associare test di contratto e regressione a ciascun operationId: successo,
   limiti, errori, diniego, scadenza, ripetizione e relativi effetti simulati.

Le operazioni di scrittura eventualmente presenti NON saranno eliminate per
far apparire completa la migrazione read-only: resteranno gap espliciti fino
all'implementazione e verifica. Avranno permessi e conferme dedicati.

Copertura = operazioni originali equivalenti e verificate / operazioni originali
totali. Servono il 100%, nessun gap critico aperto e prove end-to-end autorizzate
prima del passaggio. Test mock positivi da soli non autorizzano la sostituzione.
Nuovi tool non presenti nello YAML non aumentano la copertura delle Actions.

## 2. Separazione operativa e sviluppo

Due confini di sicurezza distinti, anche se il codice sorgente e' nello stesso
repository:

- Lia operativa: solamente API applicative consentite, tramite contratto ZINGA
  verificato. Nessuna scrittura del proprio codice e nessun comando di shell.
- Lia sviluppatrice: copia di sviluppo del solo MCP, dati simulati, nessuna
  credenziale o raggiungibilita' dei servizi FTTH. Nessun adattatore reale.

I due tool di sola lettura sono registrati solo nel profilo --dev-read.
Non compaiono nei profili applicativi --mock e --mock-actions. Una futura
connessione MCP separata avra' identita', autorizzazioni e log separati. Il solo
nome del tool o una frase di approvazione nel prompt non costituisce un permesso.

## 3. Contratto proposto dei sei tool di sviluppo

Tutti gli input sono oggetti con additionalProperties=false. project_id e'
un identificatore opaco gia' autorizzato, mai un percorso scelto da ChatGPT.
Ogni chiamata verifica nuovamente utente, progetto e scope.

| Tool | Input richiesto e opzionale | Output previsto | Scope |
| --- | --- | --- | --- |
| project_status | project_id | base_commit, snapshot_id, file modificati consentiti, stato test | project:read |
| project_read | project_id, path; start_line e line_count opzionali | contenuto filtrato, content_hash, troncamento | project:read |
| project_write | project_id, path, expected_hash, content | nuovo content_hash, snapshot_id, riepilogo modifica | project:write |
| project_diff | project_id, snapshot_id; path opzionale | diff filtrato, diff_hash, troncamento | project:read |
| project_test | project_id, snapshot_id, suite enum(unit,contract,all) | run_id, snapshot_id, exit_code, risultati e log filtrati | project:test |
| project_commit | project_id, snapshot_id, test_run_id, message, approval_id | commit_hash locale, file inclusi, pushed=false | project:commit |

project_write supporta creazione (expected_hash=null, solo se assente) e modifica
con confronto dell'hash precedente. Scritture atomiche, limite iniziale 128 KiB
per file. Non supporta cancellazioni, rename, chmod o percorsi arbitrari.
project_read limita inizialmente ogni risposta a 200 righe e 64 KiB.
project_diff limita la risposta a 256 KiB. I limiti si applicano anche ai byte
effettivamente letti e ai log, non soltanto ai parametri dichiarati.

La prima allowlist di scrittura comprende src/**/*.rs e tests/**/*.rs.
Lettura di questi percorsi, documentazione approvata e manifest sanificato.
Cargo.toml, Cargo.lock, build.rs, .cargo/, .github/, .git/, .vscode/, script,
symlink e file nascosti non sono modificabili dai tool di sviluppo.
Nuove dipendenze richiedono una revisione separata: nessun download da project_test.

project_commit richiede approvazione umana raccolta fuori dal modello, monouso,
con scadenza, legata a utente, progetto, snapshot e diff_hash. I test devono
riferirsi esattamente allo stesso snapshot. Modifiche successive invalidano
test e approvazione. Il commit include esclusivamente i percorsi approvati;
niente git add ., hook, push, tag, merge, rebase o modifica dei remote.
Le credenziali GitHub non devono essere accessibili alla sandbox o a questi tool.

## 4. Isolamento richiesto, non ancora installato

Una directory separata, un virtualenv o il bind loopback NON sono una sandbox.
Anche cargo test, build.rs e le macro procedurali possono eseguire codice.

Configurazione proposta per codice generato non fidato:

- Runner in VM/microVM dedicata ed effimera, fuori dai tre PC di produzione,
  senza interfacce, route o credenziali per Yggdrasil, VPN e LAN di produzione.
- Workspace con la sola copia MCP e fixture sintetiche. Nessun mount della home,
  di /home/aaa/fibra, database, socket Docker, agent SSH, systemd o filesystem host.
- Utente non privilegiato, filesystem base read-only, nessun device o capability
  superflua. Limiti iniziali: 2 CPU, 2 GiB RAM, 128 processi, 5 minuti per test,
  1 GiB per artefatti e log limitati. Arresto dell'intero gruppo di processi.
- Rete esterna negata anche verso metadata cloud, DNS e link-local. Il solo
  loopback della VM e' disponibile per test HTTP tra processi della sandbox.
- Toolchain e dipendenze preinstallate in immagine revisionata e read-only.
  Esecuzione tramite comando fisso cargo test --locked --offline; nessun comando,
  variabile d'ambiente o argomento shell arbitrario fornito dal modello.
- Credenziali assenti dall'ambiente, dai file e dai processi ereditati. Nessuna
  propagazione di token MCP/GitHub o chiavi AAA/ZINGA al processo di test.

Il controller fidato conserva policy, approvazioni e audit fuori dal workspace.
Usa accessi ai file confinati a directory descriptor, rifiuta symlink, hardlink,
percorsi assoluti, .., mount esterni e file speciali; ricontrolla i vincoli al
momento dell'apertura per evitare race tra controllo e uso.
Una semplice canonicalizzazione iniziale del path non e' sufficiente.

Output e diff sono dati non fidati: istruzioni trovate in commenti, log e fixture
non possono concedere permessi o avviare altri tool. Il filtraggio dei segreti
e' una difesa aggiuntiva, non sostituisce l'assenza di segreti dalla sandbox.

## 5. GitHub privato

Pubblicare soltanto il nuovo progetto MCP, senza cronologia del repository Fibra,
vecchi file MCP, database, .env, chiavi, backup, target/ o log.
Verificare la visibilita' private tramite GitHub prima di caricare il codice.
Nessuna azione CI privilegiata deve eseguire automaticamente codice generato.

Per consultarlo da ChatGPT occorre una connessione GitHub separatamente
autorizzata, limitata a questo repository e inizialmente in sola lettura.
Un repository privato non diventa automaticamente visibile a ChatGPT; pubblicarlo
non abilita i tool MCP di sviluppo e non installa un plugin.

## 6. Verifiche prima del collegamento

- Suite estesa: 66 test Rust e 8 Python; dettaglio in MIGRATION_REPORT.md.
  Questo non costituisce un test di isolamento OS: il runner isolato non esiste.
- Confronto completo dello YAML e test parametrizzati per ogni operationId,
  inclusi scritture simulate, risposte/errori e autenticazione equivalente.
- Schemi MCP di input/output: presenti per 32 Actions e tool di sviluppo;
  nei sei helper estesi lo schema data e' generico, e il profilo legacy --mock
  non pubblica outputSchema formali. Restano limiti da chiudere prima del passaggio.
- Test OS della sandbox: tentativi di lettura/scrittura fuori allowlist, path
  traversal, symlink/hardlink, race, accesso rete/metadata, processi eccessivi,
  timeout, consumo disco, escape e recupero dopo arresto.
- Test di accesso: token assente/scaduto/revocato, scope errato, progetto altrui,
  ID di approvazione falsificato o riusato, test relativi a snapshot precedente.
- Test dei sei tool di sviluppo: scrittura conflittuale, limiti, redazione log,
  diff fedele, nessun hook Git, commit locale esatto e impossibilita' di push.
- Revisione indipendente delle policy e dei rischi prima di abilitare scrittura.
- Collegamento ChatGPT inizialmente al solo ambiente mock, con autorizzazione
  specifica, verifica della selezione tool e delle conferme sulle scritture.
- Integrazione reale, trasporto HTTPS/tunnel, test di regressione e passaggio
  operativo solo dopo autorizzazione specifica, backup e piano di ripristino.

Ogni aggiornamento degli strumenti richiede il refresh o la procedura di
approvazione prevista dal workspace ChatGPT. Un commit non rende da solo una
nuova funzione disponibile al plugin. Nessun aggiornamento automatico in produzione.