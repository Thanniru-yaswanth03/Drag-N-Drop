import pytest
from fastapi.testclient import TestClient
from main import app
import ai
import database

client = TestClient(app)


def test_ai_project_intelligence_intents():
    board_data = {
        "columns": [
            {"id": "c-1", "title": "Backlog", "cardIds": ["card-1"]},
            {"id": "c-2", "title": "Done", "cardIds": ["card-2"]},
        ],
        "cards": {
            "card-1": {
                "id": "card-1",
                "title": "Fix Critical Bug",
                "priority": "high",
                "dueDate": "2026-08-15",
                "assignee": "alex",
            },
            "card-2": {
                "id": "card-2",
                "title": "Initial Setup",
                "priority": "medium",
                "dueDate": None,
                "assignee": "alex",
            },
        },
    }

    # 1. Project summary intent
    summary_res = ai.smart_local_nlp("Summarize project", board_data)
    assert "Project Intelligence Summary" in summary_res["reply"]

    # 2. Workload analysis intent
    workload_res = ai.smart_local_nlp("Workload analysis", board_data)
    assert "Workload Distribution Analysis" in workload_res["reply"]

    # 3. Overdue task analysis intent
    overdue_res = ai.smart_local_nlp("Overdue tasks", board_data)
    assert "Upcoming & Overdue Task Analysis" in overdue_res["reply"]

    # 4. Organization suggestions intent
    org_res = ai.smart_local_nlp("Suggest organization", board_data)
    assert "Project Organization Recommendations" in org_res["reply"]


def test_rate_limiting_on_auth_endpoints():
    # Make multiple rapid requests to trigger rate limit threshold
    client_ip = "192.168.1.100"
    headers = {"X-Forwarded-For": client_ip}

    status_codes = []
    for _ in range(20):
        res = client.post(
            "/api/auth/login",
            json={"username": "invalid_user", "password": "wrong_password"},
            headers=headers,
        )
        status_codes.append(res.status_code)

    # At least one request should receive HTTP 429 Too Many Requests
    assert 429 in status_codes
