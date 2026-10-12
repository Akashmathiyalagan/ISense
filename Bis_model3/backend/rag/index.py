import os
import re
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from rag.models import KnowledgeChunk, RetrievalResult, SourceCitation

logger = logging.getLogger("isense_index")

class BISSearchIndex:
    def __init__(
        self,
        chunks: Optional[List[KnowledgeChunk]] = None,
        use_dense: bool = True,
        min_relevance_threshold: float = 0.20
    ):
        self.chunks: List[KnowledgeChunk] = chunks or []
        self.min_relevance_threshold = min_relevance_threshold
        self.use_dense = use_dense
        self.dense_model = None
        self.dense_embeddings: Optional[np.ndarray] = None
        self.bm25_model = None
        self.tokenized_corpus: List[List[str]] = []
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.is_indexed = False

        self._init_models()
        if self.chunks:
            self.build_index(self.chunks)

    def _init_models(self):
        """Initializes dense sentence-transformer and lexical models."""
        if self.use_dense:
            try:
                from sentence_transformers import SentenceTransformer
                try:
                    self.dense_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", local_files_only=True)
                except Exception:
                    self.dense_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
                logger.info("Dense SentenceTransformer (all-MiniLM-L6-v2) initialized successfully.")
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer, activating TF-IDF fallback: {e}")
                self.dense_model = None

    def tokenize_text(self, text: str) -> List[str]:
        """Simple, deterministic tokenizer for BM25 lexical search."""
        return re.findall(r'\b[a-zA-Z0-9_\-\.\:\/]+\b', text.lower())

    def build_index(self, chunks: List[KnowledgeChunk]):
        """Builds both dense vector index and BM25 lexical index over chunks."""
        self.chunks = chunks
        if not chunks:
            self.is_indexed = False
            return

        corpus_texts = [
            f"{c.standard_code} {c.standard_title} {c.clause} {c.category} {c.content}"
            for c in chunks
        ]

        # 1. Lexical BM25 Index
        try:
            from rank_bm25 import BM25Okapi
            self.tokenized_corpus = [self.tokenize_text(text) for text in corpus_texts]
            self.bm25_model = BM25Okapi(self.tokenized_corpus)
            logger.info(f"BM25 index built with {len(chunks)} documents.")
        except Exception as e:
            logger.error(f"Failed to build BM25 index: {e}")
            self.bm25_model = None

        # 2. Dense Semantic Embeddings Index
        if self.dense_model is not None:
            try:
                embs = self.dense_model.encode(corpus_texts, convert_to_numpy=True, show_progress_bar=False)
                # Normalize for cosine similarity via dot product
                norms = np.linalg.norm(embs, axis=1, keepdims=True)
                norms[norms == 0] = 1e-10
                self.dense_embeddings = embs / norms
                logger.info(f"Dense embeddings generated: shape {self.dense_embeddings.shape}")
            except Exception as e:
                logger.warning(f"Dense embedding encoding failed, switching to TF-IDF fallback: {e}")
                self.dense_embeddings = None

        # 3. TF-IDF Fallback Vectorizer
        if self.dense_embeddings is None:
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                self.tfidf_vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english')
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus_texts)
                logger.info(f"TF-IDF sparse index initialized as fallback ({len(chunks)} chunks).")
            except Exception as e:
                logger.error(f"Failed to initialize TF-IDF fallback: {e}")

        self.is_indexed = True

    def query_embedding(self, query: str) -> Optional[np.ndarray]:
        """Encodes query string into dense vector if dense model is available."""
        if self.dense_model is not None:
            try:
                q_emb = self.dense_model.encode([query], convert_to_numpy=True)[0]
                norm = np.linalg.norm(q_emb)
                return q_emb / (norm if norm > 0 else 1e-10)
            except Exception as e:
                logger.warning(f"Query embedding generation failed: {e}")
        return None

    def search(
        self,
        query: str,
        top_k: int = 4,
        standard_filter: Optional[str] = None,
        alpha: float = 0.55,
        min_threshold: Optional[float] = None
    ) -> List[RetrievalResult]:
        """
        Executes hybrid dense + BM25 retrieval with standard-code exact matching boosts.
        Returns scored, filtered, and deduplicated RetrievalResult list.
        """
        if not self.chunks or not query.strip():
            return []

        threshold = min_threshold if min_threshold is not None else self.min_relevance_threshold
        num_chunks = len(self.chunks)
        dense_scores = np.zeros(num_chunks)
        bm25_scores = np.zeros(num_chunks)

        # A. Dense Vector Similarity (or TF-IDF fallback)
        if self.dense_embeddings is not None:
            q_emb = self.query_embedding(query)
            if q_emb is not None:
                dense_scores = np.dot(self.dense_embeddings, q_emb)
                # Clip negative cosine similarities to 0
                dense_scores = np.clip(dense_scores, 0.0, 1.0)
        elif self.tfidf_vectorizer is not None and self.tfidf_matrix is not None:
            from sklearn.metrics.pairwise import cosine_similarity
            q_vec = self.tfidf_vectorizer.transform([query])
            dense_scores = cosine_similarity(q_vec, self.tfidf_matrix).flatten()

        # B. Lexical BM25 Scoring
        if self.bm25_model is not None:
            tokenized_q = self.tokenize_text(query)
            if tokenized_q:
                raw_bm25 = np.array(self.bm25_model.get_scores(tokenized_q))
                # Clip negative BM25 scores from small-corpus negative IDF
                raw_bm25 = np.clip(raw_bm25, 0.0, None)
                max_bm25 = np.max(raw_bm25) if np.max(raw_bm25) > 0 else 1.0
                bm25_scores = raw_bm25 / max_bm25

        # C. Exact Standard-Number Matching Boost
        standard_boost = np.zeros(num_chunks)
        clean_q = query.upper().replace(" ", "").replace(":", "").replace("-", "")
        # Detect exact standard codes like IS16102, IS374, IS4151
        std_matches = re.findall(r'IS\s*(\d+)', query, re.IGNORECASE)

        for i, chunk in enumerate(self.chunks):
            chunk_std = chunk.standard_code.upper().replace(" ", "").replace(":", "").replace("-", "")
            # Exact standard match
            if standard_filter and (standard_filter.lower() in chunk.standard_code.lower()):
                standard_boost[i] += 0.50
            for sm in std_matches:
                if f"IS{sm}" in chunk_std or sm in chunk.standard_code:
                    standard_boost[i] += 0.60
                    break

        # D. Hybrid Score Fusion
        # If dense embeddings are not available, give full weight to BM25 lexical scores
        has_dense = self.dense_embeddings is not None or (self.tfidf_matrix is not None and self.tfidf_vectorizer is not None)
        effective_alpha = alpha if has_dense else 0.0
        hybrid_scores = (effective_alpha * dense_scores) + ((1.0 - effective_alpha) * bm25_scores) + standard_boost

        # E. Ranking and Deduplication
        ranked_indices = np.argsort(hybrid_scores)[::-1]
        results: List[RetrievalResult] = []
        seen_contents = set()

        for idx in ranked_indices:
            score = float(hybrid_scores[idx])
            if score < threshold:
                # Discard results strictly below relevance threshold
                continue
            chunk = self.chunks[idx]

            # Standard filter constraint if strict
            if standard_filter and standard_filter.strip():
                if standard_filter.lower() not in chunk.standard_code.lower() and standard_boost[idx] == 0:
                    continue

            # Deduplication by content snippet
            content_key = chunk.content[:80].strip().lower()
            if content_key in seen_contents:
                continue
            seen_contents.add(content_key)

            results.append(RetrievalResult(
                chunk=chunk,
                dense_score=float(dense_scores[idx]),
                bm25_score=float(bm25_scores[idx]),
                hybrid_score=round(score, 4),
                match_type="hybrid" if self.dense_embeddings is not None else "lexical_bm25"
            ))

            if len(results) >= top_k:
                break

        return results

def construct_citations(retrieval_results: List[RetrievalResult]) -> List[SourceCitation]:
    """Constructs verified citations from retrieved evidence chunks."""
    citations: List[SourceCitation] = []
    for r in retrieval_results:
        c = r.chunk
        citations.append(SourceCitation(
            id=c.chunk_id,
            title=f"{c.standard_code} — {c.standard_title}",
            documentRef=c.standard_code,
            page=c.page,
            section=c.clause,
            excerpt=c.content[:200] + ("..." if len(c.content) > 200 else ""),
            sourceUrl=c.source_url,
            verification_status=c.verification_status,
            confidence=round(r.hybrid_score, 3)
        ))
    return citations
