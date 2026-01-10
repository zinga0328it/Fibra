#!/usr/bin/env python3
"""
Script per inizializzare il database del Gestionale FTTH Desktop
Esegue la stessa inizializzazione dell'applicazione principale
"""

import sqlite3
import os

def init_database():
    """Inizializza il database come fa l'applicazione desktop"""
    db_path = os.path.join(os.path.dirname(__file__), "gestionale_ftth.db")

    print(f"📁 Creazione database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Crea tabella works con tutti i campi
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
            data_chiusura TEXT,
            note TEXT,
            requires_ont BOOLEAN DEFAULT FALSE,
            requires_modem BOOLEAN DEFAULT FALSE,
            ont_delivered BOOLEAN DEFAULT FALSE,
            modem_delivered BOOLEAN DEFAULT FALSE,
            extra_fields TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    # Verifica creazione
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='works'")
    if cursor.fetchone():
        print("✅ Tabella 'works' creata con successo")
    else:
        print("❌ Errore nella creazione della tabella")

    # Inserisci un record di test
    cursor.execute("""
        INSERT OR IGNORE INTO works (
            numero_wr, operatore, indirizzo, tipo_lavoro,
            nome_cliente, stato, data_apertura, note,
            requires_ont, requires_modem, extra_fields
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "DEMO-001",
        "Demo Operatore",
        "Via Demo 123, Città Demo 00100",
        "Attivazione FTTH Demo",
        "Mario Demo",
        "aperto",
        "2026-01-07 10:00:00",
        "Record demo per test funzionamento gestionale",
        True,
        True,
        '{"nome_pte": "PTE-DEMO", "porta_pte": "1/1/1", "nome_splitter_pfs": "SPL-DEMO"}'
    ))

    conn.commit()
    print("✅ Record demo inserito")

    # Conta record totali
    cursor.execute("SELECT COUNT(*) FROM works")
    count = cursor.fetchone()[0]
    print(f"📊 Record totali nel database: {count}")

    conn.close()
    print("✅ Database inizializzato con successo!")

if __name__ == "__main__":
    init_database()