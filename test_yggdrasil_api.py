#!/usr/bin/env python3
"""
Esempio di utilizzo dell'API Yggdrasil per aggiungere lavori da PC remoto.
Questo script dimostra come un PC connesso alla rete Yggdrasil può
inviare lavori al database centrale.
"""

import requests
import json
from datetime import datetime

# Configurazione API Yggdrasil
YGGDRASIL_HOST = "200:421e:6385:4a8b:dca7:cfb:197f:e9c3"
YGGDRASIL_PORT = 8600
API_KEY = "ftth_ygg_secret_2025"

BASE_URL = f"http://[{YGGDRASIL_HOST}]:{YGGDRASIL_PORT}"

def send_single_work(work_data):
    """Invia un singolo lavoro all'API"""
    url = f"{BASE_URL}/ingest/work"
    headers = {
        "Content-Type": "application/json",
        "X-KEY": API_KEY
    }

    try:
        response = requests.post(url, json=work_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Errore nell'invio del lavoro: {e}")
        return None

def send_bulk_works(works_list):
    """Invia più lavori contemporaneamente"""
    url = f"{BASE_URL}/ingest/bulk"
    headers = {
        "Content-Type": "application/json",
        "X-KEY": API_KEY
    }

    data = {
        "works": works_list,
        "source": "remote_pc_script"
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Errore nell'invio bulk: {e}")
        return None

# Esempio di utilizzo
if __name__ == "__main__":
    print("🚀 Test API Yggdrasil per gestione lavori FTTH")
    print("=" * 50)

    # Test 1: Invio singolo lavoro
    print("\n📝 Test 1: Invio singolo lavoro")
    work_data = {
        "numero_wr": f"REMOTE-{int(datetime.now().timestamp())}",
        "nome_cliente": "Cliente da PC Remoto",
        "indirizzo": "Via Remota 123, Città Remota",
        "operatore": "Tecnico Remoto",
        "tipo_lavoro": "Installazione FTTH",
        "telefono_cliente": "3330001111",
        "note": "Lavoro inviato da PC remoto via Yggdrasil",
        "extra_fields": {
            "priorita": "alta",
            "origine": "script_remoto",
            "timestamp_invio": datetime.now().isoformat()
        }
    }

    result = send_single_work(work_data)
    if result:
        print(f"✅ Lavoro inviato con successo: {result}")
    else:
        print("❌ Errore nell'invio del lavoro")

    # Test 2: Invio bulk
    print("\n📦 Test 2: Invio bulk di lavori")
    bulk_works = [
        {
            "numero_wr": f"BULK-{int(datetime.now().timestamp())}-1",
            "nome_cliente": "Cliente Bulk 1",
            "indirizzo": "Via Bulk 1, Città 1",
            "operatore": "Tecnico Bulk A",
            "tipo_lavoro": "Manutenzione",
            "telefono_cliente": "3331112222",
            "note": "Primo lavoro del bulk",
            "extra_fields": {"batch_id": "batch_001"}
        },
        {
            "numero_wr": f"BULK-{int(datetime.now().timestamp())}-2",
            "nome_cliente": "Cliente Bulk 2",
            "indirizzo": "Via Bulk 2, Città 2",
            "operatore": "Tecnico Bulk B",
            "tipo_lavoro": "Riparazione",
            "telefono_cliente": "3332223333",
            "note": "Secondo lavoro del bulk",
            "extra_fields": {"batch_id": "batch_001"}
        }
    ]

    result = send_bulk_works(bulk_works)
    if result:
        print(f"✅ Bulk inviato con successo: {result}")
    else:
        print("❌ Errore nell'invio bulk")

    print("\n🎉 Test completati!")
    print("I lavori dovrebbero essere visibili nel database centrale e nell'interfaccia web.")