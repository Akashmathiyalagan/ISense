import hashlib
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DocumentMetadata(BaseModel):
    document_id: str
    standard_code: str
    standard_title: str
    authority: str
    scheme: str
    category: str
    publication_date: Optional[str] = None
    source_url: str
    verification_status: str = "verified_official_record"
    file_path: Optional[str] = None
    content_hash: Optional[str] = None
    ingested_at: Optional[str] = None

class KnowledgeChunk(BaseModel):
    chunk_id: str
    document_id: str
    standard_code: str
    standard_title: str
    clause: str
    page: Optional[int] = None
    content: str
    category: str
    authority: str
    verification_status: str = "verified_official_record"
    source_url: str
    publication_date: Optional[str] = None

    @classmethod
    def generate_chunk_id(cls, doc_id: str, clause: str, chunk_idx: int, content: str) -> str:
        digest = hashlib.sha256(f"{doc_id}:{clause}:{chunk_idx}:{content}".encode("utf-8")).hexdigest()[:12]
        return f"chk-{doc_id.lower().replace('_', '-')}-{digest}"

class RetrievalResult(BaseModel):
    chunk: KnowledgeChunk
    dense_score: float = 0.0
    bm25_score: float = 0.0
    hybrid_score: float = 0.0
    match_type: str = "hybrid"

class SourceCitation(BaseModel):
    id: str
    title: str
    documentRef: str
    page: Optional[int] = None
    section: str
    excerpt: str
    sourceUrl: str
    verification_status: str = "verified_official_record"
    confidence: Optional[float] = None

class CandidateStandard(BaseModel):
    standard_code: str
    standard_title: str
    category: str
    scheme: str
    division: str
    scope_summary: str
    checklist: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    is_verified: bool = False
    confidence: float = 0.0
    match_type: str = "unmatched"

class DetectionResult(BaseModel):
    query: str
    candidate: Optional[CandidateStandard] = None
    all_candidates: List[CandidateStandard] = Field(default_factory=list)
    is_exact_match: bool = False
    is_ambiguous: bool = False
    is_supported: bool = True
    suggested_questions: List[str] = Field(default_factory=list)
    clarification_notice: Optional[str] = None

class RAGResponse(BaseModel):
    content: str
    sources: List[SourceCitation] = Field(default_factory=list)
    confidence: float = 0.0
    insufficient_evidence: bool = False
    warnings: List[str] = Field(default_factory=list)
    model_provider: str = "unconfigured"
    retrieval_count: int = 0
