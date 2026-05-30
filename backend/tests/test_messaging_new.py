"""MHCGED iter9 - new messaging features: auto-share, delete, broadcast, search, read receipts."""
import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL"):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")

ADMIN_EMAIL = "admin@mhcged.cg"
ADMIN_PASSWORD = "Admin@2026"


def _login(email, password):
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}, timeout=20)
    assert r.status_code == 200, r.text
    me = s.get(f"{BASE_URL}/api/auth/me", timeout=10).json()
    s.user_id = me["id"]
    s.user_name = me["name"]
    s.role = me.get("role")
    return s


@pytest.fixture(scope="module")
def admin():
    return _login(ADMIN_EMAIL, ADMIN_PASSWORD)


@pytest.fixture(scope="module")
def two_agents(admin):
    """Create two agent users for testing."""
    created = []
    for i in range(2):
        suffix = uuid.uuid4().hex[:8]
        email = f"TEST_uitest_msg_{i}_{suffix}@example.com"
        password = "Agent@2026"
        r = admin.post(f"{BASE_URL}/api/users", json={
            "email": email, "password": password, "name": f"TEST AgentNew{i} {suffix}", "role": "agent",
        }, timeout=15)
        assert r.status_code == 200, r.text
        u = r.json()
        u["password"] = password
        u["email"] = email
        created.append(u)
    yield created
    for u in created:
        try:
            admin.delete(f"{BASE_URL}/api/users/{u['id']}", timeout=10)
        except Exception:
            pass


@pytest.fixture()
def agent_a(two_agents):
    return _login(two_agents[0]["email"], two_agents[0]["password"])


@pytest.fixture()
def agent_b(two_agents):
    return _login(two_agents[1]["email"], two_agents[1]["password"])


# ============== AUTO-SHARE ==============
class TestAutoShare:
    def test_send_message_with_attachment_auto_shares(self, admin, two_agents, agent_a):
        recipient_id = two_agents[0]["id"]
        # Admin uploads a private doc
        files = {"file": ("auto.txt", b"autoshare", "text/plain")}
        data = {"title": f"TEST_AUTO_{uuid.uuid4().hex[:6]}"}
        up = admin.post(f"{BASE_URL}/api/documents", files=files, data=data, timeout=20).json()
        try:
            # Before sending, agent should NOT see this doc
            inbox_before = agent_a.get(f"{BASE_URL}/api/inbox", timeout=10).json()
            assert up["id"] not in [d["id"] for d in inbox_before["items"]]
            # Send message with attachment
            r = admin.post(f"{BASE_URL}/api/messages", json={
                "to_user_id": recipient_id, "content": "share me", "attachment_doc_id": up["id"]
            }, timeout=15)
            assert r.status_code == 200, r.text
            # Doc's shared_with should now include recipient (verified via inbox)
            inbox_after = agent_a.get(f"{BASE_URL}/api/inbox", timeout=10).json()
            assert up["id"] in [d["id"] for d in inbox_after["items"]], "Recipient did not get auto-shared access"
        finally:
            admin.delete(f"{BASE_URL}/api/documents/{up['id']}", timeout=10)

    def test_broadcast_with_attachment_auto_shares_all(self, admin, two_agents, agent_a, agent_b):
        ids = [two_agents[0]["id"], two_agents[1]["id"]]
        files = {"file": ("b.txt", b"bcastshare", "text/plain")}
        data = {"title": f"TEST_BCAST_{uuid.uuid4().hex[:6]}"}
        up = admin.post(f"{BASE_URL}/api/documents", files=files, data=data, timeout=20).json()
        try:
            r = admin.post(f"{BASE_URL}/api/messages/broadcast", json={
                "to_user_ids": ids, "content": "broadcast attach", "attachment_doc_id": up["id"]
            }, timeout=15)
            assert r.status_code == 200, r.text
            assert r.json()["sent"] == 2
            # Both agents should see in inbox
            ib_a = agent_a.get(f"{BASE_URL}/api/inbox", timeout=10).json()
            ib_b = agent_b.get(f"{BASE_URL}/api/inbox", timeout=10).json()
            assert up["id"] in [d["id"] for d in ib_a["items"]]
            assert up["id"] in [d["id"] for d in ib_b["items"]]
        finally:
            admin.delete(f"{BASE_URL}/api/documents/{up['id']}", timeout=10)


