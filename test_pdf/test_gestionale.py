#!/usr/bin/env python3
"""
Script di test per verificare il funzionamento del Gestionale FTTH Desktop
"""

import os
import sys
import sqlite3
import json
from datetime import datetime

def test_database():
    """Test creazione e connessione database"""
    print("🔍 Test Database...")

    db_path = "gestionale_ftth.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verifica tabella
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='works'")
        if cursor.fetchone():
            print("✅ Tabella 'works' esistente")
        else:
            print("❌ Tabella 'works' non trovata - ricreare database")

        # Conta record
        cursor.execute("SELECT COUNT(*) FROM works")
        count = cursor.fetchone()[0]
        print(f"📊 Record nel database: {count}")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Errore database: {e}")
        return False

def test_dependencies():
    """Test dipendenze Python"""
    print("\n🔍 Test Dipendenze...")

    dependencies = ['tkinter', 'sqlite3', 'json', 'pdfplumber']
    missing = []

    for dep in dependencies:
        try:
            if dep == 'tkinter':
                import tkinter
                tkinter.Tk().destroy()  # Test che funzioni
            elif dep == 'pdfplumber':
                import pdfplumber
            elif dep == 'sqlite3':
                import sqlite3
            elif dep == 'json':
                import json
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} - MANCANTE")
            missing.append(dep)
        except Exception as e:
            print(f"⚠️  {dep} - Errore: {e}")

    if missing:
        print(f"\n🚨 Dipendenze mancanti: {', '.join(missing)}")
        print("Installa con: pip install " + " ".join(missing))
        return False

    return True

def test_sample_data():
    """Inserisci dati di test"""
    print("\n🔍 Test Dati di Esempio...")

    try:
        conn = sqlite3.connect("gestionale_ftth.db")
        cursor = conn.cursor()

        # Verifica se ci sono già dati
        cursor.execute("SELECT COUNT(*) FROM works")
        count = cursor.fetchone()[0]

        if count == 0:
            # Inserisci lavoro di test
            extra_fields = {
                "nome_pte": "PTE-001",
                "porta_pte": "1/1/1",
                "nome_splitter_pfs": "SPL-001",
                "numero_porta_permutatore": "01",
                "porta_odf": "ODF-01-01",
                "id_building": "EDIFICIO_A"
            }

            cursor.execute("""
                INSERT INTO works (
                    numero_wr, operatore, indirizzo, tipo_lavoro,
                    nome_cliente, stato, data_apertura, note,
                    requires_ont, requires_modem, extra_fields
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "TEST-001",
                "Test Operatore",
                "Via Test 123, Città Test",
                "Attivazione FTTH",
                "Mario Rossi",
                "aperto",
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "Lavoro di test per verifica funzionamento",
                True,
                True,
                json.dumps(extra_fields)
            ))

            conn.commit()
            print("✅ Dati di test inseriti")

            # Verifica inserimento
            cursor.execute("SELECT numero_wr, nome_cliente FROM works WHERE numero_wr = 'TEST-001'")
            row = cursor.fetchone()
            if row:
                print(f"✅ Verifica dati: WR {row[0]} - Cliente {row[1]}")
            else:
                print("❌ Dati di test non trovati")

        else:
            print(f"✅ Database contiene già {count} record")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Errore test dati: {e}")
        return False

def main():
    print("🧪 TEST GESTIONALE FTTH DESKTOP")
    print("=" * 40)

    # Cambia directory se necessario
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print(f"📁 Directory lavoro: {script_dir}")

    # Test sequenziali
    tests = [
        ("Database", test_database),
        ("Dipendenze", test_dependencies),
        ("Dati Esempio", test_sample_data)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n▶️  Avvio test: {test_name}")
        result = test_func()
        results.append(result)

    # Riepilogo
    print("\n" + "=" * 40)
    print("📋 RIEPILOGO TEST")

    passed = sum(results)
    total = len(results)

    if passed == total:
        print("✅ TUTTI I TEST SUPERATI")
        print("🚀 Il gestionale è pronto per l'uso!")
        print("\nAvvia con: avvia_gestionale.bat")
    else:
        print(f"⚠️  {passed}/{total} test passati")
        print("🔧 Risolvi i problemi prima di avviare l'applicazione")

    print("=" * 40)

if __name__ == "__main__":
    main()