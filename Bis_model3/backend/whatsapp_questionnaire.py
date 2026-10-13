"""Stateful conversational product questionnaire for ISense WhatsApp.

This alternative uses normal WhatsApp interactive list messages and does not
require a published WhatsApp Flow. User answers are product context, never
regulatory evidence.
"""
import json
import os
import re
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from rag.product_questionnaire import build_questionnaire


# Legacy fallback retained only for sessions created before dynamic schemas were stored.
# New sessions use research-driven schemas built from BIS catalogue candidates and scope evidence.
QUESTION_SETS: Dict[str, List[Dict[str, Any]]] = {
    "general": [
        {"key": "product_type", "prompt": "What exact product type or model is this?", "choices": [], "input_type": "text"},
        {"key": "intended_use", "prompt": "What is the product designed to be used for?", "list_title": "Intended use?", "choices": ["Household / consumer", "Office / workplace", "School / institutional", "Children / toy", "Commercial / industrial", "Medical / specialist", "Other / not sure"], "input_type": "radio"},
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


def _questions_from_schema(
    product_name: str,
    llm_provider: Any = None,
    catalogue_candidates: Optional[List[Dict[str, Any]]] = None,
    scope_evidence: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Generate clarification fields from matching BIS candidates and indexed scope excerpts."""
    schema = build_questionnaire(
        product_name,
        llm_provider,
        catalogue_candidates=catalogue_candidates or [],
        scope_evidence=scope_evidence or [],
    )
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
                "prompt": "What kind of product, model or variant is this?",
                "list_title": "Product type?",
                "choices": [],
                "input_type": "text",
                "help_text": "Describe its design and function in everyday terms.",
            },
            {
                "key": "intended_use",
                "prompt": "What is the product designed to be used for?",
                "list_title": "Intended use?",
                "choices": ["Household / consumer", "Office / workplace", "School / institutional", "Children / toy", "Commercial / industrial", "Medical / specialist", "Other / not sure"],
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
        # Runtime dependencies cannot be JSON-serialized. Keep them outside the
        # persisted conversation data; after a process restart, a pending interview
        # safely falls back to ordinary stored questions.
        self._runtime: Dict[str, Dict[str, Any]] = {}
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
        catalogue: Any = None,
        scope_evidence: Optional[List[Any]] = None,
        rag_engine: Any = None,
    ) -> Dict[str, Any]:
        name = " ".join((product_name or "").split())[:120] or "unspecified product"
        category = classify_product(name)

        # Research first, ask second: collect candidate standards by the entered
        # product name and scope excerpts from the existing regulatory index.
        catalogue_candidates: List[Dict[str, Any]] = []
        if catalogue is not None:
            try:
                catalogue_candidates = catalogue.search(name, top_k=8)
            except Exception:
                catalogue_candidates = []

        evidence_rows: List[Dict[str, Any]] = []
        for chunk in (scope_evidence or [])[:6]:
            evidence_rows.append({
                "standard_code": getattr(chunk, "standard_code", ""),
                "standard_title": getattr(chunk, "standard_title", ""),
                "clause": getattr(chunk, "clause", ""),
                "text": getattr(chunk, "content", ""),
                "source_url": getattr(chunk, "source_url", ""),
                "verification_status": getattr(chunk, "verification_status", ""),
            })

        # Generate the initial field using the same evidence-aware question selector
        # used after every answer. This ensures the first user message also asks one
        # concrete clarification rather than showing a fixed multi-field form.
        adaptive_interview = bool(llm_provider is not None and type(llm_provider).__name__ != "UnavailableLLMProvider")
        if adaptive_interview:
            questions = self._questions_from_first_turn(
                name,
                llm_provider,
                catalogue_candidates=catalogue_candidates,
                scope_evidence=evidence_rows,
            )
        else:
            questions = _questions_from_schema(
                name,
                llm_provider,
                catalogue_candidates=catalogue_candidates,
                scope_evidence=evidence_rows,
            )
        with self._lock:
            self._sessions[sender_id] = {
                "product_name": name,
                "category": category,
                "answers": {},
                "questions": questions,
                "catalogue_candidates": catalogue_candidates,
                "questionnaire_source": "adaptive_candidate_aware" if adaptive_interview else "compact_fallback",
                "adaptive_interview": adaptive_interview,
                "asked_questions": [],
                "index": 0,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            if adaptive_interview:
                self._runtime[sender_id] = {
                    "llm_provider": llm_provider,
                    "catalogue": catalogue,
                    "rag_engine": rag_engine,
                }
            else:
                self._runtime.pop(sender_id, None)
            self._save()
            return self._current_question(sender_id, intro=True)

    def _questions_from_first_turn(
        self,
        product_name: str,
        llm_provider: Any,
        catalogue_candidates: List[Dict[str, Any]],
        scope_evidence: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Turn initial retrieval into one plain-language clarification question."""
        schema = build_questionnaire(
            product_name,
            llm_provider,
            catalogue_candidates=catalogue_candidates,
            scope_evidence=scope_evidence,
        )
        fields = schema.get("fields", [])
        if not fields:
            return _questions_from_schema(product_name, llm_provider, catalogue_candidates, scope_evidence)[:1]
        field = fields[0]
        field_id = str(field.get("id") or "product_subtype").strip()[:40]
        label = str(field.get("label") or f"What kind of {product_name} is it?").strip()[:180]
        kind = str(field.get("type") or "text").lower()
        options = field.get("options", [])
        if kind == "radio" and isinstance(options, list) and len(options) >= 2:
            choices = [str(v).strip()[:100] for v in options if str(v).strip()][:6]
        else:
            kind, choices = "text", []
        return [{
            "key": field_id,
            "prompt": label,
            "list_title": _short_picker_title(field_id, label),
            "choices": choices,
            "input_type": kind,
            "help_text": str(field.get("helpText") or "")[:240],
        }]

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
                self._runtime.pop(sender_id, None)
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
            session.setdefault("answers", {})[question["key"]] = normalized[:160]
            session["index"] = index + 1
            session.setdefault("asked_questions", []).append(question["key"])

            if session.get("adaptive_interview"):
                next_question = self._generate_next_question(sender_id, session)
                if next_question is None:
                    completed = self._sessions.pop(sender_id)
                    self._runtime.pop(sender_id, None)
                    self._save()
                    return {
                        "handled": True,
                        "complete": True,
                        "product_name": completed["product_name"],
                        "category": completed["category"],
                        "answers": completed["answers"],
                        "rag_query": self._to_rag_query(completed),
                        "message": "Thanks. I have enough product details to compare the relevant BIS sources. I’ll now check the evidence and prepare your guidance.",
                    }
                session["questions"] = [next_question]
                session["index"] = 0
                self._save()
                result = self._current_question(sender_id, intro=False)
                result["recorded_answer"] = normalized[:160]
                result["handled"] = True
                result["question_number"] = len(session["asked_questions"]) + 1
                result["total_questions"] = "adaptive"
                return result

            if session["index"] >= len(questions):
                completed = self._sessions.pop(sender_id)
                self._runtime.pop(sender_id, None)
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

    def _generate_next_question(self, sender_id: str, session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Re-query BIS evidence and generate at most one useful next question."""
        max_questions = 5
        asked = set(session.get("asked_questions", []))
        if len(asked) >= max_questions:
            return None

        product = session.get("product_name", "product")
        answers = session.get("answers", {})
        answer_context = "\n".join(
            f"- {key.replace('_', ' ')}: {value}" for key, value in answers.items()
        )
        retrieval_query = (
            f"{product} product scope intended use design construction exclusions "
            f"Indian Standard Quality Control Order\n{answer_context}"
        )

        runtime = self._runtime.get(sender_id, {})
        engine = runtime.get("rag_engine")
        catalogue = runtime.get("catalogue")
        candidates = list(session.get("catalogue_candidates", []))
        evidence_rows: List[Dict[str, Any]] = []
        if engine is not None:
            try:
                retrieved = engine.retrieve(retrieval_query, top_k=8)
            except Exception:
                retrieved = []
            for chunk in retrieved[:8]:
                evidence_rows.append({
                    "standard_code": getattr(chunk, "standard_code", ""),
                    "standard_title": getattr(chunk, "standard_title", ""),
                    "clause": getattr(chunk, "clause", ""),
                    "text": getattr(chunk, "content", ""),
                    "source_url": getattr(chunk, "source_url", ""),
                    "verification_status": getattr(chunk, "verification_status", ""),
                })
        if catalogue is not None:
            try:
                candidates = catalogue.search(product + "\n" + answer_context, top_k=8)
                session["catalogue_candidates"] = candidates
            except Exception:
                pass

        provider = runtime.get("llm_provider")
        if provider is None:
            return None

        prompt = (
            "Choose exactly one next clarification question for a BIS product-scope interview. "
            "Candidate standard titles are search hints; retrieved official scope excerpts are evidence. "
            "Ask only for a fact that would materially distinguish remaining candidate scopes or resolve a meaningful uncertainty. "
            "Do not repeat a prior field. Do not ask for the standard number, manufacturing origin, business activity, capacity, dimensions, "
            "or voltage unless supplied official evidence makes the detail relevant. "
            "If no additional clarification is needed, return a JSON object with done=true. "
            "Otherwise return JSON with done=false and a field object containing id, label, type, options, required, and helpText. "
            "The field type must be radio or text. For radio, use 2–6 plain-language answers and include Not sure. "
            "Return JSON only. Never claim that a standard applies or certification is mandatory.\n\n"
            f"PRODUCT: {product}\nANSWERS SO FAR:\n{answer_context}\n"
            f"CATALOGUE CANDIDATES (metadata only): {json.dumps(candidates[:8], ensure_ascii=False)[:5000]}\n"
            f"OFFICIAL SCOPE EXCERPTS: {json.dumps(evidence_rows[:8], ensure_ascii=False)[:9000]}\n"
            f"ALREADY ASKED: {sorted(asked)}"
        )
        try:
            result = provider.generate(
                query=prompt,
                system_instruction=(
                    "Return only a JSON decision for the next clarification question. "
                    "Questions must be grounded in current user answers and supplied BIS evidence. "
                    "Never determine legal applicability from catalogue title alone."
                ),
                retrieved_chunks=[],
                application_context={
                    "task": "adaptive_bis_product_interview",
                    "product": product,
                    "answers": answers,
                },
            )
            if not getattr(result, "is_success", False):
                return None
            raw = str(getattr(result, "text", "") or "").strip()
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE)
            left, right = raw.find("{"), raw.rfind("}")
            if left < 0 or right <= left:
                return None
            decision = json.loads(raw[left:right + 1])
            if decision.get("done") is True:
                return None
            field = decision.get("field")
            if not isinstance(field, dict):
                return None
            field_id = re.sub(r"[^a-zA-Z0-9_]+", "_", str(field.get("id", ""))).strip("_").lower()[:40]
            label = " ".join(str(field.get("label", "")).split())[:180]
            if not field_id or not label or field_id in asked:
                return None

            kind = str(field.get("type", "text")).lower()
            options = field.get("options", [])
            if kind == "radio" and isinstance(options, list):
                options = list(dict.fromkeys(" ".join(str(v).split())[:100] for v in options if str(v).strip()))[:6]
                if len(options) < 2:
                    kind, options = "text", []
            else:
                kind, options = "text", []

            return {
                "key": field_id,
                "prompt": label,
                "list_title": _short_picker_title(field_id, label),
                "choices": options,
                "input_type": kind,
                "help_text": " ".join(str(field.get("helpText", "")).split())[:240],
            }
        except Exception:
            return None

    def _current_question(self, sender_id: str, intro: bool) -> Dict[str, Any]:
        session = self._sessions[sender_id]
        questions = _questions_for_session(session)
        idx = int(session["index"])
        q = questions[idx]
        adaptive = bool(session.get("adaptive_interview"))
        if intro:
            lead = f"I checked the BIS catalogue and available scope records for *{session['product_name']}*."
        elif adaptive:
            previous_key = session.get("asked_questions", [""])[-1]
            previous_value = session.get("answers", {}).get(previous_key, "")
            lead = f"Recorded: *{previous_value}*. I’m narrowing the product scope using that detail."
        else:
            lead = f"Recorded: *{session['answers'][questions[idx - 1]['key']]}*."
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
        labels = {q["key"]: q.get("label") or q.get("prompt") or q["key"].replace("_", " ").title() for q in questions}
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
            "Explain which points are supported by retrieved official sources and which still need confirmation."
        )

        # Only append an adult-model scope note when the user's actual answers say so.
        # Do not put that phrase into every RC-car query, or it can bias the classifier.
        answer_text = " ".join(str(value) for value in session.get("answers", {}).values()).casefold()
        if session.get("category") == "rc_car" and any(
            term in answer_text for term in (
                "age 14+", "hobby use", "adult hobby", "adult collector",
                "model / hobby vehicle", "model/hobby vehicle", "scale model"
            )
        ):
            lines.append(
                "The user's answers describe an adult hobby/collector model. Check this product-scope distinction carefully; "
                "do not automatically apply children's-toy standards or the toy QCO."
            )
        candidates = session.get("catalogue_candidates", [])
        if candidates:
            lines.append("Initial BIS catalogue candidates (number/title metadata only; re-check scope and current status):")
            for item in candidates[:8]:
                lines.append(f"- {item.get('is_number')}: {item.get('title')}")
        lines.append(
            "Treat the candidate list as search hints only. Re-check all likely standards against detailed scope documents and current QCO/order evidence. "
            "Do not assume a candidate applies only because its title is similar."
        )
        return "\n".join(lines)


product_questionnaire = WhatsAppProductQuestionnaire()
