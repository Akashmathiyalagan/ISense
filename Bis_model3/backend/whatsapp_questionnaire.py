"""Stateful conversational product questionnaire for ISense WhatsApp.

This alternative uses normal WhatsApp interactive list messages and does not
require a published WhatsApp Flow. User answers are product context, never
regulatory evidence.
"""
import json
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List


QUESTION_SETS: Dict[str, List[Dict[str, Any]]] = {
    "water_bottle": [
        {"key": "material", "prompt": "What is the main material?", "choices": ["Stainless steel", "Plastic", "Glass", "Aluminium", "Other / not sure"]},
        {"key": "capacity", "prompt": "What is its capacity?", "choices": ["250 ml or less", "251–750 ml", "751 ml–1 litre", "Above 1 litre", "Not sure"]},
        {"key": "insulation", "prompt": "Is it insulated?", "choices": ["Insulated", "Non-insulated", "Not sure"]},
        {"key": "business_activity", "prompt": "What best describes your activity?", "choices": ["Personal use", "Manufacture in India", "Sell in India", "Import into India"]},
        {"key": "origin", "prompt": "Where is it manufactured?", "choices": ["Made in India", "Imported", "Not sure"]},
        {"key": "help_needed", "prompt": "What BIS guidance do you need?", "choices": ["Applicable IS standard", "Certification / registration", "Testing requirements", "Marking / labelling", "All of these"]},
    ],
    "backpack": [
        {"key": "bag_type", "prompt": "What kind of bag is it?", "choices": ["School backpack", "Laptop backpack", "Travel backpack", "Trekking backpack", "Other / not sure"]},
        {"key": "material", "prompt": "What is the main material?", "choices": ["Textile / fabric", "Leather", "Synthetic / plastic", "Mixed materials", "Other / not sure"]},
        {"key": "intended_user", "prompt": "Who is it mainly designed for?", "choices": ["Children / school use", "Adults", "All ages", "Not sure"]},
        {"key": "business_activity", "prompt": "What best describes your activity?", "choices": ["Personal use", "Manufacture in India", "Sell in India", "Import into India"]},
        {"key": "origin", "prompt": "Where is it manufactured?", "choices": ["Made in India", "Imported", "Not sure"]},
        {"key": "help_needed", "prompt": "What BIS guidance do you need?", "choices": ["Applicable IS standard", "Certification / registration", "Testing requirements", "Marking / labelling", "All of these"]},
    ],
    "rc_car": [
        {"key": "vehicle_type", "prompt": "What type of RC car is it?", "choices": ["Toy RC car", "Hobby / model vehicle", "Other / not sure"]},
        {"key": "power_source", "prompt": "How is it powered?", "choices": ["Rechargeable battery", "Replaceable batteries", "No battery / other", "Not sure"]},
        {"key": "intended_age", "prompt": "Who is it intended for?", "choices": ["Under 3 years", "3 to 8 years", "Above 8 years", "Adult hobby use", "Not sure"]},
        {"key": "material", "prompt": "What is the main body material?", "choices": ["Plastic", "Metal", "Mixed materials", "Not sure"]},
        {"key": "origin", "prompt": "Where is it manufactured?", "choices": ["Made in India", "Imported", "Not sure"]},
        {"key": "help_needed", "prompt": "What BIS guidance do you need?", "choices": ["Applicable IS standard", "Certification / registration", "Toy safety / testing", "Marking / labelling", "All of these"]},
    ],
    "general": [
        {"key": "product_type", "prompt": "Which product type describes it best?", "choices": ["Electrical / electronic", "Household product", "Toy / children's product", "Food-contact product", "Textile / bag", "Other / not sure"]},
        {"key": "material", "prompt": "What is its main material?", "choices": ["Metal", "Plastic", "Textile / fabric", "Glass / ceramic", "Mixed materials", "Other / not sure"]},
        {"key": "business_activity", "prompt": "What best describes your activity?", "choices": ["Personal use", "Manufacture in India", "Sell in India", "Import into India"]},
        {"key": "origin", "prompt": "Where is it manufactured?", "choices": ["Made in India", "Imported", "Not sure"]},
        {"key": "help_needed", "prompt": "What BIS guidance do you need?", "choices": ["Applicable IS standard", "Certification / registration", "Testing requirements", "Marking / labelling", "All of these"]},
    ],
}


