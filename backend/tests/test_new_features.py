"""MHCGED backend tests - NEW features: notifications, folder hierarchy, admin password reset."""
import os
import uuid

import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") if os.environ.get("REACT_APP_BACKEND_URL") else None
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL"):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")

ADMIN_EMAIL = "admin@mhcged.cg"
ADMIN_PASSWORD = "Admin@2026"


# ---------------- Fixtures ----------------
@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=20)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def agent_user(admin_session):
    """Create a temporary agent for tests; cleanup at end."""
    suffix = uuid.uuid4().hex[:8]
    email = f"TEST_agent_{suffix}@mhcged.cg"
    password = "Agent@2026"
    r = admin_session.post(f"{BASE_URL}/api/users", json={
        "email": email, "password": password, "name": f"TEST Agent {suffix}", "role": "agent",
    }, timeout=15)
    assert r.status_code == 200, f"Create agent failed: {r.text}"
    user = r.json()
    yield {"id": user["id"], "email": email, "password": password, "name": user["name"]}
    # Cleanup
    admin_session.delete(f"{BASE_URL}/api/users/{user['id']}", timeout=15)


@pytest.fixture()
def agent_session(agent_user):
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": agent_user["email"], "password": agent_user["password"]}, timeout=20)
    assert r.status_code == 200, f"Agent login failed: {r.text}"
    return s


