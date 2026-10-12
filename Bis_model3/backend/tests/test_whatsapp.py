"""
Automated Test Suite for ISense WhatsApp Cloud API Integration.
Covers all 13 core requirements:
1. Successful webhook verification (hub.challenge)
2. Incorrect verification token (403 Forbidden)
3. Valid Meta request signature (HMAC-SHA256 constant-time)
4. Invalid or missing request signature (401/403)
5. Incoming text messages processed through grounded RAG
6. Duplicate message ID suppression via durable store
7. Status-only webhook events safely acknowledged without RAG
8. Malformed payloads (broken JSON, non-object) handled safely (400)
9. RAG exceptions handled gracefully without leaking stack traces
10. Missing evidence uncertainty handling with official BIS portals
11. Successful outbound WhatsApp API reply via mocked Meta Graph API
12. Meta API errors and timeouts handled safely
13. Status endpoint reporting and zero secret disclosure across all endpoints
"""

import os
import json
import uuid
import hmac
import hashlib
import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import httpx

from main import app
from whatsapp_service import (
    WhatsAppConfig,
    verify_webhook_signature,
    format_whatsapp_message,
    split_whatsapp_message,
    durable_message_store,
    whatsapp_client
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def mock_meta_client():
    """Mock external Meta WhatsApp Cloud API outbound requests across tests."""
    with patch("whatsapp_service.httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "messaging_product": "whatsapp",
            "contacts": [{"input": "919876543210", "wa_id": "919876543210"}],
            "messages": [{"id": "wamid.outbound_mock_123"}]
        }
        mock_post.return_value = mock_resp
        yield mock_post


def compute_meta_signature(body_bytes: bytes, app_secret: str) -> str:
    """Computes valid X-Hub-Signature-256 header value for tests."""
    digest = hmac.new(app_secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def post_signed_webhook(client: TestClient, payload: dict | bytes, app_secret: str = None):
    """Helper to post webhook with valid HMAC signature if app_secret is set."""
    if isinstance(payload, bytes):
        raw_body = payload
    else:
        raw_body = json.dumps(payload).encode("utf-8")

    secret = app_secret if app_secret is not None else WhatsAppConfig.from_env().app_secret
    headers = {"Content-Type": "application/json"}
    if secret:
        headers["X-Hub-Signature-256"] = compute_meta_signature(raw_body, secret)

    return client.post("/api/webhook/whatsapp", content=raw_body, headers=headers)


# ==============================================================================
# 1 & 2. Webhook Verification Tests (GET /api/webhook/whatsapp)
# ==============================================================================

def test_webhook_verification_success(client, monkeypatch):
    """Scenario 1: Meta webhook verification succeeds with matching token."""
    test_token = "my_strong_verify_token_999"
    test_challenge = "meta_challenge_12345678"
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", test_token)

    res = client.get(
        "/api/webhook/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": test_token,
            "hub.challenge": test_challenge
        }
    )
    assert res.status_code == 200
    assert res.text == test_challenge


def test_webhook_verification_incorrect_token(client, monkeypatch):
    """Scenario 2: Meta webhook verification fails with 403 on incorrect token."""
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "valid_secret_token")

    res = client.get(
        "/api/webhook/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_attacker_token",
            "hub.challenge": "123456"
        }
    )
    assert res.status_code == 403
    assert "detail" in res.json()


def test_webhook_verification_invalid_mode(client, monkeypatch):
    """Scenario 2b: Verification fails when hub.mode is not 'subscribe'."""
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "valid_secret_token")

    res = client.get(
        "/api/webhook/whatsapp",
        params={
            "hub.mode": "unsubscribe",
            "hub.verify_token": "valid_secret_token",
            "hub.challenge": "123456"
        }
    )
    assert res.status_code == 403


def test_webhook_verification_unconfigured_server(client, monkeypatch):
    """Scenario 2c: Verification fails when server has no token configured."""
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "")

    res = client.get(
        "/api/webhook/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "any_token",
            "hub.challenge": "123456"
        }
    )
    assert res.status_code == 403


