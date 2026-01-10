from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
import re
import sqlite3
from typing import List, Dict
import os
from datetime import datetime
import pdfplumber

app = FastAPI(title="PDF/Text Client Upload Test")

# Database path (database ISOLATO per test)
DB_PATH = "/home/aaa/fibra/test_pdf/test_pdf.db"

class WorkData:
    def __init__(self):
        self.numero_wr = None
        self.operatore = None
        self.indirizzo = None
        self.nome_cliente = None
        self.tipo_lavoro = None
        self.stato = None
        self.data_apertura = None
        self.note = None
        # Campi extra per ONT/modem
        self.requires_ont = False
        self.requires_modem = False
        self.ont_delivered = False
        self.modem_delivered = False
        # Dizionario per campi aggiuntivi da salvare in extra_fields JSON
        self.extra_fields = {}

class ClientData:
    def __init__(self, nome: str, cognome: str, indirizzo: str, telefono: str = None):
        self.nome = nome
        self.cognome = cognome
        self.indirizzo = indirizzo
        self.telefono = telefono

def extract_text_from_pdf(pdf_path: str) -> str:
    """Estrae testo da un file PDF"""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Errore nell'estrazione testo PDF: {str(e)}")

def extract_clients_from_text(text_content: str) -> List[ClientData]:
    """Estrae dati clienti da testo WR (Work Report)"""
    clients = []

    # Suddividi in righe
    lines = text_content.split('\n')

    current_client = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Pattern per file WR reali
        # Formato 1: "NOME_CLIENTE - ANNALISA" (spazio trattino spazio)
        if ' - ' in line:
            parts = line.split(' - ', 1)
            if len(parts) == 2:
                key, value = parts[0].strip(), parts[1].strip()
                if key == 'NOME_CLIENTE':
                    current_client['nome'] = value
                elif key == 'COGNOME_CLIENTE':
                    # Se è una società (contiene SRL, SPA, etc.), trattala come nome completo
                    if any(company in value.upper() for company in ['SRL', 'SPA', 'SNC', 'SS']):
                        current_client['nome'] = value
                        current_client['cognome'] = ''
                    else:
                        current_client['cognome'] = value
                elif key == 'INDIRIZZO':
                    # Solo se non abbiamo già un indirizzo completo
                    if 'indirizzo' not in current_client:
                        current_client['indirizzo'] = value
                elif key == 'RECAPITO_TELEFONICO_CLIENTE_1':
                    current_client['telefono'] = value
                elif key == 'NUMERO_CIVICO':
                    # Aggiungi numero civico all'indirizzo se presente
                    if 'indirizzo' in current_client:
                        current_client['indirizzo'] += f" {value}"

        # Formato 2: "Cliente: SORACI GIULIANA" (due punti)
        elif ':' in line and not line.startswith('Stampata:'):
            parts = line.split(':', 1)
            if len(parts) == 2:
                key, value = parts[0].strip(), parts[1].strip()
                if key.lower() == 'cliente':
                    # Controlla se c'è anche l'indirizzo nella stessa riga
                    value_lower = value.lower()
                    if 'indiriz.' in value_lower:
                        # Formato: "Cliente: NOME Indiriz.: VIA NUMERO"
                        try:
                            # Split case-insensitive
                            indiriz_index = value_lower.find('indiriz.')
                            cliente_part = value[:indiriz_index].strip()
                            indiriz_part = value[indiriz_index + len('indiriz.'):].strip()
                            # Rimuovi "comune:" e tutto dopo
                            indiriz_part = indiriz_part.split('comune:')[0].strip()
                            
                            # Estrai nome cliente
                            name_parts = cliente_part.split()
                            if len(name_parts) >= 2:
                                if any(company in name_parts[-1].upper() for company in ['SRL', 'SPA', 'SNC', 'SS']):
                                    current_client['nome'] = cliente_part
                                    current_client['cognome'] = ''
                                else:
                                    current_client['nome'] = name_parts[0]
                                    current_client['cognome'] = ' '.join(name_parts[1:])
                            
                            # Estrai indirizzo completo
                            indiriz_part = indiriz_part.lstrip(':').strip()
                            current_client['indirizzo'] = indiriz_part
                        except Exception as e:
                            print(f"Errore parsing indirizzo: {e}")
                            # Fallback se il parsing fallisce
                            name_parts = value.split()
                            if len(name_parts) >= 2:
                                if any(company in name_parts[-1].upper() for company in ['SRL', 'SPA', 'SNC', 'SS']):
                                    current_client['nome'] = value
                                    current_client['cognome'] = ''
                                else:
                                    current_client['nome'] = name_parts[0]
                                    current_client['cognome'] = ' '.join(name_parts[1:])
                    else:
                        # Solo cliente senza indirizzo
                        name_parts = value.split()
                        if len(name_parts) >= 2:
                            if any(company in name_parts[-1].upper() for company in ['SRL', 'SPA', 'SNC', 'SS']):
                                current_client['nome'] = value
                                current_client['cognome'] = ''
                            else:
                                current_client['nome'] = name_parts[0]
                                current_client['cognome'] = ' '.join(name_parts[1:])
                elif key.lower() == 'indiriz.':
                    current_client['indirizzo'] = value
                elif key.lower() == 'telefono reclamante':
                    # Rimuovi il trattino finale se presente
                    current_client['telefono'] = value.rstrip(' -')

        # Se abbiamo tutti i campi obbligatori, crea il cliente
        # Per società, cognome può essere vuoto
        if 'nome' in current_client and 'indirizzo' in current_client:
            # Controlla se esiste già un cliente simile
            existing_client = None
            current_nome = current_client['nome']
            current_cognome = current_client.get('cognome', '')
            
            for client in clients:
                # Confronta in modo flessibile (nome cognome vs cognome nome)
                client_nome_completo = f'{client.nome} {client.cognome}'.strip().lower()
                current_nome_completo = f'{current_nome} {current_cognome}'.strip().lower()
                
                # Controlla se sono la stessa persona (anche se invertiti)
                if (client_nome_completo == current_nome_completo or 
                    client_nome_completo == f'{current_cognome} {current_nome}'.lower()):
                    existing_client = client
                    break
            
            if existing_client:
                # Aggiorna il cliente esistente con nuove informazioni
                if current_client.get('telefono') and not existing_client.telefono:
                    existing_client.telefono = current_client['telefono']
                # Se il nuovo indirizzo è più completo, usalo
                if len(current_client['indirizzo']) > len(existing_client.indirizzo):
                    existing_client.indirizzo = current_client['indirizzo']
            else:
                # Crea nuovo cliente
                cognome = current_client.get('cognome', '')
                clients.append(ClientData(
                    nome=current_client['nome'],
                    cognome=cognome,
                    indirizzo=current_client['indirizzo'],
                    telefono=current_client.get('telefono')
                ))
            current_client = {}  # Reset per prossimo cliente

    return clients

def save_clients_to_db(clients: List[ClientData]) -> int:
    """Salva clienti nel database"""
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="Database non trovato")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    saved_count = 0
    try:
        for client in clients:
            # Inserisci come work con tipo "cliente_pdf"
            cursor.execute("""
                INSERT INTO works (
                    numero_wr, operatore, indirizzo, tipo_lavoro,
                    nome_cliente, stato, data_apertura, note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"PDF_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{saved_count}",
                "Cliente da PDF",
                client.indirizzo,
                "Installazione FTTH",
                f"{client.nome} {client.cognome}",
                "aperto",
                datetime.now(),
                f"Cliente caricato da PDF - Tel: {client.telefono or 'N/A'}"
            ))
            saved_count += 1

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Errore database: {str(e)}")
    finally:
        conn.close()

    return saved_count

def save_works_to_db(works: List[WorkData]) -> int:
    """Salva works completi nel database"""
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="Database non trovato")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    saved_count = 0
    try:
        for work in works:
            # Converti extra_fields in JSON
            import json
            extra_fields_json = json.dumps(work.extra_fields) if work.extra_fields else None

            # Inserisci work completo
            cursor.execute("""
                INSERT INTO works (
                    numero_wr, operatore, indirizzo, tipo_lavoro,
                    nome_cliente, stato, data_apertura, note,
                    requires_ont, requires_modem, ont_delivered, modem_delivered,
                    extra_fields
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                work.numero_wr,
                work.operatore or "Da PDF WR",
                work.indirizzo,
                work.tipo_lavoro or "Installazione FTTH",
                work.nome_cliente,
                work.stato or "aperto",
                work.data_apertura or datetime.now(),
                work.note,
                work.requires_ont,
                work.requires_modem,
                work.ont_delivered,
                work.modem_delivered,
                extra_fields_json
            ))
            saved_count += 1

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Errore database: {str(e)}")
    finally:
        conn.close()

    return saved_count

