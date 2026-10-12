from rag.llm_provider import GeminiLLMProvider
from rag.models import KnowledgeChunk


class FailingGeminiClient:
    def generate_content(self, prompt):
        raise RuntimeError("simulated provider outage")


def test_gemini_fallback_uses_product_name_and_calls_standard_candidate(tmp_path):
    provider = GeminiLLMProvider.__new__(GeminiLLMProvider)
    provider.api_key = "test-key"
    provider.model_name = "test-model"
    provider.client = FailingGeminiClient()

    chunk = KnowledgeChunk(
        chunk_id="chk-doc-toy-123456",
        document_id="bis-toy-manual",
        standard_code="IS 9873 (Part 1):2019",
        standard_title="Safety of Toys Part 1",
        clause="Scope",
        page=1,
        content="Example retrieved passage about toy scope.",
        category="Toys",
        authority="BIS",
        verification_status="verified_official_record",
        source_url="https://www.bis.gov.in/example-toy-manual.pdf",
    )
    query = (
        "Please assess BIS requirements for this exact product.\n"
        "- Product name: rc car\n"
        "- Intended user: Age 14+ / hobby use\n"
        "Use only retrieved official BIS evidence. Do not invent standards."
    )

    result = provider.generate(
        query=query,
        system_instruction="Answer only from retrieved evidence.",
        retrieved_chunks=[chunk],
    )

    assert result.is_success is True
    assert "**Retrieved BIS evidence for: rc car**" in result.text
    assert "this category is evaluated under" not in result.text
    assert "Use only retrieved official BIS evidence" not in result.text
    assert "https://www.bis.gov.in/example-toy-manual.pdf" in result.text
    assert result.provider == "ISense Grounded Retrieval Fallback"
