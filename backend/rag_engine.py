"""
ISense BIS Certification Assistance — RAG Engine
Production Grounded Knowledge Engine for Bureau of Indian Standards Compliance.
Replaces previous hardcoded template heuristics with an end-to-end RAG architecture:
- Authoritative document ingestion & tracking
- Hybrid Dense (MiniLM) + Lexical (BM25) search retrieval
- Exact standard code parsing & candidate classification
- Grounded generation through configured LLM providers (Gemini / OpenAI / Fallback)
- Traceable citations to verified regulatory documents
"""

from rag.models import (
    DocumentMetadata,
    KnowledgeChunk,
    RetrievalResult,
    SourceCitation,
    CandidateStandard,
    DetectionResult,
    RAGResponse
)
from rag.ingestion import RegulatoryIngestionPipeline
from rag.index import BISSearchIndex, construct_citations
from rag.llm_provider import (
    BaseLLMProvider,
    GeminiLLMProvider,
    OpenAILLMProvider,
    MockLLMProvider,
    UnavailableLLMProvider,
    get_llm_provider
)
from rag.standard_detector import (
    detect_bis_standard,
    detect_bis_standard_structured,
    KNOWN_BIS_STANDARDS_CATALOG as BIS_PRODUCT_STANDARDS
)
from rag.engine import BISRAGEngine

# Singleton instance
rag_engine = BISRAGEngine()

__all__ = [
    "BISRAGEngine",
    "rag_engine",
    "detect_bis_standard",
    "detect_bis_standard_structured",
    "BIS_PRODUCT_STANDARDS",
    "KnowledgeChunk",
    "SourceCitation"
]