# ==============================================================================
# 3 & 4. Signature Verification Tests (POST /api/webhook/whatsapp)
# ==============================================================================

def test_valid_meta_request_signature(client, monkeypatch):
    """Scenario 3: Valid X-Hub-Signature-256 HMAC-SHA256 signature accepted."""
    test_secret = "test_meta_app_secret_12345"
    monkeypatch.setenv("WHATSAPP_APP_SECRET", test_secret)

    test_msg_id = f"wamid.{uuid.uuid4().hex}"
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "BIZ_1",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "from": "919876543210",
                        "id": test_msg_id,
                        "timestamp": "1741500000",
                        "text": {"body": "IS 16102"},
                        "type": "text"
                    }]
                }
            }]
        }]
    }

    raw_body = json.dumps(payload).encode("utf-8")
    sig_header = compute_meta_signature(raw_body, test_secret)

    res = client.post(
        "/api/webhook/whatsapp",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": sig_header}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "success"


def test_invalid_meta_request_signature(client, monkeypatch):
    """Scenario 4a: Webhook rejects request with invalid HMAC signature (403)."""
    test_secret = "test_meta_app_secret_12345"
    monkeypatch.setenv("WHATSAPP_APP_SECRET", test_secret)

    raw_body = b'{"object": "whatsapp_business_account", "entry": []}'
    bad_sig = "sha256=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

    res = client.post(
        "/api/webhook/whatsapp",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": bad_sig}
    )
    assert res.status_code == 403
    assert "Invalid request signature" in res.json()["detail"]


def test_missing_meta_request_signature(client, monkeypatch):
    """Scenario 4b: Webhook rejects request with missing signature when secret is configured (401)."""
    test_secret = "test_meta_app_secret_12345"
    monkeypatch.setenv("WHATSAPP_APP_SECRET", test_secret)

    raw_body = b'{"object": "whatsapp_business_account", "entry": []}'

    res = client.post(
        "/api/webhook/whatsapp",
        content=raw_body,
        headers={"Content-Type": "application/json"}
    )
    assert res.status_code == 401
    assert "Missing X-Hub-Signature-256" in res.json()["detail"]


# ==============================================================================
# 5 & 6. Incoming Text Messages & Deduplication
# ==============================================================================

def test_incoming_text_message_processing(client):
    """Scenario 5: Incoming text message processes through RAG with citations."""
    unique_msg_id = f"wamid.{uuid.uuid4().hex}"
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "BIZ_1",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "from": "919988776655",
                        "id": unique_msg_id,
                        "timestamp": "1741500000",
                        "text": {"body": "What standard applies to helmets?"},
                        "type": "text"
                    }]
                }
            }]
        }]
    }

    res = post_signed_webhook(client, payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["recipient"] == "919988776655"
    assert "4151" in data["response"] or len(data["sources"]) > 0
    assert "disclaimer" in data


def test_hi_receives_greeting(client):
    """Requirement 7.1: 'Hi' receives the welcoming greeting message."""
    test_id = f"wamid.{uuid.uuid4().hex}"
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "BIZ_1",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "from": "919876543210",
                        "id": test_id,
                        "timestamp": "1741500000",
                        "text": {"body": "Hi"},
                        "type": "text"
                    }]
                }
            }]
        }]
    }
    res = post_signed_webhook(client, payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "Welcome to ISense" in data["response"]
    assert len(data.get("sources", [])) == 0


def test_rc_car_reaches_rag_engine_not_greeting(client):
    """Requirement 7.2: 'Rc car' must reach the RAG engine and not trigger the generic greeting."""
    test_id = f"wamid.{uuid.uuid4().hex}"
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "BIZ_1",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "from": "919876543210",
                        "id": test_id,
                        "timestamp": "1741500000",
                        "text": {"body": "Rc car"},
                        "type": "text"
                    }]
                }
            }]
        }]
    }
    res = post_signed_webhook(client, payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    # Must NOT be the welcome greeting
    assert "Welcome to ISense — Your BIS Regulatory Assistant" not in data["response"]
    # Must ground in Toys standard IS 9873 or provide regulatory guidance
    assert "9873" in data["response"] or "Toy" in data["response"] or len(data.get("sources", [])) > 0


def test_led_lamps_reaches_rag_engine_returns_answer(client):
    """Requirement 7.3: 'What standard applies to LED lamps?' returns IS 16102 answer."""
    test_id = f"wamid.{uuid.uuid4().hex}"
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "BIZ_1",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "from": "919876543210",
                        "id": test_id,
                        "timestamp": "1741500000",
                        "text": {"body": "What standard applies to LED lamps?"},
                        "type": "text"
                    }]
                }
            }]
        }]
    }
    res = post_signed_webhook(client, payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "16102" in data["response"]
    assert len(data.get("sources", [])) > 0


def test_duplicate_message_ids_suppression(client):
    """Scenario 6: Subsequent webhook retries with same message ID are deduplicated."""
    shared_id = f"wamid.duplicate_test_{uuid.uuid4().hex[:8]}"
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "BIZ_1",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "from": "919111222333",
                        "id": shared_id,
                        "timestamp": "1741500000",
                        "text": {"body": "Insulation resistance for LED lamps"},
                        "type": "text"
                    }]
                }
            }]
        }]
    }

    # 1st call: fresh message
    res1 = post_signed_webhook(client, payload)
    assert res1.status_code == 200
    assert res1.json()["status"] == "success"

    # 2nd call: duplicate webhook retry from Meta
    res2 = post_signed_webhook(client, payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["status"] == "ok"
    assert data2["message"] == "duplicate_message_ignored"


# ==============================================================================
# 7. Status-Only Webhook Events (sent, delivered, read)
# ==============================================================================

def test_status_only_webhook_events(client):
    """Scenario 7: Meta status notifications safely acknowledged without RAG invocation."""
    status_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "BIZ_1",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"phone_number_id": "12345"},
                    "statuses": [{
                        "id": "wamid.HBgLMTEyMjMzNDQ1NQ",
                        "status": "delivered",
                        "timestamp": "1741500050",
                        "recipient_id": "919876543210"
                    }]
                }
            }]
        }]
    }

    res = post_signed_webhook(client, status_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["event"] == "status_update_acknowledged"


# ==============================================================================
# 8. Malformed Payloads Handled Safely
# ==============================================================================

def test_malformed_json_payload(client):
    """Scenario 8a: Broken non-JSON payload returns 400 Bad Request."""
    broken_bytes = b"{broken: true, non_json..."
    res = post_signed_webhook(client, broken_bytes)
    assert res.status_code == 400
    assert "Malformed JSON payload" in res.json()["detail"]


def test_malformed_json_non_dict_payload(client):
    """Scenario 8b: Valid JSON that is a list instead of a dict returns 400."""
    list_bytes = b'["not", "a", "dict"]'
    res = post_signed_webhook(client, list_bytes)
    assert res.status_code == 400
    assert "expected JSON object" in res.json()["detail"]


def test_empty_entry_payload(client):
    """Scenario 8c: Payload with empty entry list returns 200 OK cleanly."""
    res = post_signed_webhook(client, {"object": "whatsapp_business_account", "entry": []})
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


# ==============================================================================
# 9 & 10. RAG Exceptions & Missing Evidence / Uncertainty Handling
# ==============================================================================

def test_rag_exception_handling(client):
    """Scenario 9: Internal RAG exception does not crash webhook or leak traces."""
    test_id = f"wamid.{uuid.uuid4().hex}"
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "BIZ_1",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "from": "919999999999",
                        "id": test_id,
                        "timestamp": "1741500000",
                        "text": {"body": "Test query triggering exception"},
                        "type": "text"
                    }]
                }
            }]
        }]
    }

    with patch("main.rag_engine.answer_query", side_effect=RuntimeError("Vector index corrupted")):
        res = post_signed_webhook(client, payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "Vector index corrupted" not in data["response"]
        assert "bis.gov.in" in data["response"]


def test_missing_evidence_uncertainty_handling(client):
    """Scenario 10: Unsupported product returns uncertainty message with official portal."""
    test_id = f"wamid.{uuid.uuid4().hex}"
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "BIZ_1",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [{
                        "from": "919999999999",
                        "id": test_id,
                        "timestamp": "1741500000",
                        "text": {"body": "What standard covers interstellar warp engines?"},
                        "type": "text"
                    }]
                }
            }]
        }]
    }

    with patch("main.rag_engine.answer_query") as mock_rag:
        mock_rag.return_value = {
            "content": (
                "The retrieved official BIS documentation does not provide sufficient evidence to answer this inquiry. "
                "Please verify regulatory requirements directly on the official portal: https://www.bis.gov.in"
            ),
            "sources": [],
            "confidence": 0.0,
            "insufficient_evidence": True,
            "warnings": []
        }
        res = post_signed_webhook(client, payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "does not provide sufficient" in data["response"]
        assert "bis.gov.in" in data["response"]


# ==============================================================================
# 11 & 12. Outbound WhatsApp API Reply & Error / Timeout Handling (Mocked)
# ==============================================================================

def test_successful_outbound_whatsapp_api_reply(monkeypatch):
    """Scenario 11: Outbound message dispatches through Meta Graph API with valid payload."""
    test_config = WhatsAppConfig(
        access_token="mock_meta_access_token",
        phone_number_id="10987654321",
        verify_token="mock_verify",
        app_secret="mock_secret",
        graph_api_version="v22.0"
    )
    client_instance = whatsapp_client
    monkeypatch.setattr(client_instance, "config", test_config)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "messaging_product": "whatsapp",
        "contacts": [{"input": "919876543210", "wa_id": "919876543210"}],
        "messages": [{"id": "wamid.outbound_mock_123"}]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        result = asyncio.run(client_instance.send_raw_text("919876543210", "Hello from ISense BIS Assistant!"))
        assert result["success"] is True
        assert result["meta"]["messages"][0]["id"] == "wamid.outbound_mock_123"

        mock_post.assert_called_once()
        call_url = mock_post.call_args[0][0]
        call_headers = mock_post.call_args[1]["headers"]
        call_json = mock_post.call_args[1]["json"]

        assert call_url == "https://graph.facebook.com/v22.0/10987654321/messages"
        assert call_headers["Authorization"] == "Bearer mock_meta_access_token"
        assert call_json["to"] == "919876543210"
        assert call_json["text"]["body"] == "Hello from ISense BIS Assistant!"


def test_outbound_meta_api_error_handling(monkeypatch):
    """Scenario 12a: Meta API returning HTTP 400/401 is handled safely without crashing."""
    test_config = WhatsAppConfig(
        access_token="invalid_token",
        phone_number_id="10987654321",
        verify_token="mock_verify",
        app_secret="mock_secret",
        graph_api_version="v22.0"
    )
    client_instance = whatsapp_client
    monkeypatch.setattr(client_instance, "config", test_config)

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.json.return_value = {"error": {"message": "Invalid OAuth access token", "code": 190}}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        result = asyncio.run(client_instance.send_raw_text("919876543210", "Test query"))
        assert result["success"] is False
        assert result["status_code"] == 401
        assert "Invalid OAuth access token" not in result["error"]


def test_outbound_meta_api_timeout_handling(monkeypatch):
    """Scenario 12b: Timeout connecting to Meta API is caught gracefully."""
    test_config = WhatsAppConfig(
        access_token="mock_token",
        phone_number_id="10987654321",
        verify_token="mock_verify",
        app_secret="mock_secret",
        graph_api_version="v22.0"
    )
    client_instance = whatsapp_client
    monkeypatch.setattr(client_instance, "config", test_config)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Connection timed out after 15s")

        result = asyncio.run(client_instance.send_raw_text("919876543210", "Test message"))
        assert result["success"] is False
        assert "timed out" in result["error"].lower()


# ==============================================================================
# 13. Status Endpoint Readiness & Secret Protection Guarantee
# ==============================================================================

def test_whatsapp_status_endpoint_unconfigured(client, monkeypatch):
    """Scenario 13a: Status returns 'unconfigured' when credentials are missing."""
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "")
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "")
    monkeypatch.setenv("WHATSAPP_APP_SECRET", "")

    res = client.get("/api/whatsapp/status")
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "unconfigured"
    assert data["readiness"]["configured"] is False
    assert data["readiness"]["accessTokenConfigured"] is False
    assert data["readiness"]["phoneNumberIdConfigured"] is False
    assert "verifiedToken" not in data


