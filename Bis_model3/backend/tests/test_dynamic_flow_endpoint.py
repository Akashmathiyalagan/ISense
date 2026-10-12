import json
from pathlib import Path

from whatsapp_flow_endpoint import choose_product_screen, _response_for_request


def test_product_routing():
    assert choose_product_screen("steel water bottle") == "WATER_BOTTLE"
    assert choose_product_screen("school backpack") == "BACKPACK"
    assert choose_product_screen("RC car") == "RC_CAR"
    assert choose_product_screen("solar inverter") == "OTHER_PRODUCT"


def test_endpoint_init_routes_product():
    result = _response_for_request({"action": "data_exchange", "screen": "PRODUCT_ROUTER", "data": {"product_name": "back bag"}})
    assert result["screen"] == "BACKPACK"
    assert result["data"]["product_name"] == "back bag"


def test_flow_json_structure():
    p = Path(__file__).parents[1] / "whatsapp_flows" / "isense_dynamic_product_flow.json"
    flow = json.loads(p.read_text(encoding="utf-8"))
    assert flow["data_api_version"] == "3.0"
    ids = {screen["id"] for screen in flow["screens"]}
    assert {"PRODUCT_ROUTER", "WATER_BOTTLE", "BACKPACK", "RC_CAR", "OTHER_PRODUCT"} <= ids
