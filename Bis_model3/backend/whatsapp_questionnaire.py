"""Stateful conversational product questionnaire for ISense WhatsApp.

This alternative uses normal WhatsApp interactive list messages and does not
require a published WhatsApp Flow. User answers are product context, never
regulatory evidence.
"""
import json
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from rag.product_questionnaire import build_questionnaire


QUESTION_SETS: Dict[str, List[Dict[str, Any]]] = {
    "water_bottle": [
        {"key": "material", "prompt": "What is the main material?", "list_title": "Choose material", "choices": ["Stainless steel", "Plastic", "Glass", "Aluminium", "Other / not sure"]},
        {"key": "capacity", "prompt": "What is its capacity?", "list_title": "Choose capacity", "choices": ["250 ml or less", "251–750 ml", "751 ml–1 litre", "Above 1 litre", "Not sure"]},
        {"key": "insulation", "prompt": "Is it insulated?", "list_title": "Insulation", "choices": ["Insulated", "Non-insulated", "Not sure"]},
        {"key": "business_activity", "prompt": "What best describes your activity?", "list_title": "Your activity", "choices": ["Personal use", "Manufacture in India", "Sell in India", "Import into India"]},
        {"key": "origin", "prompt": "Where is it manufactured?", "list_title": "Product origin", "choices": ["Made in India", "Imported", "Not sure"]},
        {"key": "help_needed", "prompt": "What BIS guidance do you need?", "list_title": "BIS guidance", "choices": ["Applicable IS standard", "Certification / registration", "Testing requirements", "Marking / labelling", "All of these"]},
    ],
    "backpack": [
        {"key": "bag_type", "prompt": "What kind of bag is it?", "list_title": "Bag type", "choices": ["School backpack", "Laptop backpack", "Travel backpack", "Trekking backpack", "Other / not sure"]},
        {"key": "material", "prompt": "What is the main material?", "list_title": "Choose material", "choices": ["Textile / fabric", "Leather", "Synthetic / plastic", "Mixed materials", "Other / not sure"]},
        {"key": "intended_user", "prompt": "Who is it mainly designed for?", "list_title": "Intended user", "choices": ["Children / school use", "Adults", "All ages", "Not sure"]},
        {"key": "business_activity", "prompt": "What best describes your activity?", "list_title": "Your activity", "choices": ["Personal use", "Manufacture in India", "Sell in India", "Import into India"]},
        {"key": "origin", "prompt": "Where is it manufactured?", "list_title": "Product origin", "choices": ["Made in India", "Imported", "Not sure"]},
        {"key": "help_needed", "prompt": "What BIS guidance do you need?", "list_title": "BIS guidance", "choices": ["Applicable IS standard", "Certification / registration", "Testing requirements", "Marking / labelling", "All of these"]},
    ],
    "rc_car": [
        {"key": "vehicle_type", "prompt": "What type of RC car is it?", "list_title": "Vehicle type", "choices": ["Toy RC car", "Hobby / model vehicle", "Other / not sure"]},
        {"key": "power_source", "prompt": "How is it powered?", "list_title": "Power source", "choices": ["Rechargeable battery", "Replaceable batteries", "No battery / other", "Not sure"]},
        {"key": "intended_age", "prompt": "Who is it intended for?", "list_title": "Age group", "choices": ["Under 3 years", "3 to 8 years", "Above 8 years", "Adult hobby use", "Not sure"]},
        {"key": "material", "prompt": "What is the main body material?", "choices": ["Plastic", "Metal", "Mixed materials", "Not sure"]},
        {"key": "origin", "prompt": "Where is it manufactured?", "list_title": "Product origin", "choices": ["Made in India", "Imported", "Not sure"]},
        {"key": "help_needed", "prompt": "What BIS guidance do you need?", "list_title": "BIS guidance", "choices": ["Applicable IS standard", "Certification / registration", "Toy safety / testing", "Marking / labelling", "All of these"]},
    ],
    "general": [
        {"key": "product_type", "prompt": "Which product type describes it best?", "list_title": "Product type", "choices": ["Electrical / electronic", "Household product", "Toy / children's product", "Food-contact product", "Textile / bag", "Other / not sure"]},
        {"key": "material", "prompt": "What is its main material?", "choices": ["Metal", "Plastic", "Textile / fabric", "Glass / ceramic", "Mixed materials", "Other / not sure"]},
        {"key": "business_activity", "prompt": "What best describes your activity?", "list_title": "Your activity", "choices": ["Personal use", "Manufacture in India", "Sell in India", "Import into India"]},
        {"key": "origin", "prompt": "Where is it manufactured?", "list_title": "Product origin", "choices": ["Made in India", "Imported", "Not sure"]},
        {"key": "help_needed", "prompt": "What BIS guidance do you need?", "list_title": "BIS guidance", "choices": ["Applicable IS standard", "Certification / registration", "Testing requirements", "Marking / labelling", "All of these"]},
    ],
}


