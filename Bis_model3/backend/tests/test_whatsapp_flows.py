import json

# Import these helpers from main only in project test environment.
def test_product_only_message_triggers_flow():
    from main import should_open_product_intake_flow
    assert should_open_product_intake_flow("water bottle")
    assert should_open_product_intake_flow("I made a steel water bottle")
    assert should_open_product_intake_flow("back bag")

def test_regulatory_question_does_not_trigger_flow():
    from main import should_open_product_intake_flow
    assert not should_open_product_intake_flow("What documents are needed for a water bottle?")
    assert not should_open_product_intake_flow("IS 9873 testing requirements")
    assert not should_open_product_intake_flow("hi")

def test_flow_submission_parser():
    from main import format_flow_submission, flow_submission_to_query
    values = {"product_name": "Water bottle", "material": "stainless_steel", "capacity": "750 ml"}
    parsed = format_flow_submission(json.dumps({"flow_response": values, "flow_token": "token"}))
    assert parsed == values
    query = flow_submission_to_query(parsed)
    assert "Water bottle" in query and "750 ml" in query
