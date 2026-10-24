# Il Quaderno dei Desideri — Lia Adaptive Swarm

## Architettura concordata
- **ChatGPT Progetti:** interfaccia conversazionale, idee, file e istruzioni del progetto.
- **Lia:** interpreta, struttura e chiede esplicita conferma prima di salvare il desiderio.
- **MCP:** tool futuro `desiderio_registra` (write) + `desideri_elenca` e `desiderio_stato` (read), sempre con identita verificata dal gateway.
- **Sciami:** ricevono ticket di desideri, generano proposte e producono report; senza permessi automatici per codice e deploy.
- **Gestionale web:** soltanto la sezione privata del Quaderno, con ricevute, stato, cronologia e approvazioni future.

## Limiti dell'integrazione ChatGPT Progetti
I file, le chat e le istruzioni di un Progetto ChatGPT **non sono un filesystem esposto automaticamente al MCP**. Il tool puo ricevere solo il contenuto che ChatGPT e l'utente hanno effettivamente autorizzato a trasmettere attraverso la chiamata. La copia dei file richiede un flusso dedicato e permessi espliciti. `project_label` e `source_labels` sono soltanto etichette: non corrispondono a verificati ID interni ChatGPT. Non registrare implicitamente chat intere o file.

## Modulo prototipo
- `notebook.py`: modello SQLite degli appunti, ricevute idempotenti, storico e vista HTML privata.
- `test_notebook.py`: 6 regressioni offline su persistenza, separazione tenant/utente, sanitizzazione HTML, deduplicazione.
- I test sono stati eseguiti sul prototipo locale Python 3, **non** sul backend FTTH e **non** nella CI del repository.
- Nessun endpoint pubblico o MCP tool esposto; nessun collegamento Telegram reale o credenziale.

## Sicurezza necessaria prima dell'uso reale
1. Collegare OAuth e/o conferma Telegram a identita lato server, con enrollment verificato; non accettare `AuthenticatedPrincipal` costruito dal browser o dal modello.
2. Limitare la chiave condivisa MCP alle comunicazioni tra servizi: una API key non identifica il singolo utente.
3. Aggiungere un DB transazionale con connessioni gestite, isolamento per tenant e autorizzazioni su ogni query e aggiornamento; non usare SQLite sincrono in shared multiworker production.
4. Esporre GET `/me/wishes`, GET `/me/wishes/{id}` e POST `/me/wishes` solo dopo autentificazione, CSRF, anti-abuso, auditing e autorizzazione.
5. Lo stato iniziale `registrato` significa solo **ricevuto e scritto nel DB**; non implica lavoro degli sciami. Le transizioni di stato vanno implementate separatamente, validate da eventi verificati.
6. Niente codice generato eseguibile sui server FTTH. Anteprima e prove in sandbox isolata, approvazione prima del deploy.
7. Il portale web deve mostrare soltanto i desideri dell'utente autenticato, senza ricavare proprieta dall'ID della richiesta.

## Interfaccia prevista
L'utente parla con Lia nel proprio Progetto ChatGPT, puo caricare PDF o immagini e dire: «Lia, voglio un calendario personalizzato». Lia prepara un titolo e una descrizione, chiede consenso al salvataggio, poi invia via MCP il ticket. La ricevuta con `request_id`, `id` e stato `registrato` ritorna in chat. Il portale mostra la stessa ricevuta nella sezione dedicata, con la storia dei successivi eventi degli sciami.
