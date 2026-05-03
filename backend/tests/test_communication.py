"""MHCGED iter6 - communication feature tests: messages, comments, inbox, announcements."""
import os
import uuid
import io

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


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=20)
    assert r.status_code == 200, r.text
    me = s.get(f"{BASE_URL}/api/auth/me", timeout=10).json()
    s.user_id = me["id"]
    s.user_name = me["name"]
    return s


@pytest.fixture(scope="module")
def agent_user(admin_session):
    suffix = uuid.uuid4().hex[:8]
    email = f"TEST_msg_{suffix}@mhcged.cg"
    password = "Agent@2026"
    r = admin_session.post(f"{BASE_URL}/api/users", json={
        "email": email, "password": password, "name": f"TEST Msg {suffix}", "role": "agent",
    }, timeout=15)
    assert r.status_code == 200, r.text
    user = r.json()
    yield {"id": user["id"], "email": email, "password": password, "name": user["name"]}
    admin_session.delete(f"{BASE_URL}/api/users/{user['id']}", timeout=15)


@pytest.fixture(scope="module")
def agent_user2(admin_session):
    suffix = uuid.uuid4().hex[:8]
    email = f"TEST_msg2_{suffix}@mhcged.cg"
    password = "Agent@2026"
    r = admin_session.post(f"{BASE_URL}/api/users", json={
        "email": email, "password": password, "name": f"TEST Msg2 {suffix}", "role": "agent",
    }, timeout=15)
    assert r.status_code == 200, r.text
    user = r.json()
    yield {"id": user["id"], "email": email, "password": password, "name": user["name"]}
    admin_session.delete(f"{BASE_URL}/api/users/{user['id']}", timeout=15)


@pytest.fixture()
def agent_session(agent_user):
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": agent_user["email"], "password": agent_user["password"]}, timeout=15)
    assert r.status_code == 200
    return s


@pytest.fixture()
def agent_session2(agent_user2):
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": agent_user2["email"], "password": agent_user2["password"]}, timeout=15)
    assert r.status_code == 200
    return s


