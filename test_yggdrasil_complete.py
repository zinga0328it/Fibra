#!/usr/bin/env python3
"""
Script di test completo per PC Alex - FTTH Yggdrasil API
Testa tutti gli endpoint disponibili via Yggdrasil
"""

import requests
import json
import time
from datetime import datetime

# Configurazione
YGGDRASIL_IP = "200:421e:6385:4a8b:dca7:cfb:197f:e9c3"
MAIN_API_PORT = 6030  # API principale per lettura
YGG_API_PORT = None   # API Yggdrasil separata per ingest (da scoprire)

HEADERS = {
    "Content-Type": "application/json",
    "X-KEY": "ftth_ygg_secret_2025"
}

def test_endpoint(name, method, url, data=None, expected_status=200):
    """Testa un singolo endpoint"""
    print(f"\n🔍 Testando {name}...")
    print(f"   URL: {url}")
    print(f"   Method: {method}")

    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=HEADERS, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=HEADERS, timeout=10)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=HEADERS, timeout=10)
        else:
            print(f"   ❌ Metodo {method} non supportato")
            return False

        print(f"   Status: {response.status_code}")

        if response.status_code == expected_status:
            print(f"   ✅ SUCCESSO")
            try:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    print(f"   📊 Risultati: {len(result)} elementi")
                elif isinstance(result, dict):
                    print(f"   📊 Risposta: {json.dumps(result, indent=2)[:200]}...")
                return True
            except:
                print(f"   📄 Risposta: {response.text[:200]}...")
                return True
        else:
            print(f"   ❌ ERRORE - Status: {response.status_code}")
            print(f"   📄 Risposta: {response.text[:200]}...")
            return False

    except requests.exceptions.RequestException as e:
        print(f"   ❌ CONNESSIONE FALLITA: {e}")
        return False

def main():
    print("🚀 FTTH Yggdrasil API Test Suite - PC Alex")
    print("=" * 50)
    print(f"📍 Indirizzo Yggdrasil: [{YGGDRASIL_IP}]")
    print(f"⏰ Timestamp: {datetime.now()}")
    print()

    # Test 1: Health check API principale
    test_endpoint(
        "Health Check (porta 6030)",
        "GET",
        f"http://[{YGGDRASIL_IP}]:{MAIN_API_PORT}/health/"
    )

    # Test 2: Lista lavori (porta 6030)
    test_endpoint(
        "Lista Lavori (porta 6030)",
        "GET",
        f"http://[{YGGDRASIL_IP}]:{MAIN_API_PORT}/works/"
    )

    # Test 3: Statistiche settimanali (porta 6030)
    test_endpoint(
        "Statistiche Settimanali (porta 6030)",
        "GET",
        f"http://[{YGGDRASIL_IP}]:{MAIN_API_PORT}/stats/weekly"
    )

    # Test 4: Prova ingest work su porta 6030 (dovrebbe fallire)
    test_endpoint(
        "Ingest Work su porta 6030 (dovrebbe fallire)",
        "POST",
        f"http://[{YGGDRASIL_IP}]:{MAIN_API_PORT}/ingest/work",
        {
            "numero_wr": f"TEST-{int(time.time())}",
            "nome_cliente": "Test da PC Alex",
            "indirizzo": "Via Test 123",
            "operatore": "PC Alex",
            "tipo_lavoro": "Test Yggdrasil",
            "telefono_cliente": "3330000000",
            "note": "Test automatico"
        },
        expected_status=404  # Aspettiamo 404 perché non esiste su questa porta
    )

    # Test 5: Prova porte alternative per API Yggdrasil
    print("\n🔍 Cercando API Yggdrasil separata...")

    possible_ports = [8600, 6040, 6031, 8000, 8080]
    ygg_api_found = False

    for port in possible_ports:
        print(f"\n🔍 Testando porta {port} per API Yggdrasil...")
        try:
            response = requests.get(f"http://[{YGGDRASIL_IP}]:{port}/health/", headers=HEADERS, timeout=5)
            if response.status_code == 200:
                print(f"   ✅ API Yggdrasil trovata su porta {port}!")
                ygg_api_found = True

                # Test ingest work sulla porta trovata
                test_endpoint(
                    f"Ingest Work (porta {port})",
                    "POST",
                    f"http://[{YGGDRASIL_IP}]:{port}/ingest/work",
                    {
                        "numero_wr": f"TEST-{int(time.time())}",
                        "nome_cliente": "Test da PC Alex",
                        "indirizzo": "Via Test 123",
                        "operatore": "PC Alex",
                        "tipo_lavoro": "Test Yggdrasil",
                        "telefono_cliente": "3330000000",
                        "note": f"Test automatico porta {port}"
                    }
                )
                break
        except:
            print(f"   ❌ Porta {port} non risponde")

    if not ygg_api_found:
        print("\n❌ API Yggdrasil separata non trovata su nessuna porta comune")
        print("   Possibili porte da provare manualmente: 8600, 6040, 6031, 8000, 8080")

    print("\n🏁 Test completato!")
    print(f"📊 API principale (porta {MAIN_API_PORT}): OK")
    print(f"📊 API Yggdrasil separata: {'Trovata' if ygg_api_found else 'Da trovare'}")

if __name__ == "__main__":
    main()