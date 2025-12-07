import os
import sys
import json
import tempfile
from fastapi.testclient import TestClient
import pytest

# Ensure Python finds the app package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Ensure tests use a disposable SQLite DB in /tmp
tmp_db = os.path.join(tempfile.gettempdir(), f"test_test_{os.getpid()}.db")
os.environ["DATABASE_URL"] = f"sqlite:///{tmp_db}"
# Set a test API key
os.environ["API_KEY"] = "testkey123"

# Remove the database file if it exists to ensure a clean start
try:
    os.remove(tmp_db)
except Exception:
    pass

# Create the DB file and ensure write permissions so sqlite doesn't complain about read-only
try:
    open(tmp_db, 'a').close()
    os.chmod(tmp_db, 0o666)
except Exception:
    pass


@pytest.fixture(scope='session', autouse=True)
def _cleanup_tmp_db():
    """Session-level cleanup for the temporary DB file.

    The test suite uses a TestClient bound to a temporary SQLite DB file that
    should remain present for the entire test session. Some tests previously
    removed the file mid-run causing read-only or missing-table issues. This
    fixture removes the DB file only at the end of the session.
    """
    try:
        yield
    finally:
        try:
            if os.path.exists(tmp_db):
                os.remove(tmp_db)
        except Exception:
            pass

from app.main import app
from app.database import SessionLocal
from app.models.models import DocumentAppliedWork, Document

client = TestClient(app)


def test_create_team_and_technician_and_work():
    # Ensure clean test DB
    try:
        os.remove("./test_test.db")
    except Exception:
        pass
    # Register an admin user (no users exist at this point)
    res = client.post('/auth/register', json={'username': 'admin', 'password': 'adminpass', 'role': 'admin'})
    assert res.status_code == 200
    admin = res.json()
    assert admin.get('username') == 'admin'

    # Login to get JWT token
    res = client.post('/auth/login', json={'username': 'admin', 'password': 'adminpass'})
    assert res.status_code == 200
    token = res.json().get('access_token')
    auth_header = {"Authorization": f"Bearer {token}"}
    # Create Team
    headers = {"X-API-Key": os.environ["API_KEY"]}
    res = client.post("/teams/", json={"nome": "TeamTest"}, headers=headers)
    assert res.status_code == 200
    team = res.json()
    assert "id" in team
    team_id = team["id"]

    # Create Technician
    res = client.post(f"/technicians/", json={"nome": "Test", "cognome": "User", "telefono": "123456", "squadra_id": team_id}, headers=headers)
    assert res.status_code == 200
    tech = res.json()
    assert "id" in tech

    # Upload a work JSON
    tmp = {"numero_wr": "TESTWR1", "operatore": "OpenFiber", "indirizzo": "Via Test 1", "nome_cliente": "ACME", "tipo_lavoro": "attivazione"}
    res = client.post("/works/", json=tmp, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data.get("id") is not None
    work_id = data.get("id")
    tech_id = tech.get("id")

    # Assign work to technician
    res = client.put(f"/works/{work_id}/assign/{tech_id}", headers=headers)
    assert res.status_code == 200

    # Update status to closed
    res = client.put(f"/works/{work_id}/status", json={"stato": "chiuso"}, headers=headers)
    assert res.status_code == 200

    # Ensure work status changed
    res = client.get("/works/", headers=headers)
    assert res.status_code == 200
    works = res.json()
    assert any(w.get("id") == work_id and w.get("stato") == "chiuso" for w in works)

    # Link Telegram ID to technician
    tg_id = "9999"
    res = client.post(f"/telegram/link/{tech_id}", json={"telegram_id": tg_id}, headers=headers)
    assert res.status_code == 200

    # Monkeypatch telegram send function so we can assert it was called
    import app.utils.telegram as telegram_utils
    notified = []

    def fake_send(chat_id, text):
        notified.append((chat_id, text))
        return True

    telegram_utils.send_message_to_telegram = fake_send

    # Create a second work to test webhook
    tmp2 = {"numero_wr": "TESTWR2", "operatore": "OpenFiber", "indirizzo": "Via Test 2", "nome_cliente": "ACME", "tipo_lavoro": "attivazione"}
    res = client.post("/works/", json=tmp2, headers=headers)
    assert res.status_code == 200
    work2_id = res.json().get("id")

    # Simulate webhook to accept work
    webhook_payload = {
        "update_id": 12345,
        "message": {
            "message_id": 1,
            "from": {"id": int(tg_id), "is_bot": False, "first_name": "Tech"},
            "chat": {"id": int(tg_id), "type": "private"},
            "date": 1600000000,
            "text": f"/accetta {tmp2['numero_wr']}"
        }
    }
    res = client.post("/telegram/webhook", json=webhook_payload)
    assert res.status_code == 200
    assert res.json().get("ok") is True

    # Verify the work is assigned to the technician
    res = client.get("/works/", headers=headers)
    works = res.json()
    assert any(w.get("id") == work2_id and w.get("stato") == "in_corso" and w.get("tecnico_assegnato") is not None for w in works)

    # Upload a document (simulate pdf containing JSON text)
    tmp3 = {"numero_wr": "DOCWR1", "operatore": "OpenFiber", "indirizzo": "Via PDF 3", "nome_cliente": "ACME", "tipo_lavoro": "attivazione"}
    files = {"files": ("wr_doc.pdf", json.dumps(tmp3), "application/pdf")}
    res = client.post("/documents/upload", files=files, headers=headers)
    assert res.status_code == 200
    doc = res.json()[0]
    doc_id = doc.get("id")

    # Parse document
    res = client.post(f"/documents/{doc_id}/parse", headers=headers)
    assert res.status_code == 200
    parsed = res.json().get("parsed_data")
    assert parsed is not None
    assert parsed.get("numero_wr") == tmp3.get("numero_wr") or parsed.get("operatore") == tmp3.get("operatore")

    # Apply document to create a new work
    res = client.post(f"/documents/{doc_id}/apply", headers=headers)
    assert res.status_code == 200
    apply_doc = res.json()
    assert apply_doc.get("applied_work_id") is not None

    # Ensure the bot notification was triggered
    assert len(notified) >= 1
    assert notified[0][0] == tg_id

    # Simulate webhook to request help
    webhook_payload_help = {
        "update_id": 99999,
        "message": {
            "message_id": 3,
            "from": {"id": int(tg_id), "is_bot": False, "first_name": "Tech"},
            "chat": {"id": int(tg_id), "type": "private"},
            "date": 1600000002,
            "text": "/help"
        }
    }
    res = client.post("/telegram/webhook", json=webhook_payload_help)
    assert res.status_code == 200
    assert res.json().get("ok") is True
    # Ensure the bot sent the help text
    assert any("Mostra questo messaggio di aiuto" in t[1] for t in notified)

    # Simulate webhook to request help with bot mention
    webhook_payload_help_mention = {
        "update_id": 99998,
        "message": {
            "message_id": 4,
            "from": {"id": int(tg_id), "is_bot": False, "first_name": "Tech"},
            "chat": {"id": int(tg_id), "type": "private"},
            "date": 1600000003,
            "text": "/help@MyFtthBot"
        }
    }
    res = client.post("/telegram/webhook", json=webhook_payload_help_mention)
    assert res.status_code == 200
    assert res.json().get("ok") is True
    assert any("Mostra questo messaggio di aiuto" in t[1] for t in notified)

    # Simulate webhook to close a work via /chiudi@bot
    # First create a work and assign to the technician
    tmp4 = {"numero_wr": "CLOSEWR1", "operatore": "OpenFiber", "indirizzo": "Via Close 1", "nome_cliente": "ACME", "tipo_lavoro": "attivazione"}
    res = client.post('/works/', json=tmp4, headers=headers)
    assert res.status_code == 200
    close_work_id = res.json().get("id")
    # Assign
    res = client.put(f"/works/{close_work_id}/assign/{tech_id}", headers=headers)
    assert res.status_code == 200

    webhook_payload_chiudi = {
        "update_id": 99997,
        "message": {
            "message_id": 5,
            "from": {"id": int(tg_id), "is_bot": False, "first_name": "Tech"},
            "chat": {"id": int(tg_id), "type": "private"},
            "date": 1600000004,
            "text": f"/chiudi@MyFtthBot {tmp4['numero_wr']}"
        }
    }
    res = client.post('/telegram/webhook', json=webhook_payload_chiudi)
    assert res.status_code == 200
    assert res.json().get('ok') is True

    # Verify the work exists
    res = client.get("/works/", headers=headers)
    assert res.status_code == 200
    works = res.json()
    assert any(w.get("numero_wr") == tmp3["numero_wr"] for w in works)

    # NOTE: The temporary DB is cleaned up by a session-scoped fixture after
    # the entire test session completes. Do not remove it here.


def test_ui_edit_and_status_change():
    # Ensure we have an admin and token
    res = client.post('/auth/login', json={'username': 'admin', 'password': 'adminpass'})
    if res.status_code != 200:
        res_reg = client.post('/auth/register', json={'username': 'admin', 'password': 'adminpass', 'role': 'admin'})
        assert res_reg.status_code == 200
        res = client.post('/auth/login', json={'username': 'admin', 'password': 'adminpass'})
    assert res.status_code == 200
    token = res.json().get('access_token')
    headers = {"X-API-Key": os.environ["API_KEY"], "Authorization": f"Bearer {token}"}

    # Create Team
    res = client.post('/teams/', json={'nome': 'Test UI Team'}, headers=headers)
    assert res.status_code == 200
    team = res.json()
    team_id = team.get('id')

    # Create Technician
    res = client.post('/technicians/', json={'nome': 'Test', 'cognome': 'Tec', 'telefono': '123456', 'squadra_id': team_id}, headers=headers)
    assert res.status_code == 200
    tech = res.json()
    tech_id = tech.get('id')

    # Create a work
    tmp = {"numero_wr": "UITEST001", "operatore": "OpenTest", "indirizzo": "Via UI 1", "nome_cliente": "Cliente UI", "tipo_lavoro": "attivazione"}
    res = client.post('/works/', json=tmp, headers=headers)
    assert res.status_code == 200
    work_id = res.json().get('id')

    # Assign technician via update_work
    res = client.put(f'/works/{work_id}', json={"tecnico_assegnato_id": tech_id}, headers=headers)
    assert res.status_code == 200
    assert res.json().get('tecnico_assegnato') and res.json().get('tecnico_assegnato').get('id') == tech_id

    # Suspend the work
    res = client.put(f'/works/{work_id}', json={"stato": "sospeso"}, headers=headers)
    assert res.status_code == 200
    assert res.json().get('stato') == 'sospeso'

    # Close the work
    res = client.put(f'/works/{work_id}', json={"stato": "chiuso"}, headers=headers)
    assert res.status_code == 200
    # Ensure data_chiusura is set
    assert res.json().get('stato') == 'chiuso' and res.json().get('data_chiusura') is not None


def test_inline_update_numero_wr_and_unassign():
    # Ensure admin login
    res = client.post('/auth/login', json={'username': 'admin', 'password': 'adminpass'})
    if res.status_code != 200:
        res_reg = client.post('/auth/register', json={'username': 'admin', 'password': 'adminpass', 'role': 'admin'})
        assert res_reg.status_code == 200
        res = client.post('/auth/login', json={'username': 'admin', 'password': 'adminpass'})
    assert res.status_code == 200
    token = res.json().get('access_token')
    headers = {"X-API-Key": os.environ["API_KEY"], "Authorization": f"Bearer {token}"}

    # Create Team and Tech
    res = client.post('/teams/', json={'nome': 'InlineTeam'}, headers=headers)
    assert res.status_code == 200
    team_id = res.json().get('id')
    res = client.post('/technicians/', json={'nome': 'In', 'cognome': 'Line', 'telefono': '1234567', 'squadra_id': team_id}, headers=headers)
    assert res.status_code == 200
    tech_id = res.json().get('id')

    # Create work
    tmp = {"numero_wr": "INLINE001", "operatore": "OpenTest", "indirizzo": "Via Inline", "nome_cliente": "Client Inline", "tipo_lavoro": "attivazione"}
    res = client.post('/works/', json=tmp, headers=headers)
    assert res.status_code == 200
    work_id = res.json().get('id')

    # Assign to technician
    res = client.put(f'/works/{work_id}', json={"tecnico_assegnato_id": tech_id}, headers=headers)
    assert res.status_code == 200
    assert res.json().get('tecnico_assegnato') and res.json().get('tecnico_assegnato').get('id') == tech_id

    # Update numero_wr and unassign
    new_num = 'INLINE-UPDATED-001'
    res = client.put(f'/works/{work_id}', json={"numero_wr": new_num, "tecnico_assegnato_id": None}, headers=headers)
    assert res.status_code == 200
    assert res.json().get('numero_wr') == new_num
    assert res.json().get('tecnico_assegnato') is None


def test_multi_client_pdf_apply_creates_multiple_works():
    # Ensure admin login
    res = client.post('/auth/login', json={'username': 'admin', 'password': 'adminpass'})
    if res.status_code != 200:
        res_reg = client.post('/auth/register', json={'username': 'admin', 'password': 'adminpass', 'role': 'admin'})
        assert res_reg.status_code == 200
        res = client.post('/auth/login', json={'username': 'admin', 'password': 'adminpass'})
    assert res.status_code == 200
    token = res.json().get('access_token')
    headers = {"X-API-Key": os.environ["API_KEY"], "Authorization": f"Bearer {token}"}

    # Create a document that contains multiple WR entries encoded as JSON array
    multi = [
        {"numero_wr": "MULTI001", "operatore": "OpenF", "indirizzo": "Via X", "nome_cliente": "ClienteA", "tipo_lavoro": "attivazione"},
        {"numero_wr": "MULTI002", "operatore": "OpenF", "indirizzo": "Via Y", "nome_cliente": "ClienteB", "tipo_lavoro": "attivazione"}
    ]
    files = {"files": ("multi.pdf", json.dumps(multi), "application/pdf")}
    res = client.post('/documents/upload', files=files, headers=headers)
    assert res.status_code == 200
    doc = res.json()[0]
    doc_id = doc.get('id')

    # Parse the document
    res = client.post(f'/documents/{doc_id}/parse', headers=headers)
    assert res.status_code == 200
    parsed = res.json().get('parsed_data')
    # It should present entries or, at least, be a single parsed entity
    if isinstance(parsed, dict):
        entries = parsed.get('entries') if parsed.get('entries') is not None else [parsed]
    elif isinstance(parsed, list):
        entries = parsed
    else:
        entries = []
    assert len(entries) == 2

    # Apply document, expect create 2 works
    res = client.post(f'/documents/{doc_id}/apply', headers=headers)
    assert res.status_code == 200
    doc_after = res.json()
    parsed_after = doc_after.get('parsed_data')
    # applied_work_ids should be present
    assert parsed_after is not None
    # If parsed_after is dict with entries, applied_work_ids is in that dict
    ids = None
    if isinstance(parsed_after, dict) and parsed_after.get('applied_work_ids'):
        ids = parsed_after.get('applied_work_ids')
    elif isinstance(parsed_after, dict) and parsed_after.get('entries'):
        # may attach in entries schema
        ids = parsed_after.get('applied_work_ids')
    assert isinstance(ids, list) and len(ids) == 2
    # Check that works exist
    res = client.get('/works/', headers=headers)
    assert res.status_code == 200
    works = res.json()
    assert any(w.get('numero_wr') == 'MULTI001' for w in works)
    assert any(w.get('numero_wr') == 'MULTI002' for w in works)

    # Verify the DocumentAppliedWork association rows exist
    from app.database import SessionLocal
    from app.models.models import Document, DocumentAppliedWork
    from app.database import SessionLocal
    from app.models.models import Document, DocumentAppliedWork
    db = SessionLocal()
    rows = db.query(DocumentAppliedWork).filter(DocumentAppliedWork.document_id == doc_id).all()
    db.close()
    assert len(rows) == 2


def test_manual_create_and_assign():
    # Ensure admin is registered and we have an API key
    headers = {"X-API-Key": os.environ["API_KEY"]}
    # Create a team
    res = client.post('/teams/', json={'nome': 'ManualTestTeam'}, headers=headers)
    assert res.status_code == 200
    team_id = res.json().get('id')
    # Create tech
    res = client.post('/technicians/', json={'nome': 'Manual', 'cognome': 'Tech', 'telefono': '333444555', 'squadra_id': team_id}, headers=headers)
    assert res.status_code == 200
    tech_id = res.json().get('id')
    # Create manual work with technican assignment
    payload = {
        "numero_wr": "MANUAL001",
        "nome_cliente": "Cliente Manuale",
        "indirizzo": "Via Manuale 1",
        "tipo": "attivazione",
        "stato": "attivato",
        "tecnico": str(tech_id)
    }
    res = client.post('/manual/works', json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data.get('ok') is True
    # Verify via API
    res = client.get('/works/', headers=headers)
    assert res.status_code == 200
    works = res.json()
    assert any(w.get('numero_wr') == 'MANUAL001' and w.get('tecnico_assegnato') and w.get('tecnico_assegnato').get('id') == tech_id for w in works)


def test_notify_technician_endpoint():
    headers = {"X-API-Key": os.environ["API_KEY"]}
    # Create team and technician
    res = client.post('/teams/', json={'nome': 'NotifyTeam'}, headers=headers)
    assert res.status_code == 200
    team_id = res.json().get('id')
    res = client.post('/technicians/', json={'nome': 'Notify', 'cognome': 'Tech', 'telefono': '333777888', 'squadra_id': team_id}, headers=headers)
    assert res.status_code == 200
    tech_id = res.json().get('id')
    # Link a Telegram id to technician via route
    res = client.post(f'/telegram/link/{tech_id}', json={'telegram_id': '9999'}, headers=headers)
    assert res.status_code == 200
    # Create manual work and assign to tech
    res = client.post('/manual/works', json={'numero_wr': 'NOTIFY001', 'nome_cliente': 'Check', 'indirizzo': 'Via Notify 1', 'tecnico': str(tech_id)}, headers=headers)
    assert res.status_code == 200
    work_id = res.json().get('id')
    # Monkeypatch telegram send function
    import app.utils.telegram as telegram_utils
    notified = []
    def fake_send(chat_id, text, reply_markup=None):
        notified.append((chat_id, text))
        return True
    telegram_utils.send_message_to_telegram = fake_send
    # Use notify endpoint
    res = client.post(f'/works/{work_id}/notify', json={'message': 'Ciao Tech!'}, headers=headers)
    assert res.status_code == 200
    # Check the fake_send was called
    assert len(notified) == 1


def test_stats_yearly_endpoint():
    res = client.get('/stats/yearly')
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 12
    assert 'date' in data[0] and 'closed' in data[0]


def test_multi_client_pdf_apply_selected_indices_applies_subset():
    # Ensure admin login
    res = client.post('/auth/login', json={'username': 'admin', 'password': 'adminpass'})
    assert res.status_code == 200
    token = res.json().get('access_token')
    headers = {"X-API-Key": os.environ["API_KEY"], "Authorization": f"Bearer {token}"}

    multi = [
        {"numero_wr": "SUB1", "operatore": "OpenF", "indirizzo": "Via S1", "nome_cliente": "ClienteA", "tipo_lavoro": "attivazione"},
        {"numero_wr": "SUB2", "operatore": "OpenF", "indirizzo": "Via S2", "nome_cliente": "ClienteB", "tipo_lavoro": "attivazione"}
    ]
    files = {"files": ("multi.pdf", json.dumps(multi), "application/pdf")}
    res = client.post('/documents/upload', files=files, headers=headers)
    assert res.status_code == 200
    doc = res.json()[0]
    doc_id = doc.get('id')

    # Parse document
    res = client.post(f'/documents/{doc_id}/parse', headers=headers)
    assert res.status_code == 200
    parsed = res.json().get('parsed_data')
    if isinstance(parsed, dict):
        entries = parsed.get('entries') if parsed.get('entries') is not None else [parsed]
    elif isinstance(parsed, list):
        entries = parsed
    else:
        entries = []
    assert len(entries) == 2

    # Apply only the first entry (index 0)
    res = client.post(f'/documents/{doc_id}/apply?selected_indices=0', headers=headers)
    assert res.status_code == 200
    doc_after = res.json()
    parsed_after = doc_after.get('parsed_data')
    assert parsed_after is not None
    ids = parsed_after.get('applied_work_ids') if isinstance(parsed_after, dict) else None
    assert isinstance(ids, list) and len(ids) == 1
    # Check that only one Work exists with the given WRs
    res = client.get('/works/', headers=headers)
    assert res.status_code == 200
    works = res.json()
    assert any(w.get('numero_wr') == 'SUB1' for w in works)
    assert not any(w.get('numero_wr') == 'SUB2' for w in works)
    # Verify association rows only 1
    db = SessionLocal()
    rows = db.query(DocumentAppliedWork).filter(DocumentAppliedWork.document_id == doc_id).all()
    db.close()
    assert len(rows) == 1


def test_merge_duplicates_updates_applied_associations():
    # Ensure admin login
    res = client.post('/auth/login', json={'username': 'admin', 'password': 'adminpass'})
    assert res.status_code == 200
    token = res.json().get('access_token')
    headers = {"X-API-Key": os.environ["API_KEY"], "Authorization": f"Bearer {token}"}

    # Insert two works with normalizations that collide (via DB session)
    from app.database import SessionLocal
    from app.models.models import Work, DocumentAppliedWork, Document
    db = SessionLocal()
    import datetime
    w1 = Work(numero_wr='WR 010', operatore='op', indirizzo='A', nome_cliente='A', tipo_lavoro='attivazione', data_apertura=datetime.datetime.now())
    w2 = Work(numero_wr='WR-010', operatore='op', indirizzo='B', nome_cliente='B', tipo_lavoro='attivazione', data_apertura=datetime.datetime.now())
    db.add(w1); db.add(w2); db.commit(); db.refresh(w1); db.refresh(w2)
    doc = Document(filename='dup.pdf', mime='application/pdf', content=b'', uploaded_at=datetime.datetime.now(), parsed=True, parsed_data={'entries': [], 'applied_work_ids': [w1.id, w2.id]})
    db.add(doc); db.commit(); db.refresh(doc)
    a1 = DocumentAppliedWork(document_id=doc.id, work_id=w1.id, applied_at=datetime.datetime.now())
    a2 = DocumentAppliedWork(document_id=doc.id, work_id=w2.id, applied_at=datetime.datetime.now())
    db.add(a1); db.add(a2); db.commit()
    doc_id = doc.id
    db.close()


def test_pratica_label_parsing_and_apply():
    # Ensure admin login
    res = client.post('/auth/login', json={'username': 'admin', 'password': 'adminpass'})
    if res.status_code != 200:
        res = client.post('/auth/register', json={'username': 'admin', 'password': 'adminpass', 'role': 'admin'})
        assert res.status_code == 200
        res = client.post('/auth/login', json={'username': 'admin', 'password': 'adminpass'})
    assert res.status_code == 200
    token = res.json().get('access_token')
    headers = {"X-API-Key": os.environ["API_KEY"], "Authorization": f"Bearer {token}"}

    sample_text = 'Pratica: 1764902551\nCliente: Mario Rossi\nIndirizzo: Via Roma 12'
    files = {"files": ("pratica.pdf", sample_text, "application/pdf")}
    res = client.post('/documents/upload', files=files, headers=headers)
    assert res.status_code == 200
    doc = res.json()[0]
    doc_id = doc.get('id')

    # Parse the document (should find Pratica -> numero_wr)
    res = client.post(f'/documents/{doc_id}/parse', headers=headers)
    assert res.status_code == 200
    parsed = res.json().get('parsed_data')
    assert parsed is not None
    entries = parsed.get('entries') if isinstance(parsed, dict) and parsed.get('entries') is not None else [parsed]
    assert len(entries) == 1
    entry = entries[0]
    assert entry.get('numero_wr') == '1764902551'

    # Apply the document
    res = client.post(f'/documents/{doc_id}/apply', headers=headers)
    assert res.status_code == 200
    parsed_after = res.json().get('parsed_data')
    ids = parsed_after.get('applied_work_ids') if isinstance(parsed_after, dict) else None
    assert isinstance(ids, list) and len(ids) == 1
    # Check Work exists with normalized WR
    res = client.get('/works/', headers=headers)
    assert res.status_code == 200
    works = res.json()
    assert any(w.get('numero_wr') == 'WR-1764902551' for w in works)

    # Call merge duplicates
    res = client.post('/works/merge_duplicates', headers=headers)
    assert res.status_code == 200
    # Verify document associations updated
    db = SessionLocal()
    rows = db.query(DocumentAppliedWork).filter(DocumentAppliedWork.document_id == doc_id).all()
    # Should be only one row pointing to keeper
    assert len(rows) == 1
    keeper_id = rows[0].work_id
    d = db.query(Document).filter(Document.id == doc_id).first()
    assert d.parsed_data and isinstance(d.parsed_data.get('applied_work_ids'), list)
    assert d.parsed_data.get('applied_work_ids') == [keeper_id]
    db.close()


def test_wr_label_parsing_and_apply():
    # Ensure admin login
    res = client.post('/auth/login', json={'username': 'admin', 'password': 'adminpass'})
    if res.status_code != 200:
        res = client.post('/auth/register', json={'username': 'admin', 'password': 'adminpass', 'role': 'admin'})
        assert res.status_code == 200
        res = client.post('/auth/login', json={'username': 'admin', 'password': 'adminpass'})
    assert res.status_code == 200
    token = res.json().get('access_token')
    headers = {"X-API-Key": os.environ["API_KEY"], "Authorization": f"Bearer {token}"}

    sample_text = 'WR: 15699897\nCliente: RAINONE DANILO Indiriz.: VIA GIUSEPPE'
    files = {"files": ("wr.pdf", sample_text, "application/pdf")}
    res = client.post('/documents/upload', files=files, headers=headers)
    assert res.status_code == 200
    doc = res.json()[0]
    doc_id = doc.get('id')

    # Parse and apply
    res = client.post(f'/documents/{doc_id}/parse', headers=headers)
    assert res.status_code == 200
    parsed = res.json().get('parsed_data')
    assert parsed is not None
    entries = parsed.get('entries') if isinstance(parsed, dict) and parsed.get('entries') is not None else [parsed]
    assert len(entries) >= 1
    # Apply
    res = client.post(f'/documents/{doc_id}/apply', headers=headers)
    assert res.status_code == 200
    parsed_after = res.json().get('parsed_data')
    ids = parsed_after.get('applied_work_ids') if isinstance(parsed_after, dict) else None
    assert isinstance(ids, list) and len(ids) >= 1
    # Check Work exists with normalized WR
    res = client.get('/works/', headers=headers)
    assert res.status_code == 200
    works = res.json()
    assert any(w.get('numero_wr') == 'WR-15699897' for w in works)


def test_telegram_status_endpoint():
    # Call the status endpoint; it should return JSON with a token_set key
    res = client.get('/telegram/status')
    assert res.status_code == 200
    data = res.json()
    assert 'token_set' in data


def test_debug_db_requires_api_key():
    # Without headers, the endpoint should reject access
    res = client.get('/debug/db')
    assert res.status_code in (401, 403)
    # With X-API-Key it should return data
    res = client.get('/debug/db?table=works&limit=1', headers={'X-API-Key': os.environ['API_KEY']})
    assert res.status_code == 200
    data = res.json()
    assert 'rows' in data

def test_debug_db_documents_handles_binary_content():
    headers = {"X-API-Key": os.environ["API_KEY"]}
    # Upload a small binary file
    files = {"files": ("binary.pdf", b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n1 0 obj\n<< /Type /Catalog >>\nendobj\n", "application/pdf")}
    res = client.post('/documents/upload', files=files, headers=headers)
    assert res.status_code == 200
    doc = res.json()[0]
    doc_id = doc.get('id')
    # Call debug endpoint
    res = client.get('/debug/db?table=documents&limit=10', headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data.get('table') == 'documents'
    rows = data.get('rows')
    assert isinstance(rows, list)
    # Find our doc and check the content field is serializable
    matched = [r for r in rows if r.get('id') == doc_id]
    assert len(matched) == 1
    content = matched[0].get('content')
    # Content should be a string placeholder or base64 string
    assert content is None or isinstance(content, str)


    