def _default_list_title(question_key: str) -> str:
    """Return a concise title for the WhatsApp list picker (maximum 20 chars)."""
    titles = {
        "material": "Choose material",
        "capacity": "Choose capacity",
        "insulation": "Insulation",
        "insulation_type": "Insulation design",
        "business_activity": "Your activity",
        "origin": "Product origin",
        "help_needed": "BIS guidance",
        "bag_type": "Bag type",
        "intended_user": "Intended user",
        "vehicle_type": "Vehicle type",
        "power_source": "Power source",
        "intended_age": "Age group",
        "product_type": "Product type",
    }
    return titles.get(question_key, "Choose answer")


def _short_picker_title(field_id: str, label: str) -> str:
    """Build a readable WhatsApp list-opening title (Meta limit: 20 chars)."""
    known = {
        "material": "Material?",
        "capacity": "Capacity?",
        "insulation": "Insulation?",
        "intended_use": "Intended use?",
        "origin": "Made where?",
        "business_activity": "Your activity?",
        "help_needed": "BIS help needed?",
        "product_type": "Product type?",
        "vehicle_type": "Vehicle type?",
        "power_source": "Power source?",
        "intended_user": "Intended user?",
        "intended_age": "Age group?",
        "bag_type": "Bag type?",
        "features": "Features?",
        "specifications": "Ratings / size?",
    }
    if field_id in known:
        return known[field_id]
    cleaned = " ".join((label or "").replace("?", "").split())
    for prefix in ("What is ", "What type of ", "Which ", "Who is ", "Where is ", "How is ", "What ", "Does it ", "Is it "):
        if cleaned.casefold().startswith(prefix.casefold()):
            cleaned = cleaned[len(prefix):]
            break
    cleaned = cleaned.strip().capitalize()
    return (cleaned[:19] + "?")[:20] if cleaned else "Choose answer"


