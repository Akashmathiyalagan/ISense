import pytest
import uuid
from fastapi.testclient import TestClient
from main import app
from rag_engine import conversational_assistant, conversation_store, rag_engine
from rag.conversation import (
    classify_intent,
    INTENT_PRODUCT_APPLICABILITY,
    INTENT_DOCUMENT_CHECKLIST,
    INTENT_APPLICATION_PROCEDURE,
    INTENT_TESTING_REQUIREMENTS,
    INTENT_FEES_TIMELINES,
    INTENT_SCHEME_REQUIREMENTS,
    INTENT_QCO_APPLICABILITY,
    INTENT_LICENCE_RENEWAL,
    INTENT_MARKING_LABELLING,
    INTENT_GENERAL_INQUIRY,
)

client = TestClient(app)


def test_intent_classification():
    """Verifies that the intent classifier distinguishes all 10 regulatory intents accurately."""
    assert classify_intent("What are all the documents needed to register my product?") == INTENT_DOCUMENT_CHECKLIST
    assert classify_intent("How to apply for BIS certification step by step?") == INTENT_APPLICATION_PROCEDURE
    assert classify_intent("What tests are required for RC car?") == INTENT_TESTING_REQUIREMENTS
    assert classify_intent("RC car testing requirements") == INTENT_TESTING_REQUIREMENTS
    assert classify_intent("How much does BIS registration fee cost and what is the timeline?") == INTENT_FEES_TIMELINES
    assert classify_intent("What is the difference between ISI Mark Scheme I and CRS Scheme II?") == INTENT_SCHEME_REQUIREMENTS
    assert classify_intent("Is there a mandatory Quality Control Order (QCO) for toys?") == INTENT_QCO_APPLICABILITY
    assert classify_intent("How to renew an expired BIS license?") == INTENT_LICENCE_RENEWAL
    assert classify_intent("What are the marking and labelling requirements on packaging?") == INTENT_MARKING_LABELLING
    assert classify_intent("What standard applies to LED lamps?") == INTENT_PRODUCT_APPLICABILITY
    assert classify_intent("What is the Bureau of Indian Standards?") == INTENT_GENERAL_INQUIRY


def test_turn1_asking_documents_triggers_product_clarification():
    """Case 1: Asking for product-registration documents triggers a product clarification."""
    conv_id = f"test-flow-{uuid.uuid4().hex[:8]}"
    res = conversational_assistant.process_turn(
        conversation_id=conv_id,
        message="What are all the documents needed to register my product?",
        channel="web"
    )

    content = res["content"]
    assert "First, what product do you want to register?" in content or "what product" in content.lower()
    assert res.get("status") == "awaiting_clarification"

    state = conversation_store.get(conv_id)
    assert state is not None
    assert state.current_intent == INTENT_DOCUMENT_CHECKLIST
    assert state.pending_clarification_type == "product"


def test_turn2_replying_led_bulb_continues_conversation_and_asks_origin():
    """Case 2: Replying 'LED bulb' continues the existing conversation instead of restarting."""
    conv_id = f"test-flow-{uuid.uuid4().hex[:8]}"
    # Turn 1
    conversational_assistant.process_turn(
        conversation_id=conv_id,
        message="What are all the documents needed to register my product?",
        channel="web"
    )

    # Turn 2
    res2 = conversational_assistant.process_turn(
        conversation_id=conv_id,
        message="LED bulb",
        channel="web"
    )

    content2 = res2["content"]
    # Should recognize LED bulb, check relevant standard, and ask origin
    assert "LED bulb" in content2 or "led" in content2.lower()
    assert "manufactured in India or imported" in content2 or "imported" in content2.lower()
    assert res2.get("status") == "awaiting_clarification"

    state = conversation_store.get(conv_id)
    assert state.product_name == "led bulb"
    assert "16102" in (state.candidate_standard or "")
    assert state.pending_clarification_type == "origin"