# ============== DELETE ==============
class TestDeleteMessage:
    def test_sender_can_delete_own(self, admin, two_agents):
        recipient = two_agents[0]["id"]
        r = admin.post(f"{BASE_URL}/api/messages", json={
            "to_user_id": recipient, "content": "to delete"
        }, timeout=15)
        mid = r.json()["id"]
        rd = admin.delete(f"{BASE_URL}/api/messages/{mid}", timeout=10)
        assert rd.status_code == 200, rd.text

    def test_non_sender_non_admin_403(self, admin, two_agents, agent_a, agent_b):
        # agent_a sends to agent_b; agent_b tries to delete -> 403
        r = agent_a.post(f"{BASE_URL}/api/messages", json={
            "to_user_id": two_agents[1]["id"], "content": "from A to B"
        }, timeout=15)
        assert r.status_code == 200, r.text
        mid = r.json()["id"]
        rd = agent_b.delete(f"{BASE_URL}/api/messages/{mid}", timeout=10)
        assert rd.status_code == 403, rd.text
        assert "propres messages" in rd.json().get("detail", "")

    def test_admin_can_delete_any(self, admin, two_agents, agent_a):
        r = agent_a.post(f"{BASE_URL}/api/messages", json={
            "to_user_id": two_agents[1]["id"], "content": "admin will delete this"
        }, timeout=15)
        mid = r.json()["id"]
        rd = admin.delete(f"{BASE_URL}/api/messages/{mid}", timeout=10)
        assert rd.status_code == 200, rd.text

    def test_deleted_msg_not_in_conversation(self, admin, two_agents):
        recipient = two_agents[0]["id"]
        marker = f"DELME_{uuid.uuid4().hex[:6]}"
        r = admin.post(f"{BASE_URL}/api/messages", json={
            "to_user_id": recipient, "content": marker
        }, timeout=15)
        mid = r.json()["id"]
        admin.delete(f"{BASE_URL}/api/messages/{mid}", timeout=10)
        conv = admin.get(f"{BASE_URL}/api/messages/conversation/{recipient}", timeout=10).json()
        contents = [m.get("content") for m in conv.get("messages", [])]
        assert marker not in contents, f"Deleted message still appears: {contents}"

    def test_deleted_msg_not_in_conversations_last(self, admin, two_agents):
        recipient = two_agents[0]["id"]
        marker = f"LASTDEL_{uuid.uuid4().hex[:6]}"
        r = admin.post(f"{BASE_URL}/api/messages", json={
            "to_user_id": recipient, "content": marker
        }, timeout=15)
        mid = r.json()["id"]
        admin.delete(f"{BASE_URL}/api/messages/{mid}", timeout=10)
        convs = admin.get(f"{BASE_URL}/api/messages/conversations", timeout=10).json()
        for c in convs:
            if c["peer"]["id"] == recipient:
                assert c["last_message"].get("content") != marker, "Deleted message appears as last_message"

    def test_unread_count_excludes_deleted(self, admin, two_agents, agent_a):
        # admin sends, then deletes; agent_a's unread should not include it
        before = agent_a.get(f"{BASE_URL}/api/messages/unread-count", timeout=10).json()["unread_count"]
        r = admin.post(f"{BASE_URL}/api/messages", json={
            "to_user_id": two_agents[0]["id"], "content": "unread-del"
        }, timeout=15)
        mid = r.json()["id"]
        admin.delete(f"{BASE_URL}/api/messages/{mid}", timeout=10)
        after = agent_a.get(f"{BASE_URL}/api/messages/unread-count", timeout=10).json()["unread_count"]
        # Sent then deleted -> should not have increased
        assert after <= before, f"Unread count includes deleted msg: before={before} after={after}"