# ---------------- Notifications ----------------
class TestNotifications:
    def test_list_notifications_shape(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/notifications", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data and isinstance(data["items"], list)
        assert "unread_count" in data and isinstance(data["unread_count"], int)

    def test_list_notifications_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/notifications", timeout=15)
        assert r.status_code == 401

    def test_mark_all_read(self, admin_session):
        r = admin_session.post(f"{BASE_URL}/api/notifications/read-all", timeout=15)
        assert r.status_code == 200
        # After mark-all-read, unread should be 0
        r2 = admin_session.get(f"{BASE_URL}/api/notifications", timeout=15)
        assert r2.status_code == 200
        assert r2.json()["unread_count"] == 0


# ---------------- Admin password reset ----------------
class TestPasswordReset:
    def test_reset_password_success_and_creates_notification(self, admin_session, agent_user):
        # Admin resets agent password
        new_pw = "NewPass@123"
        r = admin_session.post(
            f"{BASE_URL}/api/users/{agent_user['id']}/reset-password",
            json={"new_password": new_pw}, timeout=15,
        )
        assert r.status_code == 200, r.text
        assert "message" in r.json()

        # Agent can login with new password
        s = requests.Session()
        r2 = s.post(f"{BASE_URL}/api/auth/login", json={"email": agent_user["email"], "password": new_pw}, timeout=15)
        assert r2.status_code == 200

        # Agent sees a new notification
        r3 = s.get(f"{BASE_URL}/api/notifications", timeout=15)
        assert r3.status_code == 200
        data = r3.json()
        assert data["unread_count"] >= 1
        titles = [n.get("title", "") for n in data["items"]]
        assert any("Mot de passe" in t for t in titles), f"No password reset notification found: {titles}"

        # Mark single notification read
        notif_id = data["items"][0]["id"]
        r4 = s.post(f"{BASE_URL}/api/notifications/{notif_id}/read", timeout=15)
        assert r4.status_code == 200

        r5 = s.get(f"{BASE_URL}/api/notifications", timeout=15)
        assert r5.json()["unread_count"] == data["unread_count"] - 1

        # Reset back so agent_user.password stays valid for later cleanup
        agent_user["password"] = new_pw

    def test_reset_password_rejects_short(self, admin_session, agent_user):
        r = admin_session.post(
            f"{BASE_URL}/api/users/{agent_user['id']}/reset-password",
            json={"new_password": "abc"}, timeout=15,
        )
        assert r.status_code == 400

    def test_reset_password_non_admin_forbidden(self, agent_session, agent_user):
        r = agent_session.post(
            f"{BASE_URL}/api/users/{agent_user['id']}/reset-password",
            json={"new_password": "SomePass@123"}, timeout=15,
        )
        assert r.status_code == 403

    def test_reset_password_invalid_user_id(self, admin_session):
        r = admin_session.post(
            f"{BASE_URL}/api/users/not-an-objectid/reset-password",
            json={"new_password": "SomePass@123"}, timeout=15,
        )
        assert r.status_code == 400

    def test_reset_password_user_not_found(self, admin_session):
        # Valid ObjectId format but doesn't exist
        fake_id = "507f1f77bcf86cd799439011"
        r = admin_session.post(
            f"{BASE_URL}/api/users/{fake_id}/reset-password",
            json={"new_password": "SomePass@123"}, timeout=15,
        )
        assert r.status_code == 404


# ---------------- Folder Hierarchy ----------------
class TestFolderHierarchy:
    def test_create_child_folder(self, admin_session):
        # Create parent
        parent_name = f"TEST_Parent_{uuid.uuid4().hex[:6]}"
        rp = admin_session.post(f"{BASE_URL}/api/folders", json={"name": parent_name}, timeout=15)
        assert rp.status_code == 200
        parent = rp.json()
        assert parent["parent_id"] is None

        # Create child
        child_name = f"TEST_Child_{uuid.uuid4().hex[:6]}"
        rc = admin_session.post(
            f"{BASE_URL}/api/folders",
            json={"name": child_name, "parent_id": parent["id"]}, timeout=15,
        )
        assert rc.status_code == 200, rc.text
        child = rc.json()
        assert child["parent_id"] == parent["id"]

        # Listing returns both
        rl = admin_session.get(f"{BASE_URL}/api/folders", timeout=15)
        assert rl.status_code == 200
        all_folders = rl.json()
        ids = {f["id"]: f for f in all_folders}
        assert parent["id"] in ids
        assert child["id"] in ids
        assert ids[child["id"]]["parent_id"] == parent["id"]

        # Cleanup
        admin_session.delete(f"{BASE_URL}/api/folders/{child['id']}", timeout=15)
        admin_session.delete(f"{BASE_URL}/api/folders/{parent['id']}", timeout=15)

    def test_create_folder_with_invalid_parent_fails(self, admin_session):
        r = admin_session.post(
            f"{BASE_URL}/api/folders",
            json={"name": "TEST_Bad", "parent_id": "non-existent-id"}, timeout=15,
        )
        assert r.status_code == 400

    def test_update_folder_parent(self, admin_session):
        # Create 2 root folders
        a = admin_session.post(f"{BASE_URL}/api/folders", json={"name": f"TEST_A_{uuid.uuid4().hex[:4]}"}, timeout=15).json()
        b = admin_session.post(f"{BASE_URL}/api/folders", json={"name": f"TEST_B_{uuid.uuid4().hex[:4]}"}, timeout=15).json()
        # Move B under A
        r = admin_session.put(f"{BASE_URL}/api/folders/{b['id']}", json={"parent_id": a["id"]}, timeout=15)
        assert r.status_code == 200
        assert r.json()["parent_id"] == a["id"]
        # Cleanup
        admin_session.delete(f"{BASE_URL}/api/folders/{b['id']}", timeout=15)
        admin_session.delete(f"{BASE_URL}/api/folders/{a['id']}", timeout=15)


# ---------------- Document share notification ----------------
class TestShareNotification:
    def test_share_creates_notification_for_new_users_only(self, admin_session, agent_user, agent_session):
        # Clear agent notifications first
        agent_session.post(f"{BASE_URL}/api/notifications/read-all", timeout=15)
        before = agent_session.get(f"{BASE_URL}/api/notifications", timeout=15).json()
        before_count = len(before["items"])

        # Upload a doc as admin
        files = {"file": ("test.txt", b"hello", "text/plain")}
        data = {"title": f"TEST_DOC_{uuid.uuid4().hex[:6]}", "description": "test", "tags": ""}
        up = admin_session.post(f"{BASE_URL}/api/documents", files=files, data=data, timeout=20)
        assert up.status_code == 200, up.text
        doc = up.json()

        # Share with agent
        sh = admin_session.post(f"{BASE_URL}/api/documents/{doc['id']}/share", json={"user_ids": [agent_user["id"]]}, timeout=15)
        assert sh.status_code == 200

        after = agent_session.get(f"{BASE_URL}/api/notifications", timeout=15).json()
        assert len(after["items"]) == before_count + 1
        assert after["items"][0]["title"].lower().startswith("document partagé".lower()) or "partagé" in after["items"][0]["title"].lower()

        # Share again with same agent - should NOT create a new notification
        sh2 = admin_session.post(f"{BASE_URL}/api/documents/{doc['id']}/share", json={"user_ids": [agent_user["id"]]}, timeout=15)
        assert sh2.status_code == 200
        after2 = agent_session.get(f"{BASE_URL}/api/notifications", timeout=15).json()
        assert len(after2["items"]) == len(after["items"]), "Re-sharing with same user must not create a new notification"

        # Cleanup
        admin_session.delete(f"{BASE_URL}/api/documents/{doc['id']}", timeout=15)
