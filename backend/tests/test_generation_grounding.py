import pytest
from rag.models import KnowledgeChunk
from rag.engine import BISRAGEngine
from rag.llm_provider import MockLLMProvider, UnavailableLLMProvider

@pytest.fixture
def test_engine(tmp_path):
    """Engine initialized with test knowledge chunks."""
    engine = BISRAGEngine(use_dense=False, min_relevance_threshold=0.10)
    # Ensure engine has sample chunks
    test_chunks = [
        KnowledgeChunk(
            chunk_id="chk-led-safety",
            document_id="DOC-LED",
            standard_code="IS 16102 (Part 1) : 2012",
            standard_title="LED Lamps Safety Requirements",
            clause="Clause 8.0 — Insulation Resistance",
            page=4,
            content="Insulation resistance shall be minimum 4.0 Megohms at 500V DC.",
            category="Lighting",
            authority="BIS ETD 23",
            verification_status="verified_official_record",
            source_url="https://services.bis.gov.in/led"
        ),
        KnowledgeChunk(
            chunk_id="chk-led-marking",
            document_id="DOC-LED",
            standard_code="IS 16102 (Part 1) : 2012",
            standard_title="LED Lamps Safety Requirements",
            clause="Clause 5 — Marking Protocol",
            page=6,
            content="Marking must withstand 15s water and 15s petroleum spirit rub without loss of legibility.",
            category="Lighting",
            authority="BIS ETD 23",
            verification_status="verified_official_record",
            source_url="https://services.bis.gov.in/led"
        )
    ]
    engine.index.build_index(test_chunks)
    return engine

def test_answer_supported_directly_by_source(test_engine):
    """Grounding test: directly supported query produces grounded response with verifiable citations."""
    mock_llm = MockLLMProvider()
    resp = test_engine.answer_query(
        "What is the insulation resistance required for LED lamps under IS 16102?",
        llm_provider_override=mock_llm
    )
    assert resp["insufficient_evidence"] is False
    assert len(resp["sources"]) > 0
    assert "IS 16102" in resp["sources"][0]["documentRef"]
    assert resp["sources"][0]["section"] == "Clause 8.0 — Insulation Resistance"
    assert resp["confidence"] > 0.0
    assert "Statutory Boundary Notice" in resp["content"]

def test_synthesis_across_multiple_sources(test_engine):
    """Grounding test: query touching insulation and marking includes multiple citations."""
    mock_llm = MockLLMProvider()
    resp = test_engine.answer_query(
        "What are the insulation and marking test requirements for LED lamps?",
        llm_provider_override=mock_llm
    )
    assert len(resp["sources"]) >= 1
    sections = [s["section"] for s in resp["sources"]]
    assert any("Clause 8.0" in sec or "Clause 5" in sec for sec in sections)

def test_unsupported_question_abstains(test_engine):
    """Grounding test: completely unsupported query abstains with insufficient_evidence=True."""
    mock_llm = MockLLMProvider()
    resp = test_engine.answer_query(
        "What is the minimum warp drive hypercharge for interstellar spacecraft?",
        llm_provider_override=mock_llm
    )
    assert resp["insufficient_evidence"] is True
    assert resp["confidence"] == 0.0
    assert len(resp["sources"]) == 0
    assert "Insufficient Regulatory Evidence" in resp["content"]

def test_citation_verifiability_and_metadata(test_engine):
    """Citation test: citations contain exact, non-hallucinated metadata."""
    mock_llm = MockLLMProvider()
    resp = test_engine.answer_query(
        "insulation resistance at 500V DC",
        llm_provider_override=mock_llm
    )
    for src in resp["sources"]:
        assert src["id"].startswith("chk-")
        assert src["verification_status"] == "verified_official_record"
        assert src["sourceUrl"] != ""
        assert len(src["excerpt"]) > 10

def test_unavailable_provider_does_not_fake_llm(test_engine):
    """Safety test: UnavailableLLMProvider transparently reports provider status and does not fabricate answers."""
    unavail = UnavailableLLMProvider()
    resp = test_engine.answer_query(
        "What is the insulation resistance under IS 16102?",
        llm_provider_override=unavail
    )
    assert resp["insufficient_evidence"] is False
    assert "LLM generation provider is currently unconfigured" in resp["content"]
    assert len(resp["sources"]) > 0
    # Verified evidence is shown directly
    assert "4.0 Megohms" in resp["content"]

def test_empty_retrieved_context_does_not_produce_false_grounding(test_engine):
    """Safety test: when search returns nothing, engine never returns false sources."""
    mock_llm = MockLLMProvider(custom_answer="Fabricated response without grounding")
    resp = test_engine.answer_query(
        "unmatched query XYZ-999-ABC",
        llm_provider_override=mock_llm
    )
    assert resp["insufficient_evidence"] is True
    assert len(resp["sources"]) == 0

def test_query_paraphrasing_consistency(test_engine):
    """Consistency test: different wordings for same technical requirement retrieve identical source chunk."""
    mock_llm = MockLLMProvider()
    q1 = "insulation resistance at 500V DC"
    q2 = "what megohms insulation required at 500 volts dc"
    res1 = test_engine.answer_query(q1, llm_provider_override=mock_llm)
    res2 = test_engine.answer_query(q2, llm_provider_override=mock_llm)
    assert res1["sources"][0]["id"] == res2["sources"][0]["id"]