def _questions_from_schema(product_name: str, llm_provider: Any = None) -> List[Dict[str, Any]]:
    """Use Gemini-generated product-specific fields; sanitize them for WhatsApp list/text UX."""
    schema = build_questionnaire(product_name, llm_provider)
    result: List[Dict[str, Any]] = []
    for field in schema.get("fields", [])[:8]:
        if not isinstance(field, dict):
            continue
        field_id = str(field.get("id") or "").strip()[:40]
        label = str(field.get("label") or "").strip()[:180]
        field_type = str(field.get("type") or "text").lower()
        options = field.get("options", [])
        if not field_id or not label:
            continue
        if field_type in {"radio", "checkbox"} and isinstance(options, list):
            choices = [str(item).strip()[:100] for item in options if str(item).strip()][:10]
            if len(choices) < 2:
                field_type = "text"
                choices = []
        else:
            field_type = "text"
            choices = []
        result.append({
            "key": field_id,
            "prompt": label,
            "list_title": _short_picker_title(field_id, label),
            "choices": choices,
            "input_type": field_type,
            "help_text": str(field.get("helpText") or "")[:240],
        })
    if len(result) < 2:
        # build_questionnaire itself has a validated fallback; this is a last
        # safety net against malformed or unexpectedly empty schemas.
        result = [
            {
                "key": "product_type",
                "prompt": "What exact product type, model or variant is this?",
                "list_title": "Product type?",
                "choices": [],
                "input_type": "text",
                "help_text": "Include model, size, rating, or construction if known.",
            },
            {
                "key": "intended_use",
                "prompt": "What is the intended use and user group?",
                "list_title": "Intended use?",
                "choices": ["Household / consumer", "Children / toy", "Commercial / industrial", "Professional / medical", "Other / not sure"],
                "input_type": "radio",
                "help_text": "",
            },
            {
                "key": "business_activity",
                "prompt": "What is your role?",
                "list_title": "Your role?",
                "choices": ["Personal use", "Manufacturer", "Importer", "Seller / distributor", "Other / not sure"],
                "input_type": "radio",
                "help_text": "",
            },
        ]
    return result


def classify_product(product_name: str) -> str:
    """Retain broad category labels for logging and legacy integrations."""
    text = " ".join((product_name or "").lower().split())
    if any(term in text for term in ("water bottle", "bottle", "flask", "thermos", "tumbler")):
        return "water_bottle"
    if any(term in text for term in ("backpack", "back pack", "back bag", "school bag", "rucksack", "bag")):
        return "backpack"
    if any(term in text for term in ("rc car", "remote control car", "toy car", "toy vehicle")):
        return "rc_car"
    return "general"


