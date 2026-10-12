import json

from whatsapp_questionnaire import WhatsAppProductQuestionnaire, classify_product


def test_product_classification_selects_product_specific_questions(tmp_path):
    bot = WhatsAppProductQuestionnaire(str(tmp_path / "sessions.json"))

    assert classify_product("steel water bottle") == "water_bottle"
    assert classify_product("school backpack") == "backpack"
    assert classify_product("RC car with rechargeable battery") == "rc_car"
    assert classify_product("unknown kitchen item") == "general"

    started = bot.start("user-1", "steel water bottle")
    assert started["handled"] is True
    assert started["question_number"] == 1
    assert "main material" in started["question"].lower()
    assert "Stainless steel" in started["options"]


def test_questionnaire_advances_and_produces_rag_query(tmp_path):
    bot = WhatsAppProductQuestionnaire(str(tmp_path / "sessions.json"))
    first = bot.start("user-1", "water bottle")
    assert first["question_number"] == 1

    step = bot.handle_reply("user-1", "Stainless steel")
    assert step["handled"] is True
    assert step["question_number"] == 2
    assert "capacity" in step["question"].lower()

    answers = [
        "500 ml or less",
        "Insulated",
        "Sell in India",
        "Made in India",
        "Applicable IS standard",
    ]
    result = None
    for answer in answers:
        result = bot.handle_reply("user-1", answer)

    assert result is not None
    assert result["handled"] is True
    assert result["complete"] is True
    assert result["category"] == "water_bottle"
    assert "Product name: water bottle" in result["rag_query"]
    assert "Material: Stainless steel" in result["rag_query"]
    assert "not regulatory evidence" in result["rag_query"]
    assert bot.has_session("user-1") is False


def test_questionnaire_state_persists_between_instances(tmp_path):
    store = str(tmp_path / "sessions.json")
    first_bot = WhatsAppProductQuestionnaire(store)
    first_bot.start("user-2", "backpack")
    first_bot.handle_reply("user-2", "School backpack")

    second_bot = WhatsAppProductQuestionnaire(store)
    assert second_bot.has_session("user-2") is True
    next_question = second_bot.handle_reply("user-2", "Textile / fabric")
    assert next_question["question_number"] == 3
    assert "designed for" in next_question["question"].lower()


def test_questionnaire_can_be_cancelled(tmp_path):
    bot = WhatsAppProductQuestionnaire(str(tmp_path / "sessions.json"))
    bot.start("user-3", "RC car")

    result = bot.handle_reply("user-3", "cancel")

    assert result["handled"] is True
    assert result["cancelled"] is True
    assert bot.has_session("user-3") is False
