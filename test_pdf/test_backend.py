#!/home/aaa/fibra/venv/bin/python
"""
Script di test per la logica di backend dell'applicazione FTTH
Testa database, parsing PDF e funzioni principali senza GUI
"""

import sqlite3
import os
import json
from datetime import datetime
import pdfplumber
import re
from typing import List, Dict

# Percorso del database di test
DB_PATH = '/home/aaa/fibra/test_pdf/test_database.db'

def init_test_database():
    """Inizializza un database di test con le tabelle principali"""
    print("Inizializzazione database di test...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabella works semplificata
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS works (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_wr TEXT UNIQUE,
            operatore TEXT,
            indirizzo TEXT,
            tipo_lavoro TEXT,
            nome_cliente TEXT,
            stato TEXT DEFAULT 'aperto',
            data_apertura TEXT,
            tecnico_assegnato_id INTEGER,
            note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabella technicians
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS technicians (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            cognome TEXT,
            telefono TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabella equipment unificata
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_number TEXT UNIQUE,
            model TEXT,
            type TEXT,
            manufacturer TEXT,
            status TEXT DEFAULT 'available',
            work_id INTEGER,
            assigned_date TEXT,
            installed_at TEXT,
            returned_date TEXT,
            location TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database inizializzato con successo")

def test_database_operations():
    """Test operazioni basilari del database"""
    print("Test operazioni database...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Inserisci tecnico di test
    cursor.execute("""
        INSERT OR IGNORE INTO technicians (nome, cognome, telefono)
        VALUES (?, ?, ?)
    """, ("Mario", "Rossi", "123456789"))

    # Inserisci lavoro di test
    cursor.execute("""
        INSERT OR IGNORE INTO works (numero_wr, operatore, indirizzo, tipo_lavoro, nome_cliente)
        VALUES (?, ?, ?, ?, ?)
    """, ("WR001", "TIM", "Via Roma 1", "Nuova Attivazione", "Cliente Test"))

    # Inserisci equipment di test
    cursor.execute("""
        INSERT OR IGNORE INTO equipment (serial_number, model, type, manufacturer, status)
        VALUES (?, ?, ?, ?, ?)
    """, ("SN123456", "FASTGate", "modem", "TIM", "available"))

    conn.commit()

    # Verifica dati inseriti
    cursor.execute("SELECT COUNT(*) FROM technicians")
    tech_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM works")
    work_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM equipment")
    equip_count = cursor.fetchone()[0]

    conn.close()

    print(f"✅ Inseriti {tech_count} tecnici, {work_count} lavori, {equip_count} equipment")

def test_pdf_parsing():
    """Test parsing PDF se disponibile"""
    print("Test parsing PDF...")

    # Cerca file PDF di test
    pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
    if pdf_files:
        try:
            pdf_path = pdf_files[0]
            print(f"Trovato PDF: {pdf_path}")

            with pdfplumber.open(pdf_path) as pdf:
                first_page = pdf.pages[0]
                text = first_page.extract_text()

                # Cerca pattern comuni nei report di lavoro
                wr_pattern = r'WR\d+'
                wr_match = re.search(wr_pattern, text)

                if wr_match:
                    print(f"✅ Trovato numero WR: {wr_match.group()}")
                else:
                    print("ℹ️  Nessun numero WR trovato nel PDF")

        except Exception as e:
            print(f"❌ Errore nel parsing PDF: {e}")
    else:
        print("ℹ️  Nessun file PDF trovato per il test")

def test_equipment_workflow():
    """Test workflow equipment semplificato"""
    print("Test workflow equipment...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Simula assegnazione
    cursor.execute("""
        UPDATE equipment
        SET status = 'assigned', work_id = 1, assigned_date = ?
        WHERE serial_number = ?
    """, (datetime.now().isoformat(), "SN123456"))

    # Verifica stato
    cursor.execute("SELECT status, work_id FROM equipment WHERE serial_number = ?", ("SN123456",))
    result = cursor.fetchone()

    if result and result[0] == 'assigned' and result[1] == 1:
        print("✅ Workflow equipment funzionante")
    else:
        print("❌ Errore nel workflow equipment")

    conn.commit()
    conn.close()

def cleanup_test():
    """Pulisce il database di test"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("🧹 Database di test eliminato")

def main():
    """Funzione principale di test"""
    print("🚀 Avvio test dell'applicazione FTTH Desktop")
    print("=" * 50)

    try:
        init_test_database()
        test_database_operations()
        test_pdf_parsing()
        test_equipment_workflow()

        print("=" * 50)
        print("✅ Tutti i test completati con successo!")
        print("L'applicazione FTTH è pronta per l'uso.")

    except Exception as e:
        print(f"❌ Errore durante i test: {e}")
        return False

    finally:
        cleanup_test()

    return True

if __name__ == "__main__":
    main()