import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_header(client):
    res = client.post("/api/auth/login", json={
        "email": "rajesh.sharma@lumensystems.in",
        "password": "Password@123"
    })
    assert res.status_code == 200
    token = res.json()["token"]
    return {"Authorization": f"Bearer {token}"}

def test_web_chat_endpoint_schema_contract(client, auth_header):
    """Integration test: /api/ai/chat returns expected schema with content, sources, confidence, and warnings."""
    res = client.post(
        "/api/ai/chat",
        headers=auth_header,
        json={"message": "What is the insulation resistance required for LED lamps under IS 16102?"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "content" in data
    assert "sources" in data
    assert "confidence" in data
    assert "insufficient_evidence" in data
    assert "role" in data
    assert data["role"] == "assistant"
    assert len(data["sources"]) > 0

    # Validate source citation structure matching frontend SourceReferenceItem
    src = data["sources"][0]
    assert "id" in src
    assert "title" in src
    assert "documentRef" in src
    assert "section" in src
    assert "excerpt" in src
    assert "sourceUrl" in src

def test_authorized_application_context_chat(client, auth_header):
    """Integration test: authorized user querying with their own applicationId receives contextual grounding."""
    res = client.post(
        "/api/ai/chat",
        headers=auth_header,
        json={
            "message": "What test report is required for this product?",
            "applicationId": "APP-001"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["insufficient_evidence"] is False
    assert len(data["sources"]) > 0

def test_whatsapp_webhook_verification(client, monkeypatch):
    """Integration test: WhatsApp Cloud API webhook hub verification challenge."""
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "isense_sih_2025_token")
    res = client.get(
        "/api/webhook/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "isense_sih_2025_token",
            "hub.challenge": "11223344"
        }
    )
    assert res.status_code == 200
    assert res.text == "11223344"

def test_whatsapp_incoming_message_pipeline(client):
    """Integration test: WhatsApp webhook handles incoming message, retrieves evidence, responds, and deduplicates retries."""
    import uuid
    import json
    import os
    import hmac
    import hashlib

    test_msg_id = f"wamid.{uuid.uuid4().hex}"
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WHATSAPP_BIZ_001",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "12345", "phone_number_id": "999"},
                    "messages": [{
                        "from": "919876543210",
                        "id": test_msg_id,
                        "timestamp": "1741500000",
                        "text": {"body": "What standard applies to ceiling fans?"},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }

    raw_body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    app_secret = os.getenv("WHATSAPP_APP_SECRET", "").strip().strip('"').strip("'")
    if app_secret:
        sig = hmac.new(app_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        headers["X-Hub-Signature-256"] = f"sha256={sig}"

    # First delivery: processed successfully through RAG
    res = client.post("/api/webhook/whatsapp", content=raw_body, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "374" in data["response"] or len(data["sources"]) > 0
    assert "sources" in data

    # Immediate retry: deduplicated safely without double-processing
    retry_res = client.post("/api/webhook/whatsapp", content=raw_body, headers=headers)
    assert retry_res.status_code == 200
    retry_data = retry_res.json()
    assert retry_data["status"] == "ok"
    assert retry_data["message"] == "duplicate_message_ignored"

def test_document_upload_and_isolation(client, auth_header):
    """Integration test: authorized user uploads document; document is isolated and visible to owner."""
    res = client.post(
        "/api/documents/upload",
        headers=auth_header,
        data={"applicationId": "APP-001", "category": "Test Report"},
        files={"file": ("test_report_is16102.pdf", b"%PDF-1.4 Safety Test Data", "application/pdf")}
    )
    assert res.status_code == 200
    doc = res.json()
    assert doc["applicationId"] == "APP-001"
    assert doc["privacyClassification"] == "applicant_private"
    assert "doc-" in doc["id"]

    # Verify document is visible in applicant documents list
    docs_res = client.get("/api/applications/APP-001/documents", headers=auth_header)
    assert docs_res.status_code == 200
    doc_ids = [d["id"] for d in docs_res.json()]
    assert doc["id"] in doc_ids

def test_search_bis_endpoint(client):
    """Integration test: /api/bis/search returns verified standards."""
    res = client.get("/api/bis/search", params={"query": "Helmet"})
    assert res.status_code == 200
    standards = res.json()
    assert len(standards) > 0
    assert any("4151" in s["isNumber"] for s in standards)
