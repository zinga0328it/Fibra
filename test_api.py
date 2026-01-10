#!/usr/bin/env python3
import requests
import json
import time

# Test dell'API FTTH sulla porta 6030
BASE_URL = "http://[200:421e:6385:4a8b:dca7:cfb:197f:e9c3]:6030"
API_KEY = "JHzxUzdAK8LJ33Y50MDgLf5E62flYset4MYA6ELpXpU="

def test_endpoint(name, method, url, data=None, headers=None, requires_auth=False):
    print(f"\n🧪 Testing {name}...")
    if headers is None:
        headers = {}
    
    if requires_auth:
        headers["X-API-Key"] = API_KEY
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == 'POST':
            headers["Content-Type"] = "application/json"
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method.upper() == 'PUT':
            headers["Content-Type"] = "application/json"
            response = requests.put(url, json=data, headers=headers, timeout=10)
        else:
            print(f"❌ Unsupported method: {method}")
            return False

        print(f"Status: {response.status_code}")
        if response.status_code < 400:
            print("✅ SUCCESS")
            if response.text:
                try:
                    print(f"Response: {json.dumps(response.json(), indent=2)[:500]}...")
                except:
                    print(f"Response: {response.text[:500]}...")
            return True
        else:
            print("❌ FAILED")
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    print("🚀 Starting FTTH API Tests on port 6030")
    print(f"Base URL: {BASE_URL}")

    # Test 1: Health check
    test_endpoint("Health Check", "GET", f"{BASE_URL}/health/")

    # Test 2: Lista lavori (senza auth per vedere se è il problema)
    test_endpoint("Get Works (no auth)", "GET", f"{BASE_URL}/works/")

    # Test 3: Lista tecnici
    test_endpoint("Get Technicians", "GET", f"{BASE_URL}/technicians/")

    # Test 4: Lista ONT (con API key)
    test_endpoint("Get ONTs", "GET", f"{BASE_URL}/onts/", requires_auth=True)

    # Test 5: Lista Modem (con API key)
    test_endpoint("Get Modems", "GET", f"{BASE_URL}/modems/", requires_auth=True)

    # Test 6: Statistiche settimanali
    test_endpoint("Weekly Stats", "GET", f"{BASE_URL}/stats/weekly")

    # Test 7: Nuovo lavoro (con auth)
    test_data = {
        "numero_wr": "TEST-001",
        "operatore": "Test Operator",
        "indirizzo": "Via Test 123",
        "nome_cliente": "Test Client",
        "stato": "aperto",
        "tipo_lavoro": "attivazione",
        "note": "Test lavoro API"
    }
    test_endpoint("Create Work", "POST", f"{BASE_URL}/works/", test_data, requires_auth=True)

    # Test 8: Nuovo ONT (con API key)
    ont_data = {
        "serial_number": "TEST-ONT-001",
        "model": "Huawei HG8245H",
        "manufacturer": "Huawei",
        "location": "Test Location"
    }
    test_endpoint("Create ONT", "POST", f"{BASE_URL}/onts/", ont_data, requires_auth=True)

    # Test 9: Nuovo Modem (con API key)
    modem_data = {
        "serial_number": "TEST-MODEM-001",
        "model": "Technicolor TG789",
        "type": "vdsl",
        "manufacturer": "Technicolor",
        "location": "Test Location"
    }
    test_endpoint("Create Modem", "POST", f"{BASE_URL}/modems/", modem_data, requires_auth=True)

    # Test 10: Nuovo endpoint ingest (con API key)
    ingest_data = {
        "numero_wr": "INGEST-TEST-001",
        "stato": "aperto",
        "descrizione": "Test ingest lavoro",
        "tecnico": "Test Technician",
        "indirizzo": "Via Ingest Test 123"
    }
    test_endpoint("Ingest Work", "POST", f"{BASE_URL}/works/ingest/work", ingest_data, requires_auth=True)

    # Test 11: Test delle pagine HTML
    print("\n🌐 Testing HTML Pages...")
    pages = [
        ("Index Page", "/"),
        ("Gestionale", "/gestionale.html"),
        ("Dashboard", "/dashboard.html"),
        ("Manual Entry", "/manual_entry.html"),
        ("PC Alex Gestionale", "/pc_alex_gestionale.html")
    ]
    
    for page_name, page_path in pages:
        try:
            response = requests.get(f"{BASE_URL}{page_path}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {page_name}: OK")
            else:
                print(f"❌ {page_name}: Status {response.status_code}")
        except Exception as e:
            print(f"❌ {page_name}: Error - {str(e)}")

    print("\n🎯 Test completati!")

if __name__ == "__main__":
    main()