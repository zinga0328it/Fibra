# Continuita' del lavoro

- Prima di modificare l'integrazione Lia Fibra/MCP, leggere
  [stato e diario operativo](../obsidian/MCP-Lia-Fibra/STATO-E-DIARIO.md).
  La sezione corrente prevale sulla cronologia: non riproporre domande su
  architettura, autorizzazioni e decisioni gia' documentate. Verificare soltanto
  i fatti variabili necessari alla richiesta, come processi e stato Git.
- Il MCP corrente e' Rust in /home/aaa/ftth-lia-mcp, repository separato.
  MCP/ in questo repository e' un esperimento precedente, non il deployment attivo.
  Leggere anche le istruzioni del repository Rust quando si interviene li'.
- AAA, ALEX e ZINGA sono macchine distinte; ALE non e' ALEX. Per questa
  integrazione niente SSH e nessuna modifica a rete, firewall, broker o chiavi.
  L'ingresso API verificato e' https://servicess.net/gestionale-gpt/.
- Non spegnere il GPT originale. Le scritture MCP sono abilitate, ma i test
  non devono modificare dati reali o inviare notifiche. Usare test isolati.
- Conservare le modifiche preesistenti e fare backup prima degli interventi.
  Non includere in Git segreti, database, backup, log o dati dei clienti.
  Non leggere o stampare credenziali per ricostruire informazioni gia' note.
- Aggiornare il diario dopo interventi significativi con esiti verificati,
  limiti, test e passi ancora necessari. Distinguere sempre codice pronto,
  codice attivo e comportamento realmente collaudato.