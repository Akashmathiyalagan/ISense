import csv

from rag.catalogue import BISStandardCatalogue
from rag.engine import BISRAGEngine
from rag.llm_provider import MockLLMProvider


def make_csv(path):
    rows = [
        {
            "is_number": "IS 9020:2020",
            "title": "Specification for Industrial Pressure Gauge Valve",
            "technical_department": "Mechanical Engineering Department",
            "sectional_committee": "MED 40",
            "standard_type": "Product Specification",
            "published_on": "2020-05-10",
            "bis_record_id": "12345",
        }
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def test_rag_uses_catalogue_candidates_without_promoting_them_to_regulatory_evidence(tmp_path):
    csv_path = tmp_path / "catalogue.csv"
    make_csv(csv_path)

    engine = BISRAGEngine(
        storage_dir=str(tmp_path / "storage"),
        use_dense=False,
        llm_provider=MockLLMProvider(),
    )
    engine.catalogue = BISStandardCatalogue(csv_path)

    answer = engine.answer_query(
        "What BIS standard applies to an industrial pressure gauge valve?"
    )

    assert answer["insufficient_evidence"] is True
    assert "Catalogue matches to investigate" in answer["content"]
    assert "IS 9020:2020" in answer["content"]
    assert "does not prove" in answer["content"].lower() or "does not establish" in answer["content"].lower()
    assert any(source["verification_status"] == "catalogue_metadata_only" for source in answer["sources"])
