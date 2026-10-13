import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rag.product_questionnaire import build_questionnaire, fallback_questionnaire, _parse_schema


def test_fallback_questions_are_compact_and_do_not_ask_generic_compliance_details():
    data = build_questionnaire("steel water bottle")
    assert data["product"] == "steel water bottle"
    assert 2 <= len(data["fields"]) <= 3
    assert any(f["id"] == "intended_use" for f in data["fields"])
    assert not any(f["id"] in {"origin", "business_activity", "help_needed"} for f in data["fields"])
    assert data["redirectPath"].startswith("/apps?product=")


def test_backpack_fallback_asks_about_actual_subtype_and_use():
    data = fallback_questionnaire("school backpack")
    assert any(f["id"] == "product_subtype" for f in data["fields"])
    assert any(f["id"] == "intended_use" for f in data["fields"])
    assert not any(f["id"] == "capacity" for f in data["fields"])
    assert not any(f["id"] == "bag_type" for f in data["fields"])


def test_unknown_product_gets_compact_product_identification_questions():
    data = fallback_questionnaire("industrial gasket")
    assert 2 <= len(data["fields"]) <= 3
    assert any(f["id"] == "intended_use" for f in data["fields"])
    assert any(f["id"] == "product_subtype" for f in data["fields"])
    assert not any(f["id"] in {"origin", "business_activity", "help_needed"} for f in data["fields"])


def test_schema_parser_rejects_invalid_options():
    raw = '{"title":"Tell us","fields":[{"id":"type","label":"Type?","type":"radio","options":["A"],"required":true}]}'
    assert _parse_schema(raw, "widget") is None


def test_schema_parser_accepts_valid_schema():
    raw = '{"title":"Tell us","fields":[{"id":"type","label":"Type?","type":"radio","options":["A","B"],"required":true},{"id":"use","label":"Intended use?","type":"checkbox","options":["Home","Commercial"],"required":true}]}'
    data = _parse_schema(raw, "widget")
    assert data is not None and len(data["fields"]) == 2
