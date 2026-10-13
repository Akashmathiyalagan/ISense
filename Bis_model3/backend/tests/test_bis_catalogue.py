import csv

from rag.catalogue import BISStandardCatalogue


def write_catalogue(path):
    rows = [
        {
            "is_number": "IS 9020:2020",
            "title": "Specification for Industrial Pressure Gauge Valve",
            "technical_department": "Mechanical Engineering Department",
            "sectional_committee": "MED 40",
            "standard_type": "Product Specification",
            "published_on": "2020-05-10",
            "bis_record_id": "12345",
        },
        {
            "is_number": "IS 1234 (Part 1):2018",
            "title": "Safety Requirements for Electric Toys",
            "technical_department": "Consumer Products Department",
            "sectional_committee": "CPD 24",
            "standard_type": "Product Specification",
            "published_on": "2018-03-01",
            "bis_record_id": "54321",
        },
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def test_catalogue_loads_records_and_marks_them_metadata_only(tmp_path):
    source = tmp_path / "catalogue.csv"
    write_catalogue(source)

    catalogue = BISStandardCatalogue(source)

    assert catalogue.status()["loaded"] is True
    assert catalogue.status()["records"] == 2
    hits = catalogue.search("pressure gauge valve standard", top_k=3)
    assert hits
    assert hits[0]["is_number"] == "IS 9020:2020"
    assert hits[0]["evidence_level"] == "catalogue_metadata_only"
    assert hits[0]["source_url"].startswith("https://standards.bis.gov.in/")


def test_exact_standard_lookup_takes_precedence(tmp_path):
    source = tmp_path / "catalogue.csv"
    write_catalogue(source)

    catalogue = BISStandardCatalogue(source)
    hits = catalogue.search("Explain IS 1234 Part 1 requirements", top_k=5)

    assert hits
    assert hits[0]["is_number"] == "IS 1234 (Part 1):2018"
    assert hits[0]["evidence_level"] == "catalogue_metadata_only"


def test_empty_or_missing_catalogue_fails_safely(tmp_path):
    catalogue = BISStandardCatalogue(tmp_path / "missing.csv")

    assert catalogue.status()["loaded"] is False
    assert catalogue.search("pressure gauge valve") == []