# ============= Messaging =============
class TestMessaging:
    def test_send_message_success(self, admin_session, agent_user):
        r = admin_session.post(f"{BASE_URL}/api/messages", json={
            "to_user_id": agent_user["id"], "content": "Hello from admin"
        }, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["content"] == "Hello from admin"
        assert data["to_user_id"] == agent_user["id"]
        assert data["is_read"] is False
        assert "id" in data

    def test_reject_empty_content_no_attachment(self, admin_session, agent_user):
        r = admin_session.post(f"{BASE_URL}/api/messages", json={
            "to_user_id": agent_user["id"], "content": "   "
        }, timeout=15)
        assert r.status_code == 400

    def test_reject_self_message(self, admin_session):
        r = admin_session.post(f"{BASE_URL}/api/messages", json={
            "to_user_id": admin_session.user_id, "content": "self"
        }, timeout=15)
        assert r.status_code == 400

    def test_reject_invalid_recipient(self, admin_session):
        # valid ObjectId but not existing
        fake_id = "507f1f77bcf86cd799439011"
        r = admin_session.post(f"{BASE_URL}/api/messages", json={
            "to_user_id": fake_id, "content": "hi"
        }, timeout=15)
        assert r.status_code == 404

    def test_message_creates_notification(self, admin_session, agent_user, agent_session):
        agent_session.post(f"{BASE_URL}/api/notifications/read-all", timeout=10)
        r = admin_session.post(f"{BASE_URL}/api/messages", json={
            "to_user_id": agent_user["id"], "content": "ping for notification"
        }, timeout=15)
        assert r.status_code == 200
        notifs = agent_session.get(f"{BASE_URL}/api/notifications", timeout=15).json()
        assert notifs["unread_count"] >= 1
        msg_notifs = [n for n in notifs["items"] if n.get("link") == "/messages"]
        assert len(msg_notifs) >= 1

    def test_attachment_with_valid_doc(self, admin_session, agent_user):
        files = {"file": ("att.txt", b"attached", "text/plain")}
        data = {"title": f"TEST_ATT_{uuid.uuid4().hex[:6]}"}
        up = admin_session.post(f"{BASE_URL}/api/documents", files=files, data=data, timeout=20)
        assert up.status_code == 200
        doc = up.json()
        try:
            r = admin_session.post(f"{BASE_URL}/api/messages", json={
                "to_user_id": agent_user["id"], "content": "with file", "attachment_doc_id": doc["id"]
            }, timeout=15)
            assert r.status_code == 200
            m = r.json()
            assert m["attachment"] is not None
            assert m["attachment"]["id"] == doc["id"]
        finally:
            admin_session.delete(f"{BASE_URL}/api/documents/{doc['id']}", timeout=10)

    def test_attachment_invalid_doc_silent(self, admin_session, agent_user):
        r = admin_session.post(f"{BASE_URL}/api/messages", json={
            "to_user_id": agent_user["id"], "content": "ghost", "attachment_doc_id": "nope-not-a-doc"
        }, timeout=15)
        assert r.status_code == 200
        assert r.json()["attachment"] is None

    def test_conversations_list(self, admin_session, agent_user):
        r = admin_session.get(f"{BASE_URL}/api/messages/conversations", timeout=15)
        assert r.status_code == 200
        convs = r.json()
        assert isinstance(convs, list)
        peer_ids = [c["peer"]["id"] for c in convs]
        assert agent_user["id"] in peer_ids
        c = next(x for x in convs if x["peer"]["id"] == agent_user["id"])
        assert "last_message" in c and "unread_count" in c

    def test_conversation_thread_marks_read(self, admin_session, agent_user, agent_session):
        # Admin sends new message to agent
        admin_session.post(f"{BASE_URL}/api/messages", json={
            "to_user_id": agent_user["id"], "content": "to be read"
        }, timeout=15)
        # Agent fetches unread before reading thread
        before = agent_session.get(f"{BASE_URL}/api/messages/unread-count", timeout=10).json()["unread_count"]
        assert before >= 1
        # Agent loads thread with admin
        r = agent_session.get(f"{BASE_URL}/api/messages/conversation/{admin_session.user_id}", timeout=15)
        assert r.status_code == 200
        thread = r.json()
        assert "messages" in thread and "peer" in thread
        assert thread["peer"]["id"] == admin_session.user_id
        # After loading thread, unread count drops
        after = agent_session.get(f"{BASE_URL}/api/messages/unread-count", timeout=10).json()["unread_count"]
        assert after < before

    def test_unread_count_endpoint(self, agent_session):
        r = agent_session.get(f"{BASE_URL}/api/messages/unread-count", timeout=10)
        assert r.status_code == 200
        assert "unread_count" in r.json()
        assert isinstance(r.json()["unread_count"], int)


# ============= Comments =============
class TestComments:
    @pytest.fixture(scope="class")
    def doc(self, admin_session):
        files = {"file": ("c.txt", b"hello", "text/plain")}
        data = {"title": f"TEST_CDOC_{uuid.uuid4().hex[:6]}"}
        r = admin_session.post(f"{BASE_URL}/api/documents", files=files, data=data, timeout=20)
        assert r.status_code == 200
        d = r.json()
        yield d
        admin_session.delete(f"{BASE_URL}/api/documents/{d['id']}", timeout=10)

    def test_add_comment(self, admin_session, doc):
        r = admin_session.post(f"{BASE_URL}/api/documents/{doc['id']}/comments",
                               json={"content": "First comment"}, timeout=15)
        assert r.status_code == 200, r.text
        c = r.json()
        assert c["content"] == "First comment"
        assert c["doc_id"] == doc["id"]
        assert "id" in c

    def test_reject_empty_comment(self, admin_session, doc):
        r = admin_session.post(f"{BASE_URL}/api/documents/{doc['id']}/comments",
                               json={"content": "  "}, timeout=15)
        assert r.status_code == 400

    def test_list_comments(self, admin_session, doc):
        r = admin_session.get(f"{BASE_URL}/api/documents/{doc['id']}/comments", timeout=15)
        assert r.status_code == 200
        lst = r.json()
        assert isinstance(lst, list)
        assert any(x["content"] == "First comment" for x in lst)

    def test_no_access_returns_403(self, admin_session, doc, agent_session):
        # agent has no access
        r = agent_session.get(f"{BASE_URL}/api/documents/{doc['id']}/comments", timeout=15)
        assert r.status_code == 403
        r2 = agent_session.post(f"{BASE_URL}/api/documents/{doc['id']}/comments",
                                json={"content": "x"}, timeout=15)
        assert r2.status_code == 403

    def test_comment_notifies_owner(self, admin_session, agent_user, agent_session, doc):
        # Share doc with agent
        admin_session.post(f"{BASE_URL}/api/documents/{doc['id']}/share",
                           json={"user_ids": [agent_user["id"]]}, timeout=15)
        admin_session.post(f"{BASE_URL}/api/notifications/read-all", timeout=10)
        # Agent comments
        r = agent_session.post(f"{BASE_URL}/api/documents/{doc['id']}/comments",
                               json={"content": "Agent comment"}, timeout=15)
        assert r.status_code == 200
        # Admin (the doc owner) gets notified
        notifs = admin_session.get(f"{BASE_URL}/api/notifications", timeout=10).json()
        assert any("commenté" in n.get("message", "").lower() or "commentaire" in n.get("title", "").lower()
                   for n in notifs["items"])

    def test_delete_comment_author_ok(self, admin_session, doc):
        r = admin_session.post(f"{BASE_URL}/api/documents/{doc['id']}/comments",
                               json={"content": "to be deleted"}, timeout=15)
        c_id = r.json()["id"]
        rd = admin_session.delete(f"{BASE_URL}/api/comments/{c_id}", timeout=10)
        assert rd.status_code == 200

    def test_delete_comment_other_forbidden(self, admin_session, agent_user, agent_session, doc):
        # admin creates comment
        r = admin_session.post(f"{BASE_URL}/api/documents/{doc['id']}/comments",
                               json={"content": "admin comment"}, timeout=15)
        c_id = r.json()["id"]
        # Need agent to have access - already shared from previous test
        rd = agent_session.delete(f"{BASE_URL}/api/comments/{c_id}", timeout=10)
        assert rd.status_code == 403
        # admin cleanup
        admin_session.delete(f"{BASE_URL}/api/comments/{c_id}", timeout=10)


# ============= Inbox =============
class TestInbox:
    def test_inbox_only_shared_docs(self, admin_session, agent_user, agent_session):
        # Upload + share new doc
        files = {"file": ("inbox.txt", b"hi", "text/plain")}
        data = {"title": f"TEST_INBOX_{uuid.uuid4().hex[:6]}"}
        up = admin_session.post(f"{BASE_URL}/api/documents", files=files, data=data, timeout=20).json()
        try:
            admin_session.post(f"{BASE_URL}/api/documents/{up['id']}/share",
                               json={"user_ids": [agent_user["id"]]}, timeout=15)
            r = agent_session.get(f"{BASE_URL}/api/inbox", timeout=15)
            assert r.status_code == 200
            data = r.json()
            assert "items" in data and "unread_count" in data
            ids = [d["id"] for d in data["items"]]
            assert up["id"] in ids
            item = next(d for d in data["items"] if d["id"] == up["id"])
            assert item["is_read"] is False
        finally:
            admin_session.delete(f"{BASE_URL}/api/documents/{up['id']}", timeout=10)

    def test_inbox_mark_read(self, admin_session, agent_user, agent_session):
        files = {"file": ("inbox2.txt", b"hi", "text/plain")}
        data = {"title": f"TEST_INBOX_{uuid.uuid4().hex[:6]}"}
        up = admin_session.post(f"{BASE_URL}/api/documents", files=files, data=data, timeout=20).json()
        try:
            admin_session.post(f"{BASE_URL}/api/documents/{up['id']}/share",
                               json={"user_ids": [agent_user["id"]]}, timeout=15)
            r = agent_session.post(f"{BASE_URL}/api/inbox/{up['id']}/read", timeout=10)
            assert r.status_code == 200
            inb = agent_session.get(f"{BASE_URL}/api/inbox", timeout=15).json()
            it = next(d for d in inb["items"] if d["id"] == up["id"])
            assert it["is_read"] is True
        finally:
            admin_session.delete(f"{BASE_URL}/api/documents/{up['id']}", timeout=10)

    def test_inbox_mark_read_404_if_not_shared(self, admin_session, agent_session):
        files = {"file": ("priv.txt", b"hi", "text/plain")}
        data = {"title": f"TEST_PRIV_{uuid.uuid4().hex[:6]}"}
        up = admin_session.post(f"{BASE_URL}/api/documents", files=files, data=data, timeout=20).json()
        try:
            r = agent_session.post(f"{BASE_URL}/api/inbox/{up['id']}/read", timeout=10)
            assert r.status_code == 404
        finally:
            admin_session.delete(f"{BASE_URL}/api/documents/{up['id']}", timeout=10)


# ============= Announcements =============
class TestAnnouncements:
    def test_create_announcement_admin(self, admin_session):
        r = admin_session.post(f"{BASE_URL}/api/announcements", json={
            "title": f"TEST_ANN_{uuid.uuid4().hex[:6]}", "content": "Body"
        }, timeout=15)
        assert r.status_code == 200, r.text
        a = r.json()
        assert "id" in a
        admin_session.delete(f"{BASE_URL}/api/announcements/{a['id']}", timeout=10)

    def test_create_announcement_rejects_empty(self, admin_session):
        r = admin_session.post(f"{BASE_URL}/api/announcements", json={
            "title": "  ", "content": "b"
        }, timeout=15)
        assert r.status_code == 400
        r2 = admin_session.post(f"{BASE_URL}/api/announcements", json={
            "title": "t", "content": "  "
        }, timeout=15)
        assert r2.status_code == 400

    def test_agent_cannot_create(self, agent_session):
        r = agent_session.post(f"{BASE_URL}/api/announcements", json={
            "title": "x", "content": "y"
        }, timeout=15)
        assert r.status_code == 403

    def test_list_announcements_visible_to_all(self, admin_session, agent_session):
        title = f"TEST_ANN_{uuid.uuid4().hex[:6]}"
        c = admin_session.post(f"{BASE_URL}/api/announcements", json={
            "title": title, "content": "Visible to all"
        }, timeout=15).json()
        try:
            r = agent_session.get(f"{BASE_URL}/api/announcements", timeout=15)
            assert r.status_code == 200
            items = r.json()
            assert any(a["title"] == title for a in items)
        finally:
            admin_session.delete(f"{BASE_URL}/api/announcements/{c['id']}", timeout=10)

    def test_announcement_creates_notifications_for_users(self, admin_session, agent_user, agent_session):
        agent_session.post(f"{BASE_URL}/api/notifications/read-all", timeout=10)
        title = f"TEST_ANN_{uuid.uuid4().hex[:6]}"
        c = admin_session.post(f"{BASE_URL}/api/announcements", json={
            "title": title, "content": "Hello agents"
        }, timeout=15).json()
        try:
            notifs = agent_session.get(f"{BASE_URL}/api/notifications", timeout=10).json()
            assert any(title in n.get("title", "") for n in notifs["items"]), \
                f"No notification found for announcement title {title}"
        finally:
            admin_session.delete(f"{BASE_URL}/api/announcements/{c['id']}", timeout=10)

    def test_delete_announcement_admin_only(self, admin_session, agent_session):
        title = f"TEST_ANN_{uuid.uuid4().hex[:6]}"
        c = admin_session.post(f"{BASE_URL}/api/announcements", json={
            "title": title, "content": "delete me"
        }, timeout=15).json()
        # agent forbidden
        r = agent_session.delete(f"{BASE_URL}/api/announcements/{c['id']}", timeout=10)
        assert r.status_code == 403
        # admin ok
        r2 = admin_session.delete(f"{BASE_URL}/api/announcements/{c['id']}", timeout=10)
        assert r2.status_code == 200