def test_turn3_replying_manufactured_in_india_preserves_led_context_and_gives_checklist():
    """Case 3 & 4: Replying 'Manufactured in India' preserves LED bulb context and retrieves relevant document checklist."""
    conv_id = f"test-flow-{uuid.uuid4().hex[:8]}"
    # Turn 1
    conversational_assistant.process_turn(
        conversation_id=conv_id,
        message="What are all the documents needed to register my product?",
        channel="web"
    )
    # Turn 2
    conversational_assistant.process_turn(
        conversation_id=conv_id,
        message="LED bulb",
        channel="web"
    )
    # Turn 3
    res3 = conversational_assistant.process_turn(
        conversation_id=conv_id,
        message="Manufactured in India.",
        channel="web"
    )

    content3 = res3["content"]
    # Context preserved
    assert "LED Bulb" in content3 or "Led Bulb" in content3 or "led bulb" in content3.lower()
    assert "India" in content3
    assert "IS 16102" in content3

    # Structured 7 sections present
    assert "1. Product & Applicant Context" in content3
    assert "2. Likely Certification Route & Applicability Conditions" in content3
    assert "3. Required Document Checklist" in content3
    assert "4. Testing & Laboratory Requirements" in content3
    assert "5. Step-by-Step Application Procedure" in content3
    assert "6. Official Source Links & References" in content3
    assert "7. Information Requiring Verification & Next Steps" in content3

    # Document details present
    assert "Form-1" in content3 or "Test Report" in content3
    assert "CRS" in content3 or "Compulsory Registration" in content3


def test_rc_car_testing_retrieves_testing_evidence_not_application_checklist():
    """Case 5: A question about RC-car testing retrieves technical testing evidence rather than an application checklist."""
    conv_id = f"test-rc-{uuid.uuid4().hex[:8]}"
    res = conversational_assistant.process_turn(
        conversation_id=conv_id,
        message="RC car testing requirements",
        channel="web"
    )

    content = res["content"]
    # Must retrieve technical toy standard IS 9873 (Part 1) : 2019
    assert "IS 9873" in content
    # Should contain technical clauses rather than an application checklist
    assert ("Clause" in content or "mechanical" in content.lower() or "safety" in content.lower())
    assert "First, what product do you want to register?" not in content


def test_internal_chunk_ids_never_appear_in_response():
    """Case 7: Internal chunk IDs never appear in user-facing responses."""
    conv_id = f"test-chk-{uuid.uuid4().hex[:8]}"
    res = conversational_assistant.process_turn(
        conversation_id=conv_id,
        message="What standard applies to LED lamps?",
        channel="web"
    )

    content = res["content"]
    assert "chk-" not in content
    assert "chk-doc-" not in content
    assert "<source_evidence" not in content
    assert "</source_evidence>" not in content


def test_website_and_whatsapp_conversations_retain_context_independently():
    """Case 8: Website and WhatsApp conversations retain context independently."""
    web_id = f"web-sess-{uuid.uuid4().hex[:8]}"
    wa_id = "919988776655"

    # Web asks for LED bulb documents
    conversational_assistant.process_turn(
        conversation_id=web_id,
        message="What are all the documents needed to register my product?",
        channel="web"
    )
    conversational_assistant.process_turn(
        conversation_id=web_id,
        message="LED bulb",
        channel="web"
    )

    # WhatsApp asks about RC car
    wa_res = conversational_assistant.process_turn(
        conversation_id=wa_id,
        message="RC car",
        channel="whatsapp"
    )

    # Web session state
    web_state = conversation_store.get(web_id)
    assert web_state.product_name == "led bulb"
    assert web_state.current_intent == INTENT_DOCUMENT_CHECKLIST

    # WhatsApp session state
    wa_state = conversation_store.get(wa_id)
    assert wa_state.product_name == "rc car"
    assert "IS 9873" in (wa_state.candidate_standard or "")


def test_new_conversation_starts_without_inheriting_prior_details():
    """Case 9: A new conversation starts without inheriting another conversation's details."""
    conv1 = f"convo-alpha-{uuid.uuid4().hex[:8]}"
    conv2 = f"convo-beta-{uuid.uuid4().hex[:8]}"

    # conv1 sets up LED bulb
    conversational_assistant.process_turn(conv1, "What are all the documents needed to register my product?")
    conversational_assistant.process_turn(conv1, "LED bulb")

    # conv2 asks for documents from scratch
    res = conversational_assistant.process_turn(conv2, "What are all the documents needed to register my product?")
    assert "First, what product do you want to register?" in res["content"]

    state2 = conversation_store.get(conv2)
    assert state2.product_name is None