def _questions_for_session(session: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return the validated, per-product questionnaire saved for this session."""
    stored = session.get("questions")
    if isinstance(stored, list) and stored:
        return stored
    # Backward compatibility for sessions created before dynamic schemas were stored.
    return list(QUESTION_SETS.get(session.get("category", "general"), QUESTION_SETS["general"]))


class WhatsAppProductQuestionnaire:
    """Persists one active questionnaire per WhatsApp sender ID."""

    CANCEL_WORDS = {"cancel", "stop", "quit", "exit", "nevermind", "never mind"}

    def __init__(self, storage_path: str = ""):
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        self.storage_path = storage_path or os.path.join(backend_dir, "storage", "whatsapp_questionnaire_sessions.json")
        os.makedirs(os.path.dirname(os.path.abspath(self.storage_path)), exist_ok=True)
        self._lock = threading.RLock()
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self._sessions = data
        except FileNotFoundError:
            self._sessions = {}
        except (json.JSONDecodeError, OSError):
            self._sessions = {}

    def _save(self) -> None:
        temp_path = self.storage_path + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(self._sessions, f, ensure_ascii=False, indent=2)
        os.replace(temp_path, self.storage_path)

    def has_session(self, sender_id: str) -> bool:
        with self._lock:
            return sender_id in self._sessions

    def start(
        self,
        sender_id: str,
        product_name: str,
        llm_provider: Any = None,
    ) -> Dict[str, Any]:
        name = " ".join((product_name or "").split())[:120] or "unspecified product"
        category = classify_product(name)
        # The website and WhatsApp use the same validated Gemini questionnaire
        # generator, so any product can receive tailored follow-up questions.
        questions = _questions_from_schema(name, llm_provider)
        with self._lock:
            self._sessions[sender_id] = {
                "product_name": name,
                "category": category,
                "answers": {},
                "questions": questions,
                "questionnaire_source": "gemini_or_validated_fallback",
                "index": 0,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._save()
            return self._current_question(sender_id, intro=True)

    def handle_reply(self, sender_id: str, answer: str) -> Dict[str, Any]:
        normalized = " ".join((answer or "").split())
        if not normalized:
            return {"handled": False}
        with self._lock:
            session = self._sessions.get(sender_id)
            if not session:
                return {"handled": False}

            if normalized.casefold() in self.CANCEL_WORDS:
                self._sessions.pop(sender_id, None)
                self._save()
                return {
                    "handled": True,
                    "cancelled": True,
                    "message": "Product questions cancelled. You can send a product name whenever you want to try again.",
                }

            questions = _questions_for_session(session)
            index = int(session.get("index", 0))
            if index >= len(questions):
                self._sessions.pop(sender_id, None)
                self._save()
                return {"handled": False}

            question = questions[index]
            # List replies use the displayed title. Free-typed answers are accepted too.
            session["answers"][question["key"]] = normalized[:160]
            session["index"] = index + 1

            # Recalculate after the answer: a choice such as Insulated can add a
            # follow-up question, so do not compare against the old question count.
            next_questions = _questions_for_session(session)
            if session["index"] >= len(next_questions):
                completed = self._sessions.pop(sender_id)
                self._save()
                return {
                    "handled": True,
                    "complete": True,
                    "product_name": completed["product_name"],
                    "category": completed["category"],
                    "answers": completed["answers"],
                    "rag_query": self._to_rag_query(completed),
                    "message": "Thanks. I have the product details. I’ll now check official BIS references and the indexed knowledge base for relevant guidance.",
                }

            self._save()
            result = self._current_question(sender_id, intro=False)
            result["recorded_answer"] = normalized[:160]
            result["handled"] = True
            return result

    def _current_question(self, sender_id: str, intro: bool) -> Dict[str, Any]:
        session = self._sessions[sender_id]
        questions = _questions_for_session(session)
        idx = int(session["index"])
        q = questions[idx]
        lead = f"Let's collect a few details about *{session['product_name']}*." if intro else f"Recorded: *{session['answers'][questions[idx - 1]['key']]}*."
        # The list-opening button is the chooser title; keep it short and
        # question-specific so the user sees the question while selecting.
        list_title = q.get("list_title") or _default_list_title(q["key"])
        type_note = f"\n{q['help_text']}" if q.get("help_text") else ""
        if q.get("input_type") == "text" or not q.get("choices"):
            response_mode = "text"
            input_instruction = "Reply with your answer in a message."
        else:
            response_mode = "list"
            input_instruction = "Tap the list below to choose an answer."
        return {
            "handled": True,
            "complete": False,
            "message": f"{lead}\n\n*Question {idx + 1} of {len(questions)}*\n{q['prompt']}{type_note}\n\n{input_instruction} You can reply *cancel* to stop.",
            "question": q["prompt"],
            "list_title": list_title[:20],
            "input_type": response_mode,
            "question_number": idx + 1,
            "total_questions": len(questions),
            "options": list(q.get("choices", [])),
        }

    @staticmethod
    def _to_rag_query(session: Dict[str, Any]) -> str:
        """Build a user-facing regulatory query; response policy belongs in the RAG system prompt."""
        questions = _questions_for_session(session)
        labels = {q["key"]: q.get("label") or q.get("prompt", q["key"].replace("_", " ").title()) for q in questions}
        lines = [
            f"Please assess the BIS requirements for this exact product: {session.get('product_name', 'unspecified product')}.",
            "Product details supplied by the user:",
            f"- Product name: {session.get('product_name', 'unspecified product')}",
        ]
        for key, value in session.get("answers", {}).items():
            lines.append(f"- {labels.get(key, key.replace('_', ' ').title())}: {value}")

        lines.append(
            "Based on the product details, identify any potentially applicable Indian Standard and its current edition, "
            "whether a current Quality Control Order or other official order makes certification compulsory, "
            "and the relevant testing and certification process for the user's stated activity. "
            "Distinguish a children's toy from an adult hobby or collector model where that distinction matters. "
            "Explain which points are supported by the retrieved official sources and which still need confirmation."
        )
        return "\n".join(lines)


product_questionnaire = WhatsAppProductQuestionnaire()
