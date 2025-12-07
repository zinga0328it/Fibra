1)

Feature: Importazione lavori 
da PDF nel gestionale web 
Descrizione: Al momento il 
gestionale HTML non ha una 
funzione per importare i 
lavori da file PDF, ma i WR 
che riceviamo dagli 
operatori sono solo in 
formato PDF. Questo ci 
costringe a inserire i dati 
manualmente, con perdita di 
tempo ed alta probabilità 
di errore. 🎯 Obiettivo 
Aggiungere al gestionale una 
funzione "Importa WR da PDF" 
che permetta di: 1. Caricare 
uno o più file PDF delle 
bolle di lavoro (WR) 2. 
Effettuare il parsing dei 
dati principali (codice WR, 
indirizzo, data, tecnico, 
stato, note, ecc.) 3. Creare 
un nuovo lavoro oppure 
aggiornare un lavoro 
esistente nel DB 4. Mostrare 
un riepilogo dei dati 
estratti prima del 
salvataggio definitivo 
💻 Proposta di flusso 
(frontend) Aggiungere un 
pulsante nel gestionale web, 
es. in Works: Importa da PDF 
L’utente seleziona uno o 
più PDF Il backend espone 
una route tipo: POST 
/works/import-pdf Il 
sistema: processa il PDF 
restituisce i dati estratti 
salva/aggiorna i record in 
base al codice WR ✅ 
Criteri di accettazione È 
possibile caricare almeno 1 
PDF alla volta (ideale 
supportare multi-upload) Se 
il WR non esiste → viene 
creato un nuovo lavoro Se il 
WR esiste → vengono 
aggiornati i campi (senza 
perdere lo storico)
In caso di errore parsing → log + messaggio chiaro all’utente