# ============== BROADCAST ==============
class TestBroadcast:
    def test_broadcast_basic(self, admin, two_agents):
        ids = [two_agents[0]["id"], two_agents[1]["id"]]
        r = admin.post(f"{BASE_URL}/api/messages/broadcast", json={
            "to_user_ids": ids, "content": f"bc_{uuid.uuid4().hex[:6]}"
        }, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json()["sent"] == 2

    def test_broadcast_empty_content_no_attach_400(self, admin, two_agents):
        r = admin.post(f"{BASE_URL}/api/messages/broadcast", json={
            "to_user_ids": [two_agents[0]["id"]], "content": "   "
        }, timeout=15)
        assert r.status_code == 400, r.text

    def test_broadcast_empty_recipients_400(self, admin):
        r = admin.post(f"{BASE_URL}/api/messages/broadcast", json={
            "to_user_ids": [], "content": "hi"
        }, timeout=15)
        assert r.status_code == 400

    def test_broadcast_only_self_400(self, admin):
        r = admin.post(f"{BASE_URL}/api/messages/broadcast", json={
            "to_user_ids": [admin.user_id], "content": "self"
        }, timeout=15)
        assert r.status_code == 400

    def test_broadcast_self_filtered(self, admin, two_agents):
        ids = [admin.user_id, two_agents[0]["id"]]
        r = admin.post(f"{BASE_URL}/api/messages/broadcast", json={
            "to_user_ids": ids, "content": "selfsilent"
        }, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json()["sent"] == 1


# ============== SEARCH ==============
class TestSearch:
    def test_search_conversations_by_peer_name(self, admin, two_agents, agent_a):
        # ensure there's a conversation by sending a message
        admin.post(f"{BASE_URL}/api/messages", json={
            "to_user_id": two_agents[0]["id"], "content": "hi"
        }, timeout=15)
        # Search by part of peer name
        token = two_agents[0]["name"].split()[0][:6]  # e.g. 'TEST'
        r = admin.get(f"{BASE_URL}/api/messages/conversations", params={"search": token.lower()}, timeout=10)
        assert r.status_code == 200
        convs = r.json()
        assert any(c["peer"]["id"] == two_agents[0]["id"] for c in convs), \
            f"Expected agent_a in search results, got peers: {[c['peer']['name'] for c in convs]}"

    def test_search_conversations_no_match(self, admin):
        r = admin.get(f"{BASE_URL}/api/messages/conversations", params={"search": "zzzz_nomatch_xyz"}, timeout=10)
        assert r.status_code == 200
        assert r.json() == []

    def test_search_thread_filter(self, admin, two_agents):
        # The current backend get_conversation does NOT support ?search=, expect graceful behavior
        marker = f"NEEDLE_{uuid.uuid4().hex[:6]}"
        admin.post(f"{BASE_URL}/api/messages", json={
            "to_user_id": two_agents[0]["id"], "content": marker
        }, timeout=15)
        admin.post(f"{BASE_URL}/api/messages", json={
            "to_user_id": two_agents[0]["id"], "content": "other content"
        }, timeout=15)
        r = admin.get(f"{BASE_URL}/api/messages/conversation/{two_agents[0]['id']}",
                      params={"search": marker.lower()}, timeout=10)
        assert r.status_code == 200, r.text
        contents = [m.get("content") for m in r.json().get("messages", [])]
        assert any(marker in c for c in contents), "Marker not found in search results"
        # If search is implemented, "other content" must be excluded; if not, this assertion fails
        assert all(marker in c for c in contents), \
            f"Thread search should filter — got non-matching content: {contents}"


# ============== SECURITY: attachment access ==============
class TestAttachmentAccessSecurity:
    def test_non_admin_cannot_attach_doc_without_access(self, admin, two_agents, agent_a, agent_b):
        """Agent A should NOT be able to attach a doc they don't own/aren't shared with."""
        # Admin uploads a private doc (only admin owns it)
        files = {"file": ("sec.txt", b"secret", "text/plain")}
        data = {"title": f"TEST_SEC_{uuid.uuid4().hex[:6]}"}
        up = admin.post(f"{BASE_URL}/api/documents", files=files, data=data, timeout=20).json()
        try:
            # Agent A tries to send to Agent B with this doc attached
            r = agent_a.post(f"{BASE_URL}/api/messages", json={
                "to_user_id": two_agents[1]["id"],
                "content": "leak attempt",
                "attachment_doc_id": up["id"],
            }, timeout=15)
            assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"
            assert "n'avez pas accès" in r.json().get("detail", "")
            # Verify agent_b did NOT get auto-shared access
            ib_b = agent_b.get(f"{BASE_URL}/api/inbox", timeout=10).json()
            assert up["id"] not in [d["id"] for d in ib_b["items"]], "Doc was leaked despite 403"
        finally:
            admin.delete(f"{BASE_URL}/api/documents/{up['id']}", timeout=10)

    def test_non_admin_cannot_broadcast_doc_without_access(self, admin, two_agents, agent_a, agent_b):
        files = {"file": ("secb.txt", b"secretbc", "text/plain")}
        data = {"title": f"TEST_SECBC_{uuid.uuid4().hex[:6]}"}
        up = admin.post(f"{BASE_URL}/api/documents", files=files, data=data, timeout=20).json()
        try:
            r = agent_a.post(f"{BASE_URL}/api/messages/broadcast", json={
                "to_user_ids": [two_agents[1]["id"]],
                "content": "bc leak",
                "attachment_doc_id": up["id"],
            }, timeout=15)
            assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"
            assert "n'avez pas accès" in r.json().get("detail", "")
        finally:
            admin.delete(f"{BASE_URL}/api/documents/{up['id']}", timeout=10)

    def test_non_admin_can_attach_doc_already_shared_with_them(self, admin, two_agents, agent_a, agent_b):
        """If admin shares a doc with agent_a, agent_a can then forward it to agent_b."""
        files = {"file": ("ok.txt", b"ok", "text/plain")}
        data = {"title": f"TEST_OKSEC_{uuid.uuid4().hex[:6]}"}
        up = admin.post(f"{BASE_URL}/api/documents", files=files, data=data, timeout=20).json()
        try:
            # Admin shares with agent_a via direct message
            admin.post(f"{BASE_URL}/api/messages", json={
                "to_user_id": two_agents[0]["id"], "content": "for you", "attachment_doc_id": up["id"]
            }, timeout=15)
            # Now agent_a (already in shared_with) should be allowed to attach it to agent_b
            r = agent_a.post(f"{BASE_URL}/api/messages", json={
                "to_user_id": two_agents[1]["id"], "content": "forwarded", "attachment_doc_id": up["id"]
            }, timeout=15)
            assert r.status_code == 200, r.text
        finally:
            admin.delete(f"{BASE_URL}/api/documents/{up['id']}", timeout=10)


# ============== READ RECEIPTS ==============
class TestReadReceipts:
    def test_read_receipt_flow(self, admin, two_agents, agent_a):
        # Admin sends message to agent_a
        marker = f"READ_{uuid.uuid4().hex[:6]}"
        r = admin.post(f"{BASE_URL}/api/messages", json={
            "to_user_id": two_agents[0]["id"], "content": marker
        }, timeout=15)
        assert r.status_code == 200
        mid = r.json()["id"]
        # Initially in admin's conv (sent) is_read should be False
        conv1 = admin.get(f"{BASE_URL}/api/messages/conversation/{two_agents[0]['id']}", timeout=10).json()
        msg1 = next((m for m in conv1["messages"] if m["id"] == mid), None)
        assert msg1 is not None
        assert msg1["is_read"] is False
        # Agent A opens conversation -> marks as read
        agent_a.get(f"{BASE_URL}/api/messages/conversation/{admin.user_id}", timeout=10)
        # Admin re-fetches: msg should be is_read=True
        conv2 = admin.get(f"{BASE_URL}/api/messages/conversation/{two_agents[0]['id']}", timeout=10).json()
        msg2 = next((m for m in conv2["messages"] if m["id"] == mid), None)
        assert msg2 is not None
        assert msg2["is_read"] is True, f"Message should be marked read after recipient fetches conv: {msg2}"
