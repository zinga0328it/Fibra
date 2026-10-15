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

def request_json(method, url, data=None, headers=None, requires_auth=False):
    if headers is None:
        headers = {}
    if requires_auth:
        headers["X-API-Key"] = API_KEY

    if method.upper() == "GET":
        response = requests.get(url, headers=headers, timeout=10)
    elif method.upper() == "POST":
        headers["Content-Type"] = "application/json"
        response = requests.post(url, json=data, headers=headers, timeout=10)
    elif method.upper() == "PUT":
        headers["Content-Type"] = "application/json"
        response = requests.put(url, json=data, headers=headers, timeout=10)
    else:
        raise ValueError(f"Unsupported method: {method}")

    return response

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

    # Test 10: Create and assign modem to a new work
    unique_suffix = int(time.time())
    assign_work_data = {
        "numero_wr": f"TEST-ASSIGN-{unique_suffix}",
        "operatore": "Test Assign Operator",
        "indirizzo": "Via Assign Test 123",
        "nome_cliente": "Assign Client",
        "stato": "aperto",
        "tipo_lavoro": "attivazione",
        "note": "Work created for modem assignment test"
    }
    work_resp = request_json("POST", f"{BASE_URL}/works/", assign_work_data, requires_auth=True)
    if work_resp.status_code == 200:
        work = work_resp.json()
        print(f"✅ Work created for assignment: id={work['id']} numero_wr={work['numero_wr']}")
    else:
        print(f"❌ Failed to create work for assignment: {work_resp.status_code} {work_resp.text}")
        work = None

    assign_modem_data = {
        "serial_number": f"TEST-MODEM-ASSIGN-{unique_suffix}",
        "model": "ZTE",
        "type": "fiber",
        "manufacturer": "ZTE",
        "location": "Test Location"
    }
    modem_resp = request_json("POST", f"{BASE_URL}/modems/", assign_modem_data, requires_auth=True)
    if modem_resp.status_code == 200:
        modem = modem_resp.json()
        print(f"✅ Modem created for assignment: id={modem['id']} serial_number={modem['serial_number']}")
    else:
        print(f"❌ Failed to create modem for assignment: {modem_resp.status_code} {modem_resp.text}")
        modem = None

    if work and modem:
        assign_resp = request_json("PUT", f"{BASE_URL}/modems/{modem['id']}/assign/{work['id']}", requires_auth=True)
        if assign_resp.status_code == 200:
            print("✅ Modem assignment succeeded")
            verify_resp = request_json("GET", f"{BASE_URL}/works/{work['id']}/equipment", requires_auth=True)
            if verify_resp.status_code == 200:
                print(f"✅ Work equipment after assignment: {verify_resp.json()}")
            else:
                print(f"❌ Work equipment check failed: {verify_resp.status_code} {verify_resp.text}")
        else:
            print(f"❌ Modem assignment failed: {assign_resp.status_code} {assign_resp.text}")


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