def extract_works_from_text(text_content: str) -> List[WorkData]:
    """Estrae dati completi WR da testo"""
    works = []

    # Suddividi in righe
    lines = text_content.split('\n')

    current_work = WorkData()
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Estrazione numero WR
        if line.startswith('WR:'):
            # Se abbiamo già un work completo, salvalo
            if current_work.numero_wr and current_work.nome_cliente:
                works.append(current_work)
            current_work = WorkData()
            current_work.numero_wr = line.split(':', 1)[1].strip()

        # Pattern per file WR reali
        elif ' - ' in line:
            parts = line.split(' - ', 1)
            if len(parts) == 2:
                key, value = parts[0].strip(), parts[1].strip()
                
                # Mappatura campi principali
                if key == 'NOME_CLIENTE':
                    current_work.extra_fields['nome_cliente'] = value
                elif key == 'COGNOME_CLIENTE':
                    current_work.extra_fields['cognome_cliente'] = value
                    # Crea nome completo
                    nome = current_work.extra_fields.get('nome_cliente', '')
                    cognome = value
                    if nome and cognome:
                        current_work.nome_cliente = f"{nome} {cognome}"
                elif key == 'INDIRIZZO':
                    current_work.indirizzo = value
                elif key == 'RECAPITO_TELEFONICO_CLIENTE_1':
                    current_work.extra_fields['telefono'] = value
                elif key == 'PROVINCIA':
                    current_work.extra_fields['provincia'] = value
                elif key == 'COMUNE':
                    current_work.extra_fields['comune'] = value
                elif key == 'CODICE_ORDINE_OLO':
                    current_work.extra_fields['codice_ordine_olo'] = value
                elif key == 'IDENTIFICATIVO_DEL_POP':
                    current_work.extra_fields['pop'] = value
                elif key == 'GPON_ATTESTAZIONE':
                    current_work.extra_fields['gpon_attestazione'] = value
                elif key == 'ID_RISORSA':
                    current_work.extra_fields['id_risorsa'] = value
                elif key == 'NOTE_INTERNE':
                    current_work.note = value
                elif key == 'INIZIO_APPUNTAMENTO':
                    current_work.extra_fields['inizio_appuntamento'] = value
                elif key == 'FINE_APPUNTAMENTO':
                    current_work.extra_fields['fine_appuntamento'] = value
                elif key == 'TIPO_INSTALLAZIONE':
                    current_work.extra_fields['tipo_installazione'] = value
                elif key == 'OLT_NAME':
                    current_work.extra_fields['olt_name'] = value
                elif key == 'OLT_PORT':
                    current_work.extra_fields['olt_port'] = value
                elif key == 'ID_EGON':
                    current_work.extra_fields['id_egon'] = value
                elif key == 'CONSEGNA_APPARATO':
                    current_work.extra_fields['consegna_apparato'] = value
                elif key == 'TIPOLOGIA_APPARATO':
                    if 'ONT' in value.upper() or 'CPE' in value.upper():
                        current_work.requires_ont = True
                    if 'MODEM' in value.upper() or 'CPE' in value.upper():
                        current_work.requires_modem = True
                elif key == 'OLT_ODF_PORT':
                    current_work.extra_fields['olt_odf_port'] = value
                elif key == 'NOME_SPLITTER_PFS':
                    current_work.extra_fields['nome_splitter_pfs'] = value
                elif key == 'PORTA_DI_USCITA_SPLITTER_PFS':
                    current_work.extra_fields['porta_di_uscita_splitter_pfs'] = value
                elif key == 'NOME_SPLITTER_PFP':
                    current_work.extra_fields['nome_splitter_pfp'] = value
                elif key == 'PORTA_DI_USCITA_SPLITTER_PFP':
                    current_work.extra_fields['porta_di_uscita_splitter_pfp'] = value
                elif key == 'NUMERO_PORTA_PERMUTATORE':
                    current_work.extra_fields['numero_porta_permutatore'] = value
                elif key == 'NOME_PTE':
                    current_work.extra_fields['nome_pte'] = value
                elif key == 'PORTA_PTE':
                    current_work.extra_fields['porta_pte'] = value
                elif key == 'PORTA_ODF':
                    current_work.extra_fields['porta_odf'] = value
                elif key == 'PORTA_DEL_PATCH_PANEL':
                    current_work.extra_fields['porta_del_patch_panel'] = value
                elif key == 'ID_BUILDING':
                    current_work.extra_fields['id_building'] = value
                elif key == 'NUMERO_UI_BUILDING':
                    current_work.extra_fields['numero_ui_building'] = value
                elif key == 'PRIMA_RISORSA_BUILDING':
                    current_work.extra_fields['prima_risorsa_building'] = value
                elif key == 'IMPIANTO_DI_TERMINAZIONE':
                    current_work.extra_fields['impianto_di_terminazione'] = value

        # Formato alternativo con ":"
        elif ':' in line and not line.startswith('Stampata:'):
            parts = line.split(':', 1)
            if len(parts) == 2:
                key, value = parts[0].strip(), parts[1].strip()
                
                if key.lower() == 'cliente':
                    # Estrai nome completo
                    if 'indiriz.' in value.lower():
                        cliente_part = value.split('indiriz.')[0].strip()
                        current_work.nome_cliente = cliente_part
                        current_work.extra_fields['nome_completo'] = cliente_part
                elif key.lower() == 'tipo':
                    current_work.tipo_lavoro = value
                elif key.lower() == 'stato wr':
                    current_work.stato = value.lower()
                elif key.lower() == 'data dispaccio':
                    current_work.data_apertura = value
                elif key.lower() == 'job type':
                    current_work.extra_fields['job_type'] = value
                elif key.lower() == 'descrizione olo':
                    current_work.extra_fields['descrizione_olo'] = value
                elif key.lower() == 'centrale':
                    current_work.extra_fields['centrale'] = value
                elif key.lower() == 'sq.':
                    current_work.operatore = value.split('-')[0].strip() if '-' in value else value
                elif key.lower() == 'ass.':
                    current_work.extra_fields['assegnatario'] = value

    # Aggiungi l'ultimo work se completo
    if current_work.numero_wr and current_work.nome_cliente:
        works.append(current_work)

    return works

