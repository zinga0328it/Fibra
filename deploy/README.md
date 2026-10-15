# Servizi persistenti su AAA

Il MCP e il tunnel usano systemd utente, con `loginctl enable-linger aaa`:
partono al boot senza login e non dipendono dal terminale VS Code.
Le unita' sono installate in `~/.config/systemd/user/` e abilitate sul
`default.target`. `Restart=always` e `RestartSec=10` recuperano le uscite
inattese; nessun limite di tentativi, per tollerare rete/API assenti al boot.
Non vengono ripetute automaticamente le scritture MCP.

## Configurazione

- `lia-fibra-mcp.service`: `/usr/bin/python3 scripts/run_live.py`, legge solo
  `API_GPTS` da `/home/aaa/fibra/.env` e passa `FTTH_API_KEY` al processo figlio.
  Esegue `.tools/runtime/ftth-lia-mcp --live --http 127.0.0.1:16033`.
- La copia runtime e' separata da `target/debug`: una nuova build non cambia
  il programma operativo al successivo riavvio. Aggiornarla solo dopo test,
  backup e arresto del solo MCP, quindi riavviare l'unita'.
- `lia-fibra-tunnel.service`: client v0.0.16, profilo esistente
  `.tools/tunnel-client/profiles/lia-fibra-test.yaml`, stesso tunnel/app ChatGPT.
  Attende il listener MCP fino a 60 secondi; in caso di uscita systemd riprova.
  Readiness su `http://127.0.0.1:16034/readyz`.
- Chiave OpenAI in `~/.config/lia-fibra/tunnel-api-key`, file 600 in cartella
  700, fuori dai repository. Il client riceve soltanto il riferimento `file:`.
  Nessun valore segreto in argomenti, unita', Git o documentazione.
- Il profilo YAML locale deve avere `control_plane.api_key` impostato su
  `file:/home/aaa/.config/lia-fibra/tunnel-api-key`: v0.0.16 risolve i riferimenti
  YAML prima degli override CLI. Non lasciare il precedente riferimento env:
  a una variabile assente. Il profilo precedente e' conservato nel backup locale.

Inserimento iniziale o aggiornamento della chiave, soltanto nel terminale:

```sh
bash /home/aaa/ftth-lia-mcp/scripts/configure-tunnel-key.sh
```

Input nascosto e non salvato nella cronologia shell. Lo script conserva un
backup privato della eventuale chiave precedente e riavvia solo il tunnel.
Non incollare la chiave nella chat. Non genera nuove chiavi o nuovi tunnel.

## Gestione

```sh
systemctl --user status lia-fibra-mcp lia-fibra-tunnel
systemctl --user restart lia-fibra-mcp lia-fibra-tunnel
systemctl --user is-enabled lia-fibra-mcp lia-fibra-tunnel
loginctl show-user aaa -p Linger
curl --fail --silent http://127.0.0.1:16034/readyz
journalctl --user -u lia-fibra-mcp -u lia-fibra-tunnel -n 40
```

Non abilitare log HTTP raw o acquisizione payload. Non condividere log senza
controllo dei dati sensibili. Per annullare solo questa installazione:
`systemctl --user disable --now lia-fibra-tunnel lia-fibra-mcp`.
Non disabilitare linger senza verificare gli altri servizi utente.
Il gestionale `ftth.service`, il bot e il GPT originale non vengono modificati.

## Verifiche del 2026-10-16

Unita' validate con systemd-analyze; launcher provato con chiave sintetica e
chiave assente. MCP installato e attivo, catalogo 38 tool e stato_api reale
HTTP 200, `simulated=false`, `live_read_write`. Linger verificato `yes`.
Crash simulato del solo MCP con SIGKILL: ripartenza automatica verificata,
nuovo PID, active/running e NRestarts=1. Gestionale rimasto attivo.
La chiave OpenAI, inizialmente assente dai contenitori noti, e' stata inserita
privatamente nel terminale. Permessi 600/700 verificati. Corretto il riferimento
nel profilo locale: tunnel active/running e readiness HTTP 200 verificati.
Anche il tunnel e' stato terminato con SIGKILL per prova: riavvio automatico
con nuovo PID, NRestarts=1 e readiness nuovamente HTTP 200.
Nessun reboot del PC o test di scrittura reale eseguito.