import json
from types import SimpleNamespace

from whatsapp_questionnaire import WhatsAppProductQuestionnaire, classify_product


class FakeSchemaProvider:
    """A provider stand-in proving custom products can receive generated questions."""

    def generate(self, query, system_instruction, retrieved_chunks, application_context=None):
        self.last_query = query
        schema = {
            "title": "Industrial gloves",
            "fields": [
                {
                    "id": "glove_coating",
                    "label": "What coating or finish do the gloves have?",
                    "type": "radio",
                    "options": ["Powder-free", "Powdered", "Textured", "Not sure"],
                    "required": True,
                    "helpText": "Select the finish on the product specification.",
                },
                {
                    "id": "application",
                    "label": "What will the gloves be used for?",
                    "type": "radio",
                    "options": ["Medical examination", "Industrial handling", "Food handling", "Other"],
                    "required": True,
                    "helpText": "",
                },
                {
                    "id": "model_details",
                    "label": "Enter model, material and thickness if known.",
                    "type": "text",
                    "options": [],
                    "required": False,
                    "helpText": "Use details from the product datasheet.",
                },
            ],
        }
        return SimpleNamespace(is_success=True, text=json.dumps(schema))


def test_product_classification_retains_common_categories():
    assert classify_product("steel water bottle") == "water_bottle"
    assert classify_product("school backpack") == "backpack"
    assert classify_product("RC car with rechargeable battery") == "rc_car"
    assert classify_product("industrial examination gloves") == "general"


def test_arbitrary_product_uses_generated_product_specific_questions(tmp_path):
    bot = WhatsAppProductQuestionnaire(str(tmp_path / "sessions.json"))
    started = bot.start(
        "user-1",
        "industrial latex examination gloves",
        llm_provider=FakeSchemaProvider(),
    )

    assert started["handled"] is True
    assert "coating" in started["question"].lower()
    assert started["list_title"]
    assert started["list_title"] != "Choose answer"
    assert "Powder-free" in started["options"]
    assert started["total_questions"] == 3

    step = bot.handle_reply("user-1", "Powder-free")
    assert step["question_number"] == 2
    assert "used for" in step["question"].lower()

    step = bot.handle_reply("user-1", "Medical examination")
    assert step["input_type"] == "text"
    assert "model" in step["question"].lower()

    result = bot.handle_reply("user-1", "Latex, non-sterile, 0.1 mm thickness")
    assert result["complete"] is True
    assert "Product name: industrial latex examination gloves" in result["rag_query"]
    assert "Powder-free" in result["rag_query"]
    assert "Latex, non-sterile, 0.1 mm thickness" in result["rag_query"]
    assert "Product details supplied by the user" in result["rag_query"]
    assert "Use only retrieved official BIS" not in result["rag_query"]
    assert "After retrieval, answer in this order" not in result["rag_query"]


def test_fallback_questionnaire_handles_water_bottle_and_finishes(tmp_path):
    bot = WhatsAppProductQuestionnaire(str(tmp_path / "sessions.json"))
    first = bot.start("user-2", "water bottle")
    assert first["handled"] is True
    assert first["total_questions"] >= 2
    assert first["options"]

    questions = list(bot._sessions["user-2"]["questions"])
    result = first
    for question in questions:
        answer = question["choices"][0] if question.get("choices") else "Product model and specification details"
        result = bot.handle_reply("user-2", answer)

    assert result["complete"] is True
    assert result["category"] == "water_bottle"
    assert "Product name: water bottle" in result["rag_query"]
    assert "Product details supplied by the user" in result["rag_query"]
    assert "Use only retrieved official BIS" not in result["rag_query"]
    assert "After retrieval, answer in this order" not in result["rag_query"]
    assert bot.has_session("user-2") is False


def test_questionnaire_state_persists_between_instances(tmp_path):
    store = str(tmp_path / "sessions.json")
    first_bot = WhatsAppProductQuestionnaire(store)
    first = first_bot.start("user-3", "school backpack")
    first_bot.handle_reply("user-3", first["options"][0])

    second_bot = WhatsAppProductQuestionnaire(store)
    assert second_bot.has_session("user-3") is True
    session = second_bot._sessions["user-3"]
    current = session["questions"][session["index"]]
    answer = current["choices"][0] if current.get("choices") else "Fabric and model details"
    next_question = second_bot.handle_reply("user-3", answer)
    assert next_question["handled"] is True
    assert next_question["question_number"] == 3


def test_questionnaire_can_be_cancelled(tmp_path):
    bot = WhatsAppProductQuestionnaire(str(tmp_path / "sessions.json"))
    bot.start("user-4", "RC car")

    result = bot.handle_reply("user-4", "cancel")

    assert result["handled"] is True
    assert result["cancelled"] is True
    assert bot.has_session("user-4") is False


class FakeCatalogue:
    def __init__(self, rows):
        self.rows = rows
        self.last_query = None

    def search(self, query, top_k=5):
        self.last_query = query
        return self.rows[:top_k]


def test_questionnaire_prompt_is_grounded_in_catalogue_candidates_and_scope_excerpts(tmp_path):
    provider = FakeSchemaProvider()
    catalogue = FakeCatalogue([
        {
            "is_number": "IS 17631:2022",
            "title": "Work Chairs — Specification",
            "technical_department": "Civil Engineering",
            "standard_type": "Product Specification",
        },
        {
            "is_number": "IS 17632:2022",
            "title": "General Purpose Chairs and Stools",
            "technical_department": "Civil Engineering",
            "standard_type": "Product Specification",
        },
    ])
    scope = SimpleNamespace(
        standard_code="IS 17631:2022",
        standard_title="Work Chairs — Specification",
        clause="Scope",
        content="Applies to work chairs; check exclusions and product scope.",
        source_url="https://www.bis.gov.in/example-work-chair-manual.pdf",
        verification_status="verified_official_record",
    )
    bot = WhatsAppProductQuestionnaire(str(tmp_path / "chair-sessions.json"))
    started = bot.start(
        "chair-user",
        "chair",
        llm_provider=provider,
        catalogue=catalogue,
        scope_evidence=[scope],
    )

    assert catalogue.last_query == "chair"
    assert "IS 17631:2022: Work Chairs — Specification" in provider.last_query
    assert "IS 17632:2022: General Purpose Chairs and Stools" in provider.last_query
    assert "Applies to work chairs" in provider.last_query
    assert "not proof that a standard applies" in provider.last_query
    assert started["total_questions"] == 3
