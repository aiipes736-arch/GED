"""Phase 1 backend tests:
- Settings (GET public, POST logo/hero admin-only, file serving)
- Permissions: agents cannot modify/delete folders or modify/delete/share/archive docs
- Permissions: agents CAN upload documents
- Isolation: agents see only their own folders/documents
"""
import io
import os
import time
import struct
import zlib

import pytest
import requests

_FE_ENV = "/app/frontend/.env"
if not os.environ.get("REACT_APP_BACKEND_URL") and os.path.exists(_FE_ENV):
    with open(_FE_ENV) as _f:
        for _line in _f:
            if _line.startswith("REACT_APP_BACKEND_URL="):
                os.environ["REACT_APP_BACKEND_URL"] = _line.split("=", 1)[1].strip()
                break

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
ADMIN_EMAIL = "admin@mhcged.cg"
ADMIN_PASSWORD = "Admin@2026"


def _minimal_png_bytes() -> bytes:
    """Build a valid 1x1 PNG without external deps."""
    sig = b"\x89PNG\r\n\x1a\n"

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    raw = b"\x00\xff\x00\x00"  # filter byte + 1 RGB pixel
    idat = chunk(b"IDAT", zlib.compress(raw))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def agent_session(admin_session):
    """Create an agent + login as that agent. Cleans up after module."""
    ts = int(time.time())
    email = f"TEST_phase1_agent_{ts}@example.com"
    password = "Agent@2026Test"
    r = admin_session.post(
        f"{BASE_URL}/api/users",
        json={"email": email, "password": password, "name": "Phase1 Agent", "role": "agent"},
    )
    assert r.status_code in (200, 201), f"Agent create failed: {r.status_code} {r.text}"
    user_id = r.json().get("id")
    s = requests.Session()
    r2 = s.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})
    assert r2.status_code == 200, f"Agent login failed: {r2.status_code} {r2.text}"
    yield s
    # teardown
    try:
        admin_session.delete(f"{BASE_URL}/api/users/{user_id}")
    except Exception:
        pass


# ============== SETTINGS ==============
class TestSettings:
    def test_get_settings_public_no_auth(self):
        r = requests.get(f"{BASE_URL}/api/settings")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "logo_url" in body and "hero_url" in body
        assert isinstance(body["logo_url"], str) and len(body["logo_url"]) > 0
        assert isinstance(body["hero_url"], str) and len(body["hero_url"]) > 0

    def test_post_logo_admin_updates_logo_url(self, admin_session):
        png = _minimal_png_bytes()
        files = {"file": ("logo.png", png, "image/png")}
        r = admin_session.post(f"{BASE_URL}/api/settings/logo", files=files)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "logo_url" in body
        assert "/api/settings/file/" in body["logo_url"]
        # GET should reflect it
        r2 = requests.get(f"{BASE_URL}/api/settings")
        assert r2.json()["logo_url"] == body["logo_url"]

    def test_post_hero_admin_updates_hero_url(self, admin_session):
        png = _minimal_png_bytes()
        files = {"file": ("hero.png", png, "image/png")}
        r = admin_session.post(f"{BASE_URL}/api/settings/hero", files=files)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "hero_url" in body
        assert "/api/settings/file/" in body["hero_url"]

    def test_post_logo_non_admin_403(self, agent_session):
        png = _minimal_png_bytes()
        files = {"file": ("logo.png", png, "image/png")}
        r = agent_session.post(f"{BASE_URL}/api/settings/logo", files=files)
        assert r.status_code == 403, f"Expected 403 got {r.status_code}: {r.text}"

    def test_post_hero_non_admin_403(self, agent_session):
        png = _minimal_png_bytes()
        files = {"file": ("hero.png", png, "image/png")}
        r = agent_session.post(f"{BASE_URL}/api/settings/hero", files=files)
        assert r.status_code == 403

    def test_settings_file_serves_uploaded(self, admin_session):
        # Upload first to ensure there's an image
        png = _minimal_png_bytes()
        files = {"file": ("logo.png", png, "image/png")}
        r = admin_session.post(f"{BASE_URL}/api/settings/logo", files=files)
        assert r.status_code == 200
        url = r.json()["logo_url"]
        # Resolve relative URL against BASE_URL
        if url.startswith("/"):
            full = f"{BASE_URL}{url}"
        else:
            full = url
        r2 = requests.get(full)
        assert r2.status_code == 200, f"file serve failed: {r2.status_code}"
        assert r2.content[:8] == b"\x89PNG\r\n\x1a\n", "Not a PNG response"


# ============== PERMISSIONS: FOLDERS ==============
class TestFolderPermissions:
    def test_agent_cannot_update_folder(self, admin_session, agent_session):
        r = admin_session.post(f"{BASE_URL}/api/folders", json={"name": "TEST_PHASE1_FOLDER_ADMIN"})
        assert r.status_code == 200, r.text
        fid = r.json()["id"]
        try:
            ru = agent_session.put(f"{BASE_URL}/api/folders/{fid}", json={"name": "renamed"})
            assert ru.status_code == 403
            assert "administrateur" in ru.json().get("detail", "").lower()
        finally:
            admin_session.delete(f"{BASE_URL}/api/folders/{fid}")

    def test_agent_cannot_delete_folder(self, admin_session, agent_session):
        r = admin_session.post(f"{BASE_URL}/api/folders", json={"name": "TEST_PHASE1_FOLDER_DEL"})
        assert r.status_code == 200
        fid = r.json()["id"]
        rd = agent_session.delete(f"{BASE_URL}/api/folders/{fid}")
        assert rd.status_code == 403
        # admin cleanup
        admin_session.delete(f"{BASE_URL}/api/folders/{fid}")


