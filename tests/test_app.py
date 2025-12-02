import os
import sys
import json
import tempfile
from fastapi.testclient import TestClient

# Ensure Python finds the app package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Ensure tests use a disposable SQLite DB
os.environ["DATABASE_URL"] = "sqlite:///./test_test.db"
# Set a test API key
os.environ["API_KEY"] = "testkey123"

from app.main import app

client = TestClient(app)


def test_create_team_and_technician_and_work():
    # Create Team
    headers = {"X-API-Key": os.environ["API_KEY"]}
    res = client.post("/teams/", json={"nome": "TeamTest"}, headers=headers)
    assert res.status_code == 200
    team = res.json()
    assert "id" in team
    team_id = team["id"]

    # Create Technician
    res = client.post(f"/technicians/", json={"nome": "Test", "cognome": "User", "telefono": "12345", "squadra_id": team_id}, headers=headers)
    assert res.status_code == 200
    tech = res.json()
    assert "id" in tech

    # Upload a work JSON
    tmp = {"numero_wr": "TESTWR1", "operatore": "OpenFiber", "indirizzo": "Via Test 1", "nome_cliente": "ACME", "tipo_lavoro": "attivazione"}
    files = {"file": ("wr.json", json.dumps(tmp), "application/json")}
    res = client.post("/works/upload", files=files, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data.get("id") is not None
    work_id = data.get("id")
    tech_id = tech.get("id")

    # Assign work to technician
    res = client.put(f"/works/{work_id}/assign/{tech_id}", headers=headers)
    assert res.status_code == 200

    # Update status to closed
    res = client.put(f"/works/{work_id}/status?status=chiuso", headers=headers)
    assert res.status_code == 200

    # Ensure work status changed
    res = client.get("/works/", headers=headers)
    assert res.status_code == 200
    works = res.json()
    assert any(w.get("id") == work_id and w.get("stato") == "chiuso" for w in works)

    # Cleanup test DB
    try:
        os.remove("./test_test.db")
    except Exception:
        pass