@app.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """Carica file (PDF o TXT) e estrae clienti"""
    if not file.filename.lower().endswith(('.pdf', '.txt')):
        raise HTTPException(status_code=400, detail="Solo file PDF o TXT sono accettati")

    # Salva temporaneamente il file
    temp_path = f"/tmp/{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Leggi contenuto del file
        if file.filename.lower().endswith('.pdf'):
            # Estrai testo dal PDF
            text_content = extract_text_from_pdf(temp_path)
        else:
            # Leggi file di testo
            try:
                with open(temp_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
            except UnicodeDecodeError:
                # Fallback per encoding diversi
                with open(temp_path, 'r', encoding='latin-1') as f:
                    text_content = f.read()

        # Estrai clienti
        clients = extract_clients_from_text(text_content)

        if not clients:
            return {"message": "Nessun cliente trovato nel file", "clients": []}

        # Salva nel database
        saved_count = save_clients_to_db(clients)

        return {
            "message": f"Caricato file con {len(clients)} clienti, salvati {saved_count} nel database",
            "clients": [
                {
                    "nome": c.nome,
                    "cognome": c.cognome,
                    "indirizzo": c.indirizzo,
                    "telefono": c.telefono
                } for c in clients
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore processamento: {str(e)}")
    finally:
        # Pulisci file temporaneo
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/", response_class=HTMLResponse)
async def get_upload_page():
    """Pagina HTML per upload PDF"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Upload PDF Clienti - Test</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .upload-form { border: 2px dashed #ccc; padding: 20px; text-align: center; }
            input[type="file"] { margin: 10px 0; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; }
            button:hover { background: #0056b3; }
            .result { margin-top: 20px; padding: 10px; background: #f8f9fa; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>🧪 Test Upload PDF Clienti</h1>
        <p>Carica un PDF o TXT con dati clienti nel formato:</p>
        <pre>
Nome: Mario
Cognome: Rossi
Indirizzo: Via Roma 123, Roma
Telefono: 1234567890

Nome: Luca
Cognome: Verdi
Indirizzo: Via Milano 456, Milano
        </pre>

        <form class="upload-form" id="uploadForm">
            <input type="file" id="uploadFile" accept=".pdf,.txt" required>
            <br><br>
            <button type="submit">Carica File e Salva Clienti</button>
        </form>

        <div id="result" class="result" style="display: none;"></div>

        <script>
            document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                e.preventDefault();

                const fileInput = document.getElementById('uploadFile');
                const resultDiv = document.getElementById('result');

                if (!fileInput.files[0]) {
                    resultDiv.style.display = 'block';
                    resultDiv.innerHTML = '<p style="color: red;">Seleziona un file PDF o TXT</p>';
                    return;
                }

                const formData = new FormData();
                formData.append('file', fileInput.files[0]);

                try {
                    const response = await fetch('/upload-file', {
                        method: 'POST',
                        body: formData
                    });

                    const data = await response.json();

                    resultDiv.style.display = 'block';
                    if (response.ok) {
                        resultDiv.innerHTML = `
                            <h3>✅ Successo!</h3>
                            <p>${data.message}</p>
                            <h4>Works estratti:</h4>
                            <div style="max-height: 400px; overflow-y: auto;">
                                ${data.works.map(w => `
                                    <div style="border: 1px solid #ccc; margin: 10px 0; padding: 10px; border-radius: 5px;">
                                        <strong>WR ${w.numero_wr}</strong> - ${w.nome_cliente}<br>
                                        <strong>Indirizzo:</strong> ${w.indirizzo}<br>
                                        <strong>Tipo:</strong> ${w.tipo_lavoro} | <strong>Stato:</strong> ${w.stato}<br>
                                        <strong>Operatore:</strong> ${w.operatore} | <strong>Data:</strong> ${w.data_apertura}<br>
                                        ${w.note ? `<strong>Note:</strong> ${w.note}<br>` : ''}
                                        ${w.requires_ont ? '<span style="color: blue;">📡 Richiede ONT</span> ' : ''}
                                        ${w.requires_modem ? '<span style="color: green;">📶 Richiede Modem</span>' : ''}
                                        ${Object.keys(w.extra_fields).length > 0 ? `<br><strong>Dettagli aggiuntivi:</strong> ${Object.entries(w.extra_fields).map(([k,v]) => `${k}: ${v}`).join(', ')}` : ''}
                                    </div>
                                `).join('')}
                            </div>
                        `;
                    } else {
                        resultDiv.innerHTML = `<p style="color: red;">Errore: ${data.detail}</p>`;
                    }
                } catch (error) {
                    resultDiv.style.display = 'block';
                    resultDiv.innerHTML = `<p style="color: red;">Errore di rete: ${error.message}</p>`;
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    print("Avvio server su http://127.0.0.1:8001")
    try:
        # Proviamo con parametri diversi
        uvicorn.run(
            "pdf_client_upload:app", 
            host="127.0.0.1", 
            port=8001, 
            reload=False,
            log_level="info"
        )
    except Exception as e:
        print(f"Errore avvio server: {e}")
        import traceback
        traceback.print_exc()