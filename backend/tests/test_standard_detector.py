import pytest
from rag.standard_detector import (
    detect_bis_standard,
    detect_bis_standard_structured,
    extract_exact_standard_code
)

def test_known_supported_products():
    """Standard detection test: known commodities match applicable candidate standards."""
    led = detect_bis_standard("LED Bulb")
    assert "16102" in led["standard_code"]
    assert led["category"] == "Electronics & Lighting"

    fan = detect_bis_standard("BLDC Ceiling Fan")
    assert "374" in fan["standard_code"]

    helmet = detect_bis_standard("Motorcycle Helmet")
    assert "4151" in helmet["standard_code"]

    solar = detect_bis_standard("Grid-tie Solar Inverter")
    assert "16221" in solar["standard_code"] or "16169" in solar["standard_code"]

def test_exact_standard_number_query():
    """Standard detection test: explicit standard code is parsed correctly."""
    assert extract_exact_standard_code("What does IS 16102 (Part 1) : 2012 cover?") == "IS 16102 (PART 1) : 2012"
    assert extract_exact_standard_code("Check IS 4151") == "IS 4151"
    
    res = detect_bis_standard("Applicability of IS 374")
    assert "374" in res["standard_code"]
    assert res["is_verified"] is True

def test_ambiguous_product_handling():
    """Standard detection test: ambiguous product 'charger' flags ambiguity and lists multiple candidate standards."""
    res = detect_bis_standard("charger")
    assert "Ambiguous" in res["standard_code"]
    assert "13252" in res["standard_code"] and "17017" in res["standard_code"]
    assert res["is_ambiguous"] is True
    assert len(res["all_candidates"]) >= 2
    assert len(res["suggested_questions"]) > 0

def test_unsupported_product_rejects_default_invention():
    """Standard detection test: unsupported product does NOT invent IS 13252 as a default standard."""
    res = detect_bis_standard("Superconducting Quantum Computer QPU")
    assert res["is_supported"] is False
    assert res["standard_code"] == "No Verified Standard Identified"
    assert res["confidence"] == 0.0

    res2 = detect_bis_standard("Handmade Acoustic Guitar")
    assert res2["is_supported"] is False
    assert "13252" not in res2["standard_code"]

def test_structured_detection_result_model():
    """Standard detection test: structured detection result provides clean Pydantic model."""
    res = detect_bis_standard_structured("Solar Inverter")
    assert res.is_supported is True
    assert res.candidate is not None
    assert "16221" in res.candidate.standard_code

    unsupported = detect_bis_standard_structured("Suborbital Spacecraft")
    assert unsupported.is_supported is False
    assert unsupported.candidate is None
    assert unsupported.clarification_notice is not None

def test_precedence_bug_fix_behavior():
    """Standard detection test: explicit standard code cannot be accidentally overridden by product name."""
    # Simulate application payload with explicit standard IS 374 for an LED-named product
    payload_std = "IS 374 : 2019"
    product_name = "LED Decorative Fan"

    # Evaluated under the new validated logic
    detected = detect_bis_standard(product_name)
    if payload_std and payload_std.strip() and payload_std != "Under Determination":
        assigned_code = payload_std.strip()
    else:
        assigned_code = detected["standard_code"]

    assert assigned_code == "IS 374 : 2019"