def test_website_ai_chat_api_endpoint():
    """Case 10: Existing /api/ai/chat endpoint works with multi-turn conversations."""
    session_id = f"api-test-{uuid.uuid4().hex[:8]}"

    # Turn 1
    resp1 = client.post("/api/ai/chat", json={
        "message": "What are all the documents needed to register my product?",
        "conversationId": session_id
    })
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert "First, what product do you want to register?" in data1["content"]
    assert data1["conversationId"] == session_id

    # Turn 2
    resp2 = client.post("/api/ai/chat", json={
        "message": "LED bulb",
        "conversationId": session_id
    })
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert "manufactured in India or imported" in data2["content"]

    # Turn 3
    resp3 = client.post("/api/ai/chat", json={
        "message": "Manufactured in India.",
        "conversationId": session_id
    })
    assert resp3.status_code == 200
    data3 = resp3.json()
    assert "IS 16102" in data3["content"]
    assert "3. Required Document Checklist" in data3["content"]


# ==============================================================================
# Dedicated Regression Tests for Product-Change, Evidence Relevance & LLM Config
# ==============================================================================

def test_regression_rc_car_to_steel_water_bottle_product_change_and_no_is9873_leak():
    """
    Regression Test (Requirements 3, 4, 6, 7 & 10):
    1. User asks about RC car -> retrieves IS 9873 toy-safety evidence.
    2. User then says: 'I made a steel water bottle'.
    3. Product context changes from RC car to steel water bottle.
    4. Does NOT inherit IS 9873 or toy safety clauses.
    5. Returns transparent limitation / clarification without inventing standards or fees.
    """
    conv_id = f"regr-switch-{uuid.uuid4().hex[:8]}"

    # Turn 1: User asks about RC car
    res1 = conversational_assistant.process_turn(
        conversation_id=conv_id,
        message="What tests are required for RC car?",
        channel="web"
    )
    content1 = res1["content"]
    assert "IS 9873" in content1
    state1 = conversation_store.get(conv_id)
    assert state1.product_name == "rc car"
    assert "9873" in (state1.candidate_standard or "")

    # Turn 2: User switches product to steel water bottle
    res2 = conversational_assistant.process_turn(
        conversation_id=conv_id,
        message="I made a steel water bottle",
        channel="web"
    )
    content2 = res2["content"]

    # 1. Product context MUST be replaced
    state2 = conversation_store.get(conv_id)
    assert state2.product_name == "steel water bottle"
    assert state2.candidate_standard is None

    # 2. IS 9873 and toy safety clauses MUST NOT be inherited or mentioned
    assert "IS 9873" not in content2
    assert "9873" not in content2
    assert "toy" not in content2.lower()
    assert "rc car" not in content2.lower()

    # 3. Transparent limitation / clarification returned without inventing fake standards
    assert res2.get("insufficient_evidence") is True
    assert "steel water bottle" in content2.lower()
    assert ("clarify" in content2.lower() or "limitation" in content2.lower() or "manak" in content2.lower())


def test_regression_missing_regulatory_evidence_causes_clarification_not_hallucination():
    """
    Regression Test (Requirements 6, 7 & 10):
    An unindexed product (e.g. steel water bottle) triggers transparent limitation and clarification
    instead of inventing standard numbers, QCO status, document checklists or fees.
    """
    conv_id = f"regr-unidx-{uuid.uuid4().hex[:8]}"
    res = conversational_assistant.process_turn(
        conversation_id=conv_id,
        message="I made a steel water bottle",
        channel="web"
    )
    content = res["content"]
    assert res.get("insufficient_evidence") is True
    assert res.get("status") == "awaiting_clarification"
    # Never invent standards or fees
    assert "IS 9873" not in content
    assert "₹50,000" not in content
    # Identifies product and asks clarification on specifications
    assert "steel water bottle" in content.lower()
    assert "intended" in content.lower() or "clarify" in content.lower()


def test_regression_missing_llm_credentials_reported_safely():
    """
    Regression Test (Requirements 2 & 10):
    When no LLM credentials are configured, UnavailableLLMProvider returns a clear operational error.
    It does not claim neural generation, and never exposes keys.
    """
    from rag.llm_provider import UnavailableLLMProvider
    from rag.models import KnowledgeChunk

    provider = UnavailableLLMProvider()

    # Empty retrieved evidence test: returns clear operational notice
    empty_result = provider.generate(
        query="RC car testing",
        system_instruction="You are ISense",
        retrieved_chunks=[]
    )
    assert empty_result.is_success is False
    assert "unconfigured" in empty_result.text.lower()
    assert "AIza" not in empty_result.text

    dummy_chunks = [
        KnowledgeChunk(
            chunk_id="chk-doc-dummy",
            document_id="doc-001",
            standard_code="IS 9873 (Part 1) : 2019",
            standard_title="Safety of Toys",
            category="Consumer Goods & Toys",
            clause="Clause 4.4",
            content="Verified technical requirement on physical safety.",
            authority="Bureau of Indian Standards",
            source_url="https://www.services.bis.gov.in"
        )
    ]

    result = provider.generate(
        query="RC car testing",
        system_instruction="You are ISense",
        retrieved_chunks=dummy_chunks
    )

    # Transparently reports unconfigured status
    assert "LLM generation provider is currently unconfigured" in result.text or "unconfigured" in result.text.lower()
    # Must not contain API keys or secret tokens
    assert "AIza" not in result.text
    assert "AQ." not in result.text


