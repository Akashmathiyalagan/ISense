import os
import pytest
from rag.models import KnowledgeChunk, RetrievalResult
from rag.ingestion import RegulatoryIngestionPipeline, clean_text
from rag.index import BISSearchIndex

@pytest.fixture
def sample_corpus():
    return [
        KnowledgeChunk(
            chunk_id="chk-led-01",
            document_id="DOC-LED",
            standard_code="IS 16102 (Part 1) : 2012",
            standard_title="Self-Ballasted LED-Lamps Safety Requirements",
            clause="Clause 8.0 — Insulation Resistance",
            page=4,
            content="Insulation resistance between live parts and accessible metal parts shall not be less than 4.0 Megohms at 500V DC.",
            category="Lighting",
            authority="BIS ETD 23",
            verification_status="verified_official_record",
            source_url="https://services.bis.gov.in/led"
        ),
        KnowledgeChunk(
            chunk_id="chk-solar-01",
            document_id="DOC-SOLAR",
            standard_code="IS 16221 (Part 2) : 2015",
            standard_title="Safety of Power Converters for Photovoltaic Systems",
            clause="Clause 5.1 — Anti-Islanding Protection",
            page=12,
            content="Grid-connected PV inverters shall cease to energize the utility line within 2.0 seconds upon loss of grid voltage.",
            category="Solar",
            authority="MNRE & BIS ETD 28",
            verification_status="verified_official_record",
            source_url="https://services.bis.gov.in/solar"
        ),
        KnowledgeChunk(
            chunk_id="chk-helmet-01",
            document_id="DOC-HELMET",
            standard_code="IS 4151 : 2020",
            standard_title="Protective Helmets for Two-Wheeler Riders",
            clause="Clause 9.1 — Impact Deceleration Attenuation",
            page=14,
            content="Peak deceleration shall not exceed 300g (3000 m/s2) and duration exceeding 150g shall not exceed 5.0 milliseconds.",
            category="Road Safety",
            authority="MoRTH & BIS TED 18",
            verification_status="verified_official_record",
            source_url="https://services.bis.gov.in/helmet"
        ),
        KnowledgeChunk(
            chunk_id="chk-helmet-02",
            document_id="DOC-HELMET",
            standard_code="IS 4151 : 2020",
            standard_title="Protective Helmets for Two-Wheeler Riders",
            clause="Clause 9.2 — Retention System Strength",
            page=18,
            content="Dynamic elongation of retention chinstrap shall not exceed 25mm under 10kg drop impulse.",
            category="Road Safety",
            authority="MoRTH & BIS TED 18",
            verification_status="verified_official_record",
            source_url="https://services.bis.gov.in/helmet"
        )
    ]

@pytest.fixture
def search_index(sample_corpus):
    return BISSearchIndex(chunks=sample_corpus, use_dense=True, min_relevance_threshold=0.15)

def test_exact_standard_number_query(search_index):
    """Retrieval test: exact standard code 'IS 4151' retrieves helmet chunks first."""
    results = search_index.search("What does IS 4151 specify?", top_k=2)
    assert len(results) > 0
    top_chunk = results[0].chunk
    assert "4151" in top_chunk.standard_code
    assert top_chunk.category == "Road Safety"

def test_natural_language_paraphrase(search_index):
    """Retrieval test: natural language query without standard number retrieves correct chunk."""
    results = search_index.search("How fast must an inverter disconnect if the electrical grid fails?", top_k=2)
    assert len(results) > 0
    assert "16221" in results[0].chunk.standard_code or "16169" in results[0].chunk.standard_code
    assert "2.0 seconds" in results[0].chunk.content

def test_multi_document_corpus_precision(search_index):
    """Retrieval test: LED insulation query retrieves LED lamp document and excludes solar/helmet."""
    results = search_index.search("minimum insulation resistance for led bulb at 500V DC", top_k=2)
    assert len(results) > 0
    assert "16102" in results[0].chunk.standard_code
    assert "4.0 Megohms" in results[0].chunk.content

def test_irrelevant_product_rejection(search_index):
    """Retrieval test: query for completely unmentioned topic is rejected or scored low."""
    results = search_index.search("interstellar rocket propellant cryogenic oxidizer", top_k=2, min_threshold=0.35)
    assert len(results) == 0

def test_empty_query(search_index):
    """Retrieval test: empty or whitespace query returns empty result list."""
    assert search_index.search("") == []
    assert search_index.search("   \n\t  ") == []

def test_duplicate_ingestion_detection(tmp_path):
    """Ingestion test: duplicate ingestion of identical file is skipped via hash verification."""
    storage_dir = str(tmp_path)
    pipeline = RegulatoryIngestionPipeline(storage_dir=storage_dir)

    test_file = tmp_path / "test_std.md"
    test_file.write_text(
        "---\nstandard_code: IS 1234\nstandard_title: Test Standard\ncategory: Testing\n---\n"
        "## Clause 1 - Scope & Verification\n"
        "This is an official verification document containing technical testing requirements and regulatory scope for deduplication.",
        encoding="utf-8"
    )

    _, chunks1, res1 = pipeline.ingest_file(str(test_file))
    assert res1["status"] == "success"
    assert len(chunks1) > 0

    # Second ingestion of unchanged file must skip
    _, chunks2, res2 = pipeline.ingest_file(str(test_file))
    assert res2["status"] == "skipped"
    assert "identical hash" in res2["message"]

def test_index_rebuild_and_update(sample_corpus):
    """Index test: adding new chunk updates retrieval results dynamically."""
    idx = BISSearchIndex(chunks=sample_corpus[:2], use_dense=False, min_relevance_threshold=0.15)
    initial_res = idx.search("helmet", top_k=2, min_threshold=0.15)
    assert len(initial_res) == 0

    # Rebuild index with helmet chunks
    idx.build_index(sample_corpus)
    updated_res = idx.search("helmet deceleration", top_k=2, min_threshold=0.10)
    assert len(updated_res) > 0
    assert "4151" in updated_res[0].chunk.standard_code
