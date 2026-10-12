from rag.engine import BISRAGEngine
from rag.llm_provider import MockLLMProvider


def test_adult_hobby_rc_car_gets_scope_warning_not_children_toy_standard(tmp_path):
    engine = BISRAGEngine(
        storage_dir=str(tmp_path),
        use_dense=False,
        llm_provider=MockLLMProvider(),
    )
    query = (
        "Please assess BIS requirements for this exact product. "
        "Product name: rc car. Product type: Model / hobby vehicle. "
        "Intended user: Age 14+ / hobby use. Power source: Rechargeable battery. "
        "User role: Manufacturer. Help needed: applicable IS standard and certification process."
    )

    result = engine.answer_query(query)

    assert result["insufficient_evidence"] is True
    assert "standard scope needs confirmation" in result["content"].lower()
    assert "does not apply to scale models for adult collectors" in result["content"].lower()
    assert any("IS 15644:2006" in s["title"] for s in result["sources"])
    assert "IS 9873 (Part 1) : 2019" not in result["content"]