def test_regression_new_user_cannot_inherit_another_users_context():
    """
    Regression Test (Requirements 3, 9 & 10):
    User A's product and conversation context is completely isolated from User B.
    """
    user_a_id = f"user-a-{uuid.uuid4().hex[:8]}"
    user_b_id = f"user-b-{uuid.uuid4().hex[:8]}"

    # User A asks about RC car
    conversational_assistant.process_turn(user_a_id, "What tests are required for RC car?")
    state_a = conversation_store.get(user_a_id)
    assert state_a.product_name == "rc car"

    # User B asks about general registration
    res_b = conversational_assistant.process_turn(user_b_id, "What are all the documents needed to register my product?")
    state_b = conversation_store.get(user_b_id)
    assert state_b.product_name is None
    assert "rc car" not in res_b["content"].lower()
    assert "IS 9873" not in res_b["content"]


def test_regression_multi_product_sequence_switch():
    """
    Test 1, 2, 3: rc car -> water bottle -> back bag -> LED bulb -> mobile charger.
    Verifies that each new product updates product context and no previous product's standard
    or answers leak into the new query.
    """
    conv_id = f"seq-test-{uuid.uuid4().hex[:8]}"

    # Step 1: rc car
    res1 = conversational_assistant.process_turn(conv_id, "rc car")
    state1 = conversation_store.get(conv_id)
    assert state1.product_name == "rc car"
    assert "9873" in (state1.candidate_standard or "")
    assert "IS 9873" in res1["content"]

    # Step 2: water bottle
    res2 = conversational_assistant.process_turn(conv_id, "water bottle")
    state2 = conversation_store.get(conv_id)
    assert state2.product_name == "water bottle"
    assert state2.candidate_standard is None
    assert "IS 9873" not in res2["content"]
    assert "toy" not in res2["content"].lower()
    assert "water bottle" in res2["content"].lower()

    # Step 3: back bag
    res3 = conversational_assistant.process_turn(conv_id, "back bag")
    state3 = conversation_store.get(conv_id)
    assert state3.product_name == "back bag"
    assert state3.candidate_standard is None
    assert "water bottle" not in res3["content"].lower()
    assert "bottle" not in res3["content"].lower()
    assert "back bag" in res3["content"].lower()

    # Step 4: LED bulb
    res4 = conversational_assistant.process_turn(conv_id, "LED bulb")
    state4 = conversation_store.get(conv_id)
    assert state4.product_name == "led bulb"
    assert "16102" in (state4.candidate_standard or "")
    assert "back bag" not in res4["content"].lower()
    assert "water bottle" not in res4["content"].lower()
    assert "IS 16102" in res4["content"]

    # Step 5: mobile charger
    res5 = conversational_assistant.process_turn(conv_id, "mobile charger")
    state5 = conversation_store.get(conv_id)
    assert state5.product_name == "mobile charger"
    assert "13252" in (state5.candidate_standard or "")
    assert "16102" not in (state5.candidate_standard or "")
    assert "led bulb" not in res5["content"].lower()
    assert "is 16102" not in res5["content"].lower()
    assert "back bag" not in res5["content"].lower()
    assert "IS 13252" in res5["content"]