# ============== PERMISSIONS: DOCUMENTS ==============
class TestDocumentPermissions:
    def _upload(self, session, title="TEST_PHASE1_DOC"):
        files = {"file": ("t.txt", b"hello", "text/plain")}
        data = {"title": title, "description": "", "tags": ""}
        r = session.post(f"{BASE_URL}/api/documents", files=files, data=data)
        return r

    def test_agent_can_upload(self, agent_session):
        r = self._upload(agent_session, "TEST_PHASE1_AGENT_UPLOAD")
        assert r.status_code == 200, r.text
        assert r.json().get("uploaded_by_name")

    def test_agent_cannot_modify_doc(self, admin_session, agent_session):
        r = self._upload(admin_session, "TEST_PHASE1_DOC_MOD")
        assert r.status_code == 200
        did = r.json()["id"]
        # Share with agent so they have read access (still cannot modify)
        admin_session.post(f"{BASE_URL}/api/documents/{did}/share", json={"user_ids": []})
        ru = agent_session.put(f"{BASE_URL}/api/documents/{did}", json={"title": "new"})
        assert ru.status_code == 403

    def test_agent_cannot_delete_doc(self, admin_session, agent_session):
        r = self._upload(admin_session, "TEST_PHASE1_DOC_DEL")
        did = r.json()["id"]
        rd = agent_session.delete(f"{BASE_URL}/api/documents/{did}")
        assert rd.status_code == 403

    def test_agent_cannot_share_doc(self, admin_session, agent_session):
        r = self._upload(admin_session, "TEST_PHASE1_DOC_SHARE")
        did = r.json()["id"]
        rs = agent_session.post(f"{BASE_URL}/api/documents/{did}/share", json={"user_ids": []})
        assert rs.status_code == 403

    def test_agent_cannot_archive_doc(self, admin_session, agent_session):
        r = self._upload(admin_session, "TEST_PHASE1_DOC_ARCH")
        did = r.json()["id"]
        ra = agent_session.post(f"{BASE_URL}/api/documents/{did}/archive")
        assert ra.status_code == 403
        # And the agent should also fail unarchive
        ru = agent_session.post(f"{BASE_URL}/api/documents/{did}/unarchive")
        assert ru.status_code == 403


# ============== ISOLATION ==============
class TestIsolation:
    def test_folder_isolation(self, admin_session, agent_session):
        # Admin creates a folder
        r1 = admin_session.post(f"{BASE_URL}/api/folders", json={"name": "TEST_PHASE1_ISO_ADMIN_FOLDER"})
        admin_fid = r1.json()["id"]
        # Agent creates a folder
        r2 = agent_session.post(f"{BASE_URL}/api/folders", json={"name": "TEST_PHASE1_ISO_AGENT_FOLDER"})
        agent_fid = r2.json()["id"]
        try:
            # Agent listing must not include admin folder
            ra = agent_session.get(f"{BASE_URL}/api/folders").json()
            ids = [f["id"] for f in ra]
            assert agent_fid in ids
            assert admin_fid not in ids
            # Admin sees both
            radm = admin_session.get(f"{BASE_URL}/api/folders").json()
            ids2 = [f["id"] for f in radm]
            assert agent_fid in ids2 and admin_fid in ids2
        finally:
            admin_session.delete(f"{BASE_URL}/api/folders/{admin_fid}")
            admin_session.delete(f"{BASE_URL}/api/folders/{agent_fid}")

    def test_document_isolation(self, admin_session, agent_session):
        files = {"file": ("a.txt", b"x", "text/plain")}
        ra = admin_session.post(
            f"{BASE_URL}/api/documents",
            files=files,
            data={"title": "TEST_PHASE1_ISO_ADMIN_DOC", "description": "", "tags": ""},
        )
        admin_did = ra.json()["id"]
        rb = agent_session.post(
            f"{BASE_URL}/api/documents",
            files={"file": ("b.txt", b"x", "text/plain")},
            data={"title": "TEST_PHASE1_ISO_AGENT_DOC", "description": "", "tags": ""},
        )
        agent_did = rb.json()["id"]
        # Agent should NOT see admin doc
        agent_docs = agent_session.get(f"{BASE_URL}/api/documents").json()
        agent_ids = [d["id"] for d in agent_docs]
        assert agent_did in agent_ids
        assert admin_did not in agent_ids, "Agent leaked admin's document"
        # Admin sees both
        admin_docs = admin_session.get(f"{BASE_URL}/api/documents").json()
        admin_ids = [d["id"] for d in admin_docs]
        assert admin_did in admin_ids and agent_did in admin_ids