def test_whatsapp_status_endpoint_ready(client, monkeypatch):
    """Scenario 13b: Status accurately reports 'ready' when configured."""
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "real_access_token_123")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "9988776655")
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "verify_secret_123")
    monkeypatch.setenv("WHATSAPP_APP_SECRET", "app_secret_123")
    monkeypatch.setenv("WHATSAPP_GRAPH_API_VERSION", "v22.0")

    res = client.get("/api/whatsapp/status")
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "ready"
    assert data["readiness"]["configured"] is True
    assert data["readiness"]["accessTokenConfigured"] is True
    assert data["readiness"]["phoneNumberIdConfigured"] is True
    assert data["readiness"]["graphApiVersion"] == "v22.0"


def test_zero_secrets_exposed_across_endpoints(client, monkeypatch):
    """Scenario 13c: Strictly verify no secret tokens or keys appear in any response."""
    canary_token = "CANARY_META_ACCESS_TOKEN_XYZ_999"
    canary_secret = "CANARY_META_APP_SECRET_XYZ_888"
    canary_verify = "CANARY_VERIFY_TOKEN_XYZ_777"

    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", canary_token)
    monkeypatch.setenv("WHATSAPP_APP_SECRET", canary_secret)
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", canary_verify)

    # 1. Check status endpoint
    status_text = client.get("/api/whatsapp/status").text
    assert canary_token not in status_text
    assert canary_secret not in status_text
    assert canary_verify not in status_text

    # 2. Check webhook verification error responses
    verif_err_text = client.get("/api/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=wrong").text
    assert canary_token not in verif_err_text
    assert canary_secret not in verif_err_text
    assert canary_verify not in verif_err_text

    # 3. Check incoming webhook signature error
    sig_err_text = client.post("/api/webhook/whatsapp", json={"object": "test"}).text
    assert canary_token not in sig_err_text
    assert canary_secret not in sig_err_text
    assert canary_verify not in sig_err_text


# ==============================================================================
# Helper Formatting & Message Splitting Tests
# ==============================================================================

def test_whatsapp_formatting():
    """Verify bold headers, citation bullets, and statutory notices."""
    raw = "### Requirements\n**IS 16102** requires insulation resistance of at least 2.0 Megaohms."
    sources = [{
        "documentRef": "IS 16102 (Part 1)",
        "section": "Clause 8.1",
        "sourceUrl": "https://www.bis.gov.in/test"
    }]

    formatted = format_whatsapp_message(raw, sources=sources)
    assert "**" not in formatted
    assert "*IS 16102*" in formatted
    assert "*Official BIS Sources:*" in formatted
    assert "https://www.bis.gov.in/test" in formatted
    assert "*Statutory Notice:*" in formatted


def test_whatsapp_message_splitting():
    """Verify messages exceeding 3800 characters are cleanly partitioned."""
    long_content = "This is a regulatory test paragraph.\n\n" * 150
    chunks = split_whatsapp_message(long_content, max_chars=3800)

    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= 3800
        assert not chunk.endswith("\n\n\n")