def test_regression_followup_and_transition_to_backpack():
    """
    Test 4, 5: A follow-up question retains product details (LED bulb -> What documents do I need? -> Manufactured in India).
    Then switching with 'Now tell me about a backpack' switches product cleanly without leaking LED bulb context.
    """
    conv_id = f"switch-test-{uuid.uuid4().hex[:8]}"

    # Identify LED bulb
    conversational_assistant.process_turn(conv_id, "LED bulb")
    state1 = conversation_store.get(conv_id)
    assert state1.product_name == "led bulb"

    # Follow up: What documents do I need?
    res2 = conversational_assistant.process_turn(conv_id, "What documents do I need?")
    assert "manufactured in India or imported" in res2["content"]
    state2 = conversation_store.get(conv_id)
    assert state2.product_name == "led bulb"
    assert state2.pending_clarification_type == "origin"

    # Origin answer: Manufactured in India
    res3 = conversational_assistant.process_turn(conv_id, "Manufactured in India.")
    assert "LED Bulb" in res3["content"] or "led bulb" in res3["content"].lower()
    assert "IS 16102" in res3["content"]
    assert "3. Required Document Checklist" in res3["content"]

    # Now switch to backpack
    res4 = conversational_assistant.process_turn(conv_id, "Now tell me about a backpack")
    state4 = conversation_store.get(conv_id)
    assert state4.product_name == "backpack"
    assert state4.candidate_standard is None
    assert "IS 16102" not in res4["content"]
    assert "led bulb" not in res4["content"].lower()
    assert "backpack" in res4["content"].lower()


def test_regression_search_unknown_product_and_standard_number():
    """
    Test 8, 9: An unknown product searches available knowledge base without hardcoded rejection.
    Searching an explicit standard number not in KNOWN_BIS_STANDARDS_CATALOG still searches corpus.
    """
    # Searching standard number IS 16169 (islanding)
    res = rag_engine.answer_query("What does IS 16169 cover?")
    assert len(res["sources"]) > 0
    assert any("16169" in s["documentRef"] for s in res["sources"])

    # Searching an unknown product: does not invent a standard
    res_unknown = rag_engine.answer_query("Is BIS certification required for handmade bamboo flute?")
    assert res_unknown["insufficient_evidence"] is True
    assert "IS 13252" not in res_unknown["content"]
    assert "IS 16102" not in res_unknown["content"]


def test_regression_water_bottle_to_hi_short_greeting():
    """
    Regression Test 1: User discusses water bottle -> sends 'hi' -> ISense returns a short greeting response,
    NOT the repeated water bottle unindexed prompt, while preserving conversation context.
    """
    conv_id = f"wb-hi-{uuid.uuid4().hex[:8]}"
    # Turn 1: water bottle
    res1 = conversational_assistant.process_turn(conv_id, "water bottle")
    state1 = conversation_store.get(conv_id)
    assert state1.product_name == "water bottle"
    assert "water bottle" in res1["content"].lower()

    # Turn 2: hi
    res2 = conversational_assistant.process_turn(conv_id, "hi")
    state2 = conversation_store.get(conv_id)
    assert state2.product_name == "water bottle"  # Context preserved
    assert res2.get("is_greeting") is True
    assert len(res2.get("sources", [])) == 0  # No document retrieval
    assert "hello" in res2["content"].lower() or "welcome" in res2["content"].lower()
    # Does NOT repeat the unindexed regulatory water bottle text
    assert "laboratory testing specifications specifically covering" not in res2["content"]
    assert "To assist with identifying potential compliance requirements" not in res2["content"]


def test_regression_water_bottle_to_backpack_new_product_context():
    """
    Regression Test 2: User discusses water bottle -> sends 'backpack' -> cleanly switches to backpack context.
    No water bottle standard or stale text leaked.
    """
    conv_id = f"wb-bp-{uuid.uuid4().hex[:8]}"
    # Turn 1: water bottle
    conversational_assistant.process_turn(conv_id, "water bottle")
    state1 = conversation_store.get(conv_id)
    assert state1.product_name == "water bottle"

    # Turn 2: backpack
    res2 = conversational_assistant.process_turn(conv_id, "backpack")
    state2 = conversation_store.get(conv_id)
    assert state2.product_name == "backpack"
    assert "water bottle" not in res2["content"].lower()
    assert "bottle" not in res2["content"].lower()
    assert "backpack" in res2["content"].lower()


def test_regression_pending_clarification_led_bulb_answer_flow():
    """
    Regression Test 3: Pending product clarification -> user answers 'LED bulb' -> correctly routes as product answer flow,
    NOT as a greeting.
    """
    conv_id = f"clarif-led-{uuid.uuid4().hex[:8]}"
    # Turn 1: ask for documents without specifying product
    res1 = conversational_assistant.process_turn(conv_id, "What documents do I need to register?")
    state1 = conversation_store.get(conv_id)
    assert state1.pending_clarification_type == "product"
    assert state1.conversation_status == "awaiting_clarification"

    # Turn 2: reply with 'LED bulb'
    res2 = conversational_assistant.process_turn(conv_id, "LED bulb")
    state2 = conversation_store.get(conv_id)
    assert state2.product_name == "led bulb"
    assert "16102" in (state2.candidate_standard or "")
    assert res2.get("is_greeting") is not True
    assert "manufactured in India or imported" in res2["content"] or "imported" in res2["content"].lower()


