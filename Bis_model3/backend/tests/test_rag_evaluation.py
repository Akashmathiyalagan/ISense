import pytest
from typing import List, Dict, Any
from rag.engine import BISRAGEngine
from rag.llm_provider import MockLLMProvider

# Curated Gold Benchmark Dataset for BIS RAG Pipeline Evaluation
BENCHMARK_DATASET: List[Dict[str, Any]] = [
    {
        "query": "What is the insulation resistance required for self-ballasted LED lamps?",
        "expected_standard": "IS 16102",
        "expected_keywords": ["4.0 megohms", "500v dc"],
        "is_supported": True
    },
    {
        "query": "How fast must a photovoltaic grid-tied inverter trip during islanding condition?",
        "expected_standard": ["IS 16221", "IS 16169"],
        "expected_keywords": ["2.0 seconds", "islanding"],
        "is_supported": True
    },
    {
        "query": "What is the peak deceleration threshold for motorcycle protective helmets?",
        "expected_standard": "IS 4151",
        "expected_keywords": ["300g", "150g", "5.0 milliseconds"],
        "is_supported": True
    },
    {
        "query": "What is the minimum air delivery for a 1200mm sweep electric ceiling fan?",
        "expected_standard": "IS 374",
        "expected_keywords": ["210", "service value"],
        "is_supported": True
    },
    {
        "query": "What is the external short circuit resistance for secondary lithium cells under IS 16046?",
        "expected_standard": "IS 16046",
        "expected_keywords": ["80", "short circuit", "55"],
        "is_supported": True
    },
    {
        "query": "What is the small parts cylinder diameter test for children toy safety?",
        "expected_standard": "IS 9873",
        "expected_keywords": ["31.7 mm", "choking"],
        "is_supported": True
    },
    {
        "query": "What glow-wire temperature is required for plug and socket insulating components under IS 1293?",
        "expected_standard": "IS 1293",
        "expected_keywords": ["750°c", "glow-wire"],
        "is_supported": True
    },
    {
        "query": "What hi-pot dielectric test voltage is required between primary and secondary circuits in IT equipment adapters?",
        "expected_standard": "IS 13252",
        "expected_keywords": ["3000v ac", "dielectric"],
        "is_supported": True
    },
    {
        "query": "What is the mechanical crush resistance required for electric vehicle conductive charging connectors?",
        "expected_standard": "IS 17017",
        "expected_keywords": ["5000 n", "drive-over"],
        "is_supported": True
    },
    {
        "query": "What are the statutory penalties under Section 29 of the BIS Act 2016 for unauthorized standard mark use?",
        "expected_standard": "BIS Act 2016",
        "expected_keywords": ["two years", "two lakh rupees"],
        "is_supported": True
    },
    # Negative / Unsupported Benchmark Queries (Must Abstain)
    {
        "query": "What is the minimum warp drive hypercharge for suborbital spacecraft navigation?",
        "expected_standard": None,
        "expected_keywords": [],
        "is_supported": False
    },
    {
        "query": "What are the official BIS regulations regarding quantum teleportation repeaters?",
        "expected_standard": None,
        "expected_keywords": [],
        "is_supported": False
    }
]

@pytest.fixture
def rag_engine():
    return BISRAGEngine(use_dense=True, min_relevance_threshold=0.10)

def test_retrieval_benchmark_metrics(rag_engine):
    """
    Executes formal RAG retrieval evaluation over the curated gold benchmark dataset.
    Measures:
    - Recall@3
    - Precision@3
    - Mean Reciprocal Rank (MRR)
    - Citation Precision Rate
    - Abstention Quality on unsupported queries
    """
    k = 3
    recalls = []
    precisions = []
    reciprocal_ranks = []
    correct_citations = 0
    total_citations = 0
    abstention_success = 0
    total_unsupported = 0

    for item in BENCHMARK_DATASET:
        query = item["query"]
        expected_std = item["expected_standard"]
        is_supported = item["is_supported"]

        results = rag_engine.retrieve_with_scores(query, top_k=k)
        retrieved_stds = [r.chunk.standard_code for r in results]

        if is_supported:
            def matches_std(std: str) -> bool:
                if isinstance(expected_std, list):
                    return any(s.lower() in std.lower() for s in expected_std)
                return expected_std.lower() in std.lower()

            hits = [1 for std in retrieved_stds if matches_std(std)]
            hit_count = sum(hits)
            recalls.append(1.0 if hit_count > 0 else 0.0)
            precisions.append(hit_count / float(k))

            # Calculate Reciprocal Rank
            rr = 0.0
            for rank_idx, std in enumerate(retrieved_stds):
                if matches_std(std):
                    rr = 1.0 / (rank_idx + 1)
                    break
            reciprocal_ranks.append(rr)

            # Check Citation Precision
            for r in results:
                total_citations += 1
                if matches_std(r.chunk.standard_code):
                    correct_citations += 1
        else:
            total_unsupported += 1
            # For unsupported queries, retrieval should yield below threshold or engine should abstain
            resp = rag_engine.answer_query(query, llm_provider_override=MockLLMProvider())
            if resp["insufficient_evidence"] is True:
                abstention_success += 1

    mean_recall = sum(recalls) / len(recalls) if recalls else 0.0
    mean_precision = sum(precisions) / len(precisions) if precisions else 0.0
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0
    citation_precision = correct_citations / total_citations if total_citations else 0.0
    abstention_rate = abstention_success / total_unsupported if total_unsupported else 1.0

    print("\n" + "=" * 60)
    print("ISENSE RAG RETRIEVAL & GROUNDING EVALUATION REPORT")
    print("=" * 60)
    print(f"Total Benchmark Queries:     {len(BENCHMARK_DATASET)}")
    print(f"Supported Test Queries:      {len(recalls)}")
    print(f"Unsupported Test Queries:    {total_unsupported}")
    print(f"Recall@{k}:                    {mean_recall:.2%}")
    print(f"Precision@{k}:                 {mean_precision:.2%}")
    print(f"Mean Reciprocal Rank (MRR):  {mrr:.4f}")
    print(f"Citation Precision Rate:     {citation_precision:.2%}")
    print(f"Abstention Quality Rate:     {abstention_rate:.2%}")
    print("=" * 60)

    # Verification Assertions
    assert mean_recall >= 0.90, f"Recall@{k} ({mean_recall:.2f}) was below required 0.90 threshold"
    assert mrr >= 0.85, f"MRR ({mrr:.4f}) was below required 0.85 threshold"
    assert abstention_rate == 1.0, f"Abstention rate ({abstention_rate:.2f}) failed on unsupported queries"
    assert citation_precision >= 0.80, f"Citation precision ({citation_precision:.2f}) was below 0.80"
