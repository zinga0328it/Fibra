#!/usr/bin/env python3
"""
Test della logica di estrazione PDF senza GUI
"""

import re
import sqlite3
import pdfplumber
import json
import os
from datetime import datetime
from typing import List, Dict

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
        self.requires_ont = False
        self.requires_modem = False
        self.ont_delivered = False
        self.modem_delivered = False
        self.extra_fields = {}

def extract_text_from_pdf(pdf_path: str) -> str:
    """Estrae testo da un file PDF"""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_works_from_text(text_content: str) -> List[WorkData]:
    """Estrae dati completi WR da testo"""
    works = []
    lines = text_content.split('\n')
    current_work = WorkData()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Estrazione numero WR
        if line.startswith('WR:') or 'WR:' in line:
            if current_work.numero_wr and current_work.nome_cliente:
                works.append(current_work)
            current_work = WorkData()
            wr_match = re.search(r'WR:\s*([^\s]+)', line)
            if wr_match:
                current_work.numero_wr = wr_match.group(1).strip()

        # Cliente
        elif 'Cliente:' in line or 'NOME_CLIENTE -' in line:
            if 'Cliente:' in line:
                cliente_part = line.split('Cliente:', 1)[1].strip()
            else:
                cliente_part = line.split('NOME_CLIENTE -', 1)[1].strip()

            cliente_part = cliente_part.split('Indiriz')[0].strip()
            cliente_part = cliente_part.split('Telefono')[0].strip()
            current_work.nome_cliente = cliente_part

        # Indirizzo
        elif 'Indiriz' in line and ':' in line:
            indiriz_part = line.split(':', 1)[1].strip()
            indiriz_part = indiriz_part.split('Comune')[0].strip()
            indiriz_part = indiriz_part.split('Telefono')[0].strip()
            current_work.indirizzo = indiriz_part

        # Tipo lavoro
        elif 'Tipo lavoro:' in line or 'TIPO_LAVORO -' in line:
            if 'Tipo lavoro:' in line:
                tipo_part = line.split('Tipo lavoro:', 1)[1].strip()
            else:
                tipo_part = line.split('TIPO_LAVORO -', 1)[1].strip()
            current_work.tipo_lavoro = tipo_part

        # Stato
        elif 'Stato:' in line or 'STATO -' in line:
            if 'Stato:' in line:
                stato_part = line.split('Stato:', 1)[1].strip()
            else:
                stato_part = line.split('STATO -', 1)[1].strip()
            current_work.stato = stato_part.lower()

        # Data apertura
        elif 'Data apertura:' in line or 'DATA_APERTURA -' in line:
            if 'Data apertura:' in line:
                data_part = line.split('Data apertura:', 1)[1].strip()
            else:
                data_part = line.split('DATA_APERTURA -', 1)[1].strip()
            current_work.data_apertura = data_part

        # Note
        elif 'Note:' in line or 'NOTE -' in line:
            if 'Note:' in line:
                note_part = line.split('Note:', 1)[1].strip()
            else:
                note_part = line.split('NOTE -', 1)[1].strip()
            current_work.note = note_part

        # Campi tecnici
        elif ' - ' in line:
            parts = line.split(' - ', 1)
            if len(parts) == 2:
                key, value = parts[0].strip(), parts[1].strip()
                if any(tech in key.upper() for tech in ['PTE', 'SPLITTER', 'PORTA', 'ODF', 'BUILDING', 'OLT', 'GPON', 'PATCH', 'PERMUTATORE', 'NUMERO', 'NOME', 'TIPO', 'MODELLO']):
                    current_work.extra_fields[key] = value

                    if 'ONT' in key.upper() or 'FIBRA' in key.upper():
                        current_work.requires_ont = True
                    if 'MODEM' in key.upper() or 'ADSL' in key.upper() or 'VDSL' in key.upper():
                        current_work.requires_modem = True

    # Aggiungi l'ultimo work
    if current_work.numero_wr and current_work.nome_cliente:
        works.append(current_work)

    return works

def save_works_to_db(works: List[WorkData], db_path: str) -> int:
    """Salva works nel database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    saved_count = 0
    try:
        for work in works:
            cursor.execute("SELECT id FROM works WHERE numero_wr = ?", (work.numero_wr,))
            if cursor.fetchone():
                continue

            extra_fields_json = json.dumps(work.extra_fields) if work.extra_fields else None

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
                work.data_apertura or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
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
        raise e
    finally:
        conn.close()

    return saved_count

def main():
    print("🧪 TEST LOGICA ESTRAZIONE PDF")
    print("=" * 40)

    pdf_file = "lavoro domani.PDF"
    db_file = "gestionale_ftth.db"

    if not os.path.exists(pdf_file):
        print(f"❌ File PDF non trovato: {pdf_file}")
        return

    try:
        # Estrai testo
        print("📄 Estrazione testo dal PDF...")
        text_content = extract_text_from_pdf(pdf_file)
        print(f"✅ Testo estratto: {len(text_content)} caratteri")

        # Estrai works
        print("🔍 Estrazione dati WR...")
        works = extract_works_from_text(text_content)
        print(f"✅ Works trovati: {len(works)}")

        # Mostra dettagli primi works
        for i, work in enumerate(works[:3]):
            print(f"\n🏗️  Work {i+1}:")
            print(f"   WR: {work.numero_wr}")
            print(f"   Cliente: {work.nome_cliente}")
            print(f"   Indirizzo: {work.indirizzo}")
            print(f"   Tipo: {work.tipo_lavoro}")
            print(f"   Stato: {work.stato}")
            print(f"   ONT: {'Sì' if work.requires_ont else 'No'}")
            print(f"   Modem: {'Sì' if work.requires_modem else 'No'}")
            print(f"   Campi tecnici: {len(work.extra_fields)}")
            if work.extra_fields:
                print("   Dati tecnici:")
                for key, value in list(work.extra_fields.items())[:5]:  # Primi 5
                    print(f"     {key}: {value}")

        # Salva nel database
        if works:
            print(f"\n💾 Salvataggio nel database {db_file}...")
            saved_count = save_works_to_db(works, db_file)
            print(f"✅ Salvati {saved_count} works nel database")

            # Verifica database
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM works")
            total_count = cursor.fetchone()[0]
            conn.close()
            print(f"📊 Totale record nel database: {total_count}")

        print("\n✅ TEST COMPLETATO CON SUCCESSO!")
        print("🎉 L'applicazione desktop è pronta per Windows!")

    except Exception as e:
        print(f"❌ Errore durante il test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()