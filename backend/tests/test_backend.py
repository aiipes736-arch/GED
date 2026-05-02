"""MHCGED backend API tests (pytest)."""
import io
import os
import uuid

import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") if os.environ.get("REACT_APP_BACKEND_URL") else None
if not BASE_URL:
    # Fallback to frontend .env via file read
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL"):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")

ADMIN_EMAIL = "admin@mhcged.cg"
ADMIN_PASSWORD = "Admin@2026"


@pytest.fixture(scope="session")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=20)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    assert data["email"] == ADMIN_EMAIL
    assert data["role"] == "admin"
    return s


# ---------- Auth ----------
def test_login_invalid():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong"}, timeout=15)
    assert r.status_code == 401


def test_me_unauth():
    r = requests.get(f"{BASE_URL}/api/auth/me", timeout=15)
    assert r.status_code == 401


def test_me_authenticated(admin_session):
    r = admin_session.get(f"{BASE_URL}/api/auth/me", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == ADMIN_EMAIL
    assert data["role"] == "admin"
    assert "id" in data


# ---------- Dashboard ----------
def test_dashboard_stats(admin_session):
    r = admin_session.get(f"{BASE_URL}/api/dashboard/stats", timeout=15)
    assert r.status_code == 200
    d = r.json()
    for k in ["total_documents", "total_archived", "total_folders", "total_agents", "recent_documents"]:
        assert k in d


# ---------- Folders CRUD ----------
def test_folder_crud(admin_session):
    name = f"TEST_Folder_{uuid.uuid4().hex[:6]}"
    r = admin_session.post(f"{BASE_URL}/api/folders", json={"name": name, "description": "t"}, timeout=15)
    assert r.status_code == 200, r.text
    folder = r.json()
    assert folder["name"] == name
    fid = folder["id"]

    r = admin_session.get(f"{BASE_URL}/api/folders", timeout=15)
    assert r.status_code == 200
    assert any(f["id"] == fid for f in r.json())

    r = admin_session.put(f"{BASE_URL}/api/folders/{fid}", json={"name": name + "_upd"}, timeout=15)
    assert r.status_code == 200
    assert r.json()["name"] == name + "_upd"

    r = admin_session.delete(f"{BASE_URL}/api/folders/{fid}", timeout=15)
    assert r.status_code == 200


# ---------- Users CRUD (admin) ----------
@pytest.fixture(scope="session")
def created_agent(admin_session):
    email = f"test_agent_{uuid.uuid4().hex[:6]}@mhcged.cg"
    r = admin_session.post(
        f"{BASE_URL}/api/users",
        json={"email": email, "password": "Passw0rd!", "name": "TEST Agent", "role": "agent"},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    u = r.json()
    assert u["email"] == email
    yield u, email
    admin_session.delete(f"{BASE_URL}/api/users/{u['id']}", timeout=15)


def test_list_users(admin_session, created_agent):
    u, _ = created_agent
    r = admin_session.get(f"{BASE_URL}/api/users", timeout=15)
    assert r.status_code == 200
    assert any(x["id"] == u["id"] for x in r.json())


def test_update_user(admin_session, created_agent):
    u, _ = created_agent
    r = admin_session.put(f"{BASE_URL}/api/users/{u['id']}", json={"name": "TEST Agent Updated"}, timeout=15)
    assert r.status_code == 200
    assert r.json()["name"] == "TEST Agent Updated"


def test_non_admin_cannot_list_users(created_agent):
    _, email = created_agent
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "Passw0rd!"}, timeout=15)
    assert r.status_code == 200
    r = s.get(f"{BASE_URL}/api/users", timeout=15)
    assert r.status_code == 403


# ---------- Documents ----------
@pytest.fixture(scope="session")
def uploaded_doc(admin_session):
    files = {"file": ("test.txt", io.BytesIO(b"hello mhcged"), "text/plain")}
    data = {"title": "TEST Doc", "description": "desc", "tags": "t1,t2"}
    r = admin_session.post(f"{BASE_URL}/api/documents", files=files, data=data, timeout=60)
    assert r.status_code == 200, f"Upload failed: {r.status_code} {r.text}"
    d = r.json()
    assert d["title"] == "TEST Doc"
    assert "t1" in d["tags"]
    yield d
    admin_session.delete(f"{BASE_URL}/api/documents/{d['id']}", timeout=15)


def test_list_documents(admin_session, uploaded_doc):
    r = admin_session.get(f"{BASE_URL}/api/documents", timeout=15)
    assert r.status_code == 200
    assert any(x["id"] == uploaded_doc["id"] for x in r.json())


def test_download_document(admin_session, uploaded_doc):
    r = admin_session.get(f"{BASE_URL}/api/documents/{uploaded_doc['id']}/download", timeout=30)
    assert r.status_code == 200
    assert b"hello mhcged" in r.content


def test_update_document(admin_session, uploaded_doc):
    r = admin_session.put(f"{BASE_URL}/api/documents/{uploaded_doc['id']}", json={"title": "TEST Doc Updated"}, timeout=15)
    assert r.status_code == 200
    assert r.json()["title"] == "TEST Doc Updated"


def test_archive_unarchive(admin_session, uploaded_doc):
    r = admin_session.post(f"{BASE_URL}/api/documents/{uploaded_doc['id']}/archive", timeout=15)
    assert r.status_code == 200
    r = admin_session.get(f"{BASE_URL}/api/documents?archived=true", timeout=15)
    assert any(x["id"] == uploaded_doc["id"] for x in r.json())
    r = admin_session.post(f"{BASE_URL}/api/documents/{uploaded_doc['id']}/unarchive", timeout=15)
    assert r.status_code == 200


def test_share_document(admin_session, uploaded_doc, created_agent):
    u, _ = created_agent
    r = admin_session.post(f"{BASE_URL}/api/documents/{uploaded_doc['id']}/share", json={"user_ids": [u["id"]]}, timeout=15)
    assert r.status_code == 200
    assert u["id"] in r.json()["shared_with"]


def test_tags(admin_session, uploaded_doc):
    r = admin_session.get(f"{BASE_URL}/api/tags", timeout=15)
    assert r.status_code == 200
    assert "t1" in r.json()


def test_activity(admin_session):
    r = admin_session.get(f"{BASE_URL}/api/activity", timeout=15)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ---------- Logout ----------
def test_logout():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
    assert r.status_code == 200
    r = s.post(f"{BASE_URL}/api/auth/logout", timeout=15)
    assert r.status_code == 200
    r = s.get(f"{BASE_URL}/api/auth/me", timeout=15)
    assert r.status_code == 401