def classify_product(product_name: str) -> str:
    """Map common product descriptions to predefined product question sets."""
    text = " ".join((product_name or "").lower().split())
    if any(term in text for term in ("water bottle", "bottle", "flask", "thermos", "tumbler")):
        return "water_bottle"
    if any(term in text for term in ("backpack", "back pack", "back bag", "school bag", "rucksack", "bag")):
        return "backpack"
    if any(term in text for term in ("rc car", "remote control car", "toy car", "toy vehicle")):
        return "rc_car"
    return "general"


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

    def start(self, sender_id: str, product_name: str) -> Dict[str, Any]:
        name = " ".join((product_name or "").split())[:120] or "unspecified product"
        category = classify_product(name)
        with self._lock:
            self._sessions[sender_id] = {
                "product_name": name,
                "category": category,
                "answers": {},
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

            questions = QUESTION_SETS.get(session.get("category", "general"), QUESTION_SETS["general"])
            index = int(session.get("index", 0))
            if index >= len(questions):
                self._sessions.pop(sender_id, None)
                self._save()
                return {"handled": False}

            question = questions[index]
            # List replies use the displayed title. Free-typed answers are accepted too.
            session["answers"][question["key"]] = normalized[:160]
            session["index"] = index + 1

            if session["index"] >= len(questions):
                completed = self._sessions.pop(sender_id)
                self._save()
                return {
                    "handled": True,
                    "complete": True,
                    "product_name": completed["product_name"],
                    "category": completed["category"],
                    "answers": completed["answers"],
                    "rag_query": self._to_rag_query(completed),
                    "message": "Thanks. I have the product details. I’ll now check the indexed BIS sources for relevant guidance.",
                }

            self._save()
            result = self._current_question(sender_id, intro=False)
            result["recorded_answer"] = normalized[:160]
            result["handled"] = True
            return result

    def _current_question(self, sender_id: str, intro: bool) -> Dict[str, Any]:
        session = self._sessions[sender_id]
        questions = QUESTION_SETS[session["category"]]
        idx = int(session["index"])
        q = questions[idx]
        lead = f"Let's collect a few details about *{session['product_name']}*." if intro else f"Recorded: *{session['answers'][questions[idx - 1]['key']]}*."
        return {
            "handled": True,
            "complete": False,
            "message": f"{lead}\n\n*Question {idx + 1} of {len(questions)}*\n{q['prompt']}\n\nYou can type an answer instead, or reply *cancel* to stop.",
            "question": q["prompt"],
            "question_number": idx + 1,
            "total_questions": len(questions),
            "options": list(q["choices"]),
        }

    @staticmethod
    def _to_rag_query(session: Dict[str, Any]) -> str:
        questions = QUESTION_SETS.get(session.get("category", "general"), QUESTION_SETS["general"])
        labels = {q["key"]: q["prompt"].rstrip("?") for q in questions}
        lines = [
            "The user is seeking BIS guidance. The following are user-provided product details, not regulatory evidence.",
            f"Product name: {session.get('product_name', 'unspecified')}",
            f"Product category detected for questionnaire routing: {session.get('category', 'general')}",
        ]
        for key, value in session.get("answers", {}).items():
            lines.append(f"{labels.get(key, key)}: {value}")
        lines.append(
            "Use only retrieved evidence to state any potentially applicable Indian Standard, Quality Control Order, "
            "certification, testing, or marking requirement. Do not infer legal applicability from the user answers alone. "
            "If the indexed official evidence is insufficient, say so and recommend checking current official BIS sources."
        )
        return "\n".join(lines)


product_questionnaire = WhatsAppProductQuestionnaire()