def test_regression_duplicate_webhook_event_no_duplicate_reply():
    """
    Regression Test 4: WhatsApp webhook duplicate event suppression: webhook retry with same message ID
    returns duplicate_message_ignored and sends no duplicate outbound reply.
    """
    from tests.test_whatsapp import post_signed_webhook
    from unittest.mock import patch

    test_id = f"wamid.idempotent.{uuid.uuid4().hex}"
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

    with patch("whatsapp_service.whatsapp_client.send_rag_response") as mock_send:
        # First event
        res1 = post_signed_webhook(client, payload)
        assert res1.status_code == 200
        assert res1.json()["status"] == "success"

        # Duplicate retry with same message ID
        res2 = post_signed_webhook(client, payload)
        assert res2.status_code == 200
        assert res2.json().get("message") == "duplicate_message_ignored"
        assert mock_send.call_count <= 1


def test_regression_two_concurrent_senders_no_shared_state():
    """
    Regression Test 5: Two concurrent senders maintain strictly isolated conversation states.
    Sender A's product and testing requirements do not leak into Sender B's conversation.
    """
    sender_a = f"sender-a-{uuid.uuid4().hex[:6]}"
    sender_b = f"sender-b-{uuid.uuid4().hex[:6]}"

    # Sender A queries helmet
    res_a1 = conversational_assistant.process_turn(sender_a, "helmet")
    state_a = conversation_store.get(sender_a)
    assert state_a.product_name == "helmet"
    assert "4151" in (state_a.candidate_standard or "")

    # Sender B queries ceiling fan
    res_b1 = conversational_assistant.process_turn(sender_b, "ceiling fan")
    state_b = conversation_store.get(sender_b)
    assert state_b.product_name == "ceiling fan"
    assert "374" in (state_b.candidate_standard or "")

    # Sender A asks tests
    res_a2 = conversational_assistant.process_turn(sender_a, "What tests are required?")
    assert "4151" in res_a2["content"] or "impact" in res_a2["content"].lower() or "helmet" in res_a2["content"].lower()
    assert "ceiling fan" not in res_a2["content"].lower()
    assert "air delivery" not in res_a2["content"].lower()

    # Sender B asks tests
    res_b2 = conversational_assistant.process_turn(sender_b, "What tests are required?")
    assert "374" in res_b2["content"] or "air delivery" in res_b2["content"].lower() or "fan" in res_b2["content"].lower()
    assert "helmet" not in res_b2["content"].lower()
    assert "4151" not in res_b2["content"]


def test_regression_llm_unavailable_no_stale_answer_returned():
    """
    Regression Test 6: When LLM is unavailable, assistant uses UnavailableLLMProvider to produce
    grounded structured answers from retrieved chunks of the current turn,
    never returning a stale answer from a previous product or query.
    """
    from rag.llm_provider import UnavailableLLMProvider

    conv_id = f"unavail-{uuid.uuid4().hex[:6]}"
    # Turn 1: LED bulb
    conversational_assistant.process_turn(conv_id, "LED bulb")

    # Turn 2: Query for ceiling fan with UnavailableLLMProvider override
    rag_res = rag_engine.answer_query(
        "ceiling fan",
        llm_provider_override=UnavailableLLMProvider(error_message="Simulated 429 quota exhaustion")
    )
    # Content must reflect ceiling fan / IS 374, NOT stale LED bulb
    assert "374" in rag_res["content"] or "ceiling fan" in rag_res["content"].lower()
    assert "16102" not in rag_res["content"]
    assert "led bulb" not in rag_res["content"].lower()





def test_whatsapp_greeting_detector_routes_hi_as_greeting_only():
    """Webhook routing helper recognises greetings without matching product messages."""
    from main import is_greeting_message

    assert is_greeting_message("hi") is True
    assert is_greeting_message(" Hi! ") is True
    assert is_greeting_message("good morning") is True
    assert is_greeting_message("water bottle") is False
    assert is_greeting_message("back bag") is False
    assert is_greeting_message("RC car") is False
    assert is_greeting_message("IS 16102") is False
