"""MHCGED backend tests - Monthly reports feature (admin only)."""
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


# ---------- Fixtures ----------
@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=20)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def temp_agent(admin_session):
    suffix = uuid.uuid4().hex[:8]
    email = f"TEST_rep_agent_{suffix}@mhcged.cg"
    pw = "Agent@2026"
    r = admin_session.post(f"{BASE_URL}/api/users", json={
        "email": email, "password": pw, "name": f"TEST RepAgent {suffix}", "role": "agent",
    }, timeout=15)
    assert r.status_code == 200, r.text
    user = r.json()
    yield {"id": user["id"], "email": email, "password": pw, "name": user["name"]}
    admin_session.delete(f"{BASE_URL}/api/users/{user['id']}", timeout=15)


@pytest.fixture()
def agent_session(temp_agent):
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": temp_agent["email"], "password": temp_agent["password"]}, timeout=20)
    assert r.status_code == 200, r.text
    return s


# ---------- Preview JSON ----------
class TestReportsPreview:
    def test_monthly_preview_admin_ok(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/reports/monthly", params={"year": 2026, "month": 5}, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "top_docs" in data and isinstance(data["top_docs"], list)
        assert "top_agents" in data and isinstance(data["top_agents"], list)
        assert "scope_label" in data and isinstance(data["scope_label"], str)
        assert data["scope_label"] == "Tous les agents"

    def test_monthly_preview_with_agent_filter_scope_label(self, admin_session, temp_agent):
        r = admin_session.get(
            f"{BASE_URL}/api/reports/monthly",
            params={"year": 2026, "month": 5, "agent_id": temp_agent["id"]},
            timeout=20,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["scope_label"].startswith("Agent : ")
        assert temp_agent["name"] in data["scope_label"]

    def test_monthly_preview_non_admin_forbidden(self, agent_session):
        r = agent_session.get(f"{BASE_URL}/api/reports/monthly", params={"year": 2026, "month": 5}, timeout=15)
        assert r.status_code == 403

    def test_monthly_preview_unauthenticated(self):
        r = requests.get(f"{BASE_URL}/api/reports/monthly", params={"year": 2026, "month": 5}, timeout=15)
        assert r.status_code == 401

    def test_monthly_preview_invalid_month_zero(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/reports/monthly", params={"year": 2026, "month": 0}, timeout=15)
        assert r.status_code in (400, 422)

    def test_monthly_preview_invalid_month_thirteen(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/reports/monthly", params={"year": 2026, "month": 13}, timeout=15)
        assert r.status_code in (400, 422)


# ---------- PDF download ----------
class TestReportsPDF:
    def test_monthly_pdf_admin_returns_valid_pdf(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/reports/monthly/pdf", params={"year": 2026, "month": 5}, timeout=60)
        assert r.status_code == 200, r.text[:300]
        assert r.headers.get("content-type", "").startswith("application/pdf")
        cd = r.headers.get("content-disposition", "")
        assert "attachment" in cd.lower()
        assert "rapport-mhcged-2026-05.pdf" in cd
        assert len(r.content) > 1000
        assert r.content[:4] == b"%PDF"

    def test_monthly_pdf_non_admin_forbidden(self, agent_session):
        r = agent_session.get(f"{BASE_URL}/api/reports/monthly/pdf", params={"year": 2026, "month": 5}, timeout=20)
        assert r.status_code == 403

    def test_monthly_pdf_invalid_month(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/reports/monthly/pdf", params={"year": 2026, "month": 13}, timeout=20)
        assert r.status_code in (400, 422)

    def test_monthly_pdf_logs_activity(self, admin_session):
        # Trigger a generation
        r = admin_session.get(f"{BASE_URL}/api/reports/monthly/pdf", params={"year": 2026, "month": 7}, timeout=60)
        assert r.status_code == 200

        # Check activity logs include action='report_generated'
        rl = admin_session.get(f"{BASE_URL}/api/activity-logs", timeout=15)
        # Endpoint may differ; if not 200, look for alt route
        if rl.status_code != 200:
            rl = admin_session.get(f"{BASE_URL}/api/activity", timeout=15)
        assert rl.status_code == 200, f"Activity logs endpoint failed: {rl.status_code} {rl.text[:200]}"
        items = rl.json() if isinstance(rl.json(), list) else rl.json().get("items", [])
        actions = [it.get("action") for it in items]
        assert "report_generated" in actions, f"report_generated not found in activity logs: {actions[:10]}"
