import os
import re
import json
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from threading import Lock

from rag.models import KnowledgeChunk
from rag.standard_detector import detect_bis_standard_structured, KNOWN_BIS_STANDARDS_CATALOG

logger = logging.getLogger("isense_conversation")

# Recognized regulatory intents
INTENT_PRODUCT_APPLICABILITY = "product_standard_applicability"
INTENT_DOCUMENT_CHECKLIST = "document_checklist"
INTENT_APPLICATION_PROCEDURE = "application_procedure"
INTENT_TESTING_REQUIREMENTS = "testing_requirements"
INTENT_FEES_TIMELINES = "fees_and_timelines"
INTENT_SCHEME_REQUIREMENTS = "scheme_requirements"
INTENT_QCO_APPLICABILITY = "qco_applicability"
INTENT_LICENCE_RENEWAL = "licence_renewal"
INTENT_MARKING_LABELLING = "marking_and_labelling"
INTENT_GENERAL_INQUIRY = "general_bis_inquiry"
INTENT_GREETING = "greeting"
INTENT_FAREWELL = "farewell"
INTENT_THANKS = "thanks"
INTENT_CLARIFICATION = "clarification"

ALL_INTENTS = [
    INTENT_PRODUCT_APPLICABILITY,
    INTENT_DOCUMENT_CHECKLIST,
    INTENT_APPLICATION_PROCEDURE,
    INTENT_TESTING_REQUIREMENTS,
    INTENT_FEES_TIMELINES,
    INTENT_SCHEME_REQUIREMENTS,
    INTENT_QCO_APPLICABILITY,
    INTENT_LICENCE_RENEWAL,
    INTENT_MARKING_LABELLING,
    INTENT_GENERAL_INQUIRY,
    INTENT_GREETING,
    INTENT_FAREWELL,
    INTENT_THANKS,
    INTENT_CLARIFICATION,
]

STATUTORY_DISCLAIMER_SUFFIX = (
    "\n\n*Statutory Boundary Notice: ISense is an independent compliance assistance platform. "
    "Official licenses and ISI mark certifications are granted exclusively by the Bureau of Indian Standards (BIS). "
    "Official filings must be made via the BIS Manak Online portal.*"
)

GREETING_WORDS = {
    "hi", "hello", "hey", "greetings", "good morning", "good afternoon",
    "good evening", "howdy", "namaste", "hola", "hi there", "hello there", "hey there",
    "start", "menu"
}

FAREWELL_WORDS = {
    "bye", "goodbye", "bye bye", "see you", "see ya", "talk to you later",
    "cya", "take care", "good night", "have a good day", "farewell"
}

THANKS_WORDS = {
    "thanks", "thank you", "thx", "thanks a lot", "thank you so much",
    "many thanks", "appreciate it", "thank u", "ty"
}

def is_greeting(text: str) -> bool:
    if not text:
        return False
    clean = text.lower().strip()
    clean_no_punct = re.sub(r'[^\w\s]', '', clean).strip()
    if clean_no_punct in GREETING_WORDS:
        return True
    words = clean_no_punct.split()
    if 1 <= len(words) <= 3:
        if words[0] in {"hi", "hello", "hey", "namaste", "greetings", "howdy", "hola"}:
            non_greeting = set(words) - {"hi", "hello", "hey", "namaste", "greetings", "howdy", "hola", "there", "isense", "assistant", "bot"}
            if not non_greeting:
                return True
        if len(words) >= 2 and words[0] == "good" and words[1] in {"morning", "afternoon", "evening", "day"}:
            return True
    return False

def is_farewell(text: str) -> bool:
    if not text:
        return False
    clean = text.lower().strip()
    clean_no_punct = re.sub(r'[^\w\s]', '', clean).strip()
    if clean_no_punct in FAREWELL_WORDS:
        return True
    words = clean_no_punct.split()
    if 1 <= len(words) <= 3:
        if words[0] in {"bye", "goodbye", "cya", "farewell"}:
            return True
        if len(words) >= 2 and words[0] == "see" and words[1] in {"you", "ya"}:
            return True
        if len(words) >= 2 and words[0] == "take" and words[1] == "care":
            return True
    return False

def is_thanks(text: str) -> bool:
    if not text:
        return False
    clean = text.lower().strip()
    clean_no_punct = re.sub(r'[^\w\s]', '', clean).strip()
    if clean_no_punct in THANKS_WORDS:
        return True
    words = clean_no_punct.split()
    if 1 <= len(words) <= 4:
        if any(w in words for w in ["thank", "thanks", "thx", "appreciate"]):
            if not any(w in words for w in ["standard", "test", "tests", "doc", "document", "documents", "fee", "fees", "cost", "is", "qco"]):
                return True
    return False


class ConversationState:
    """Represents the structured multi-turn conversation state."""

    def __init__(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
        channel: str = "web",
        current_intent: str = INTENT_GENERAL_INQUIRY,
        product_name: Optional[str] = None,
        product_category: Optional[str] = None,
        product_attributes: Optional[Dict[str, Any]] = None,
        manufacturing_country: Optional[str] = None,
        import_status: Optional[str] = None,
        manufacturer_details: Optional[str] = None,
        applicant_details: Optional[str] = None,
        candidate_standard: Optional[str] = None,
        candidate_standards: Optional[List[str]] = None,
        candidate_title: Optional[str] = None,
        certification_scheme: Optional[str] = None,
        current_clarification_question: Optional[str] = None,
        pending_clarification_type: Optional[str] = None,
        collected_answers: Optional[Dict[str, Any]] = None,
        conversation_status: str = "active",
        state_version: int = 1,
        turns: Optional[List[Dict[str, Any]]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        now = datetime.now(timezone.utc).isoformat()
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.channel = channel
        self.current_intent = current_intent
        self.product_name = product_name
        self.product_category = product_category
        self.product_attributes = product_attributes if product_attributes is not None else {}
        self.manufacturing_country = manufacturing_country
        self.import_status = import_status
        self.manufacturer_details = manufacturer_details
        self.applicant_details = applicant_details
        self.candidate_standard = candidate_standard
        if candidate_standards is not None:
            self.candidate_standards = candidate_standards
        elif candidate_standard:
            self.candidate_standards = [candidate_standard]
        else:
            self.candidate_standards = []
        self.candidate_title = candidate_title
        self.certification_scheme = certification_scheme
        self.current_clarification_question = current_clarification_question
        self.pending_clarification_type = pending_clarification_type
        self.collected_answers = collected_answers if collected_answers is not None else {}
        self.conversation_status = conversation_status
        self.state_version = state_version
        self.turns = turns if turns is not None else []
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    @property
    def current_product(self) -> Optional[str]:
        return self.product_name

    @current_product.setter
    def current_product(self, value: Optional[str]):
        self.product_name = value

    @property
    def pending_clarification(self) -> Optional[str]:
        return self.pending_clarification_type

    @pending_clarification.setter
    def pending_clarification(self, value: Optional[str]):
        self.pending_clarification_type = value

    @property
    def previous_answers(self) -> Dict[str, Any]:
        return self.collected_answers

    @previous_answers.setter
    def previous_answers(self, value: Dict[str, Any]):
        self.collected_answers = value

    def switch_product(
        self,
        new_product: str,
        catalog_entry: Optional[Dict[str, Any]] = None,
        candidate_standard: Optional[str] = None
    ):
        """Cleanly switches product context and clears old product standards, evidence, and answers."""
        cleaned = new_product.strip().lower()
        logger.info(f"Context Product Switch: '{self.product_name}' -> '{cleaned}' (Conversation: {self.conversation_id})")
        self.product_name = cleaned
        if catalog_entry:
            self.candidate_standard = catalog_entry["standard_code"]
            self.candidate_standards = [catalog_entry["standard_code"]]
            self.candidate_title = catalog_entry.get("standard_title")
            self.product_category = catalog_entry.get("category")
            self.certification_scheme = catalog_entry.get("scheme")
        elif candidate_standard:
            self.candidate_standard = candidate_standard
            self.candidate_standards = [candidate_standard]
            self.candidate_title = None
            self.product_category = None
            self.certification_scheme = None
        else:
            self.candidate_standard = None
            self.candidate_standards = []
            self.candidate_title = None
            self.product_category = None
            self.certification_scheme = None

        self.product_attributes = {}
        self.pending_clarification_type = None
        self.current_clarification_question = None
        self.conversation_status = "active"
        self.collected_answers = {}
        self.state_version += 1
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def add_turn(self, role: str, content: str, intent: Optional[str] = None):
        self.turns.append({
            "id": f"trn-{uuid.uuid4().hex[:6]}",
            "role": role,
            "content": content,
            "intent": intent or self.current_intent,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self.state_version += 1
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "channel": self.channel,
            "current_intent": self.current_intent,
            "product_name": self.product_name,
            "current_product": self.product_name,
            "product_category": self.product_category,
            "product_attributes": self.product_attributes,
            "manufacturing_country": self.manufacturing_country,
            "import_status": self.import_status,
            "manufacturer_details": self.manufacturer_details,
            "applicant_details": self.applicant_details,
            "candidate_standard": self.candidate_standard,
            "candidate_standards": self.candidate_standards,
            "candidate_title": self.candidate_title,
            "certification_scheme": self.certification_scheme,
            "current_clarification_question": self.current_clarification_question,
            "pending_clarification_type": self.pending_clarification_type,
            "pending_clarification": self.pending_clarification_type,
            "collected_answers": self.collected_answers,
            "previous_answers": self.collected_answers,
            "conversation_status": self.conversation_status,
            "state_version": self.state_version,
            "turns": self.turns,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationState":
        return cls(
            conversation_id=data.get("conversation_id", f"conv-{uuid.uuid4().hex[:8]}"),
            user_id=data.get("user_id"),
            channel=data.get("channel", "web"),
            current_intent=data.get("current_intent", INTENT_GENERAL_INQUIRY),
            product_name=data.get("product_name") or data.get("current_product"),
            product_category=data.get("product_category"),
            product_attributes=data.get("product_attributes", {}),
            manufacturing_country=data.get("manufacturing_country"),
            import_status=data.get("import_status"),
            manufacturer_details=data.get("manufacturer_details"),
            applicant_details=data.get("applicant_details"),
            candidate_standard=data.get("candidate_standard"),
            candidate_standards=data.get("candidate_standards", []),
            candidate_title=data.get("candidate_title"),
            certification_scheme=data.get("certification_scheme"),
            current_clarification_question=data.get("current_clarification_question"),
            pending_clarification_type=data.get("pending_clarification_type") or data.get("pending_clarification"),
            collected_answers=data.get("collected_answers") or data.get("previous_answers", {}),
            conversation_status=data.get("conversation_status", "active"),
            state_version=data.get("state_version", 1),
            turns=data.get("turns", []),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


class ConversationStore:
    """Thread-safe persistent session store with disk caching and TTL cleanup."""

    def __init__(self, storage_dir: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.storage_dir = storage_dir or os.path.join(base_dir, "storage")
        os.makedirs(self.storage_dir, exist_ok=True)
        self.file_path = os.path.join(self.storage_dir, "conversations.json")
        self._lock = Lock()
        self._cache: Dict[str, ConversationState] = {}
        self._load()

    def _load(self):
        with self._lock:
            if os.path.exists(self.file_path):
                try:
                    with open(self.file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for cid, cdata in data.items():
                            self._cache[cid] = ConversationState.from_dict(cdata)
                except Exception as e:
                    logger.warning(f"Could not load conversations from {self.file_path}: {e}")

    def _save(self):
        with self._lock:
            try:
                serializable = {cid: state.to_dict() for cid, state in self._cache.items()}
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump(serializable, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to persist conversations to {self.file_path}: {e}")

    def get(self, conversation_id: str) -> Optional[ConversationState]:
        with self._lock:
            return self._cache.get(conversation_id)

    def get_or_create(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
        channel: str = "web"
    ) -> ConversationState:
        with self._lock:
            state = self._cache.get(conversation_id)
            if state is None:
                state = ConversationState(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    channel=channel
                )
                self._cache[conversation_id] = state
            else:
                if user_id and not state.user_id:
                    state.user_id = user_id
            return state

    def save(self, state: ConversationState):
        state.updated_at = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._cache[state.conversation_id] = state
        self._save()

    def delete(self, conversation_id: str) -> bool:
        removed = False
        with self._lock:
            if conversation_id in self._cache:
                del self._cache[conversation_id]
                removed = True
        if removed:
            self._save()
        return removed

    def cleanup_expired(self, ttl_seconds: int = 172800) -> int:
        """Removes conversations inactive for longer than TTL (default 48h)."""
        now = datetime.now(timezone.utc)
        removed_count = 0
        with self._lock:
            to_delete = []
            for cid, state in self._cache.items():
                try:
                    updated = datetime.fromisoformat(state.updated_at)
                    if (now - updated).total_seconds() > ttl_seconds:
                        to_delete.append(cid)
                except Exception:
                    pass
            for cid in to_delete:
                del self._cache[cid]
                removed_count += 1
        if removed_count > 0:
            self._save()
            logger.info(f"Cleaned up {removed_count} expired conversation(s).")
        return removed_count


# ==============================================================================
# Intent Classifier
# ==============================================================================

def classify_intent(query: str, state: Optional[ConversationState] = None) -> str:
    """
    Distinguishes the 10 core regulatory intents, plus greetings, farewells, thanks, and clarifications.
    Preserves existing multi-turn intent if user is answering a pending clarification.
    """
    q_lower = (query or "").strip().lower()

    # Routing before regulatory retrieval: Greeting, Farewell, Thanks
    if is_greeting(query):
        return INTENT_GREETING
    if is_farewell(query):
        return INTENT_FAREWELL
    if is_thanks(query):
        return INTENT_THANKS

    # If currently waiting for user clarification on an active journey
    if state and state.conversation_status == "awaiting_clarification" and state.pending_clarification_type:
        if state.current_intent in [INTENT_DOCUMENT_CHECKLIST, INTENT_APPLICATION_PROCEDURE, INTENT_PRODUCT_APPLICABILITY]:
            return state.current_intent

    # 1. Document Checklist
    doc_patterns = [
        "document", "documents", "doc checklist", "checklist", "papers needed",
        "paperwork", "form-v", "form-1", "form 1", "form v", "documents required",
        "documents needed", "what do i need to submit", "what documents"
    ]
    if any(p in q_lower for p in doc_patterns) and not any(p in q_lower for p in ["fee", "cost", "renewal"]):
        return INTENT_DOCUMENT_CHECKLIST

    # 2. Application Procedure
    proc_patterns = [
        "application procedure", "how to apply", "application process", "steps to get",
        "how do i register", "registration process", "manak online registration",
        "step by step", "procedure for bis", "how to get bis", "filing process"
    ]
    if any(p in q_lower for p in proc_patterns):
        return INTENT_APPLICATION_PROCEDURE

    # 3. Testing Requirements
    testing_patterns = [
        "test requirements", "testing requirements", "what tests", "laboratory test",
        "test clause", "testing clause", "insulation resistance", "cap torque",
        "flammability test", "mechanical abuse", "drop test", "dielectric",
        "anti-islanding", "air delivery", "creepage distance"
    ]
    if any(p in q_lower for p in testing_patterns) or ("test" in q_lower and "standard" not in q_lower and "fee" not in q_lower):
        return INTENT_TESTING_REQUIREMENTS

    # 4. Fees and Timelines
    fee_patterns = [
        "fee", "fees", "cost", "how much", "charges", "statutory fee", "marking fee",
        "processing fee", "inspection fee", "timeline", "processing time", "how long",
        "turnaround time", "schedule 1", "schedule 2"
    ]
    if any(p in q_lower for p in fee_patterns):
        return INTENT_FEES_TIMELINES

    # 5. ISI Mark and CRS Requirements (Scheme requirements)
    scheme_patterns = [
        "scheme i", "scheme ii", "difference between isi and crs", "crs vs isi",
        "compulsory registration scheme", "product certification scheme", "fmcs",
        "which scheme", "foreign manufacturers certification"
    ]
    if any(p in q_lower for p in scheme_patterns):
        return INTENT_SCHEME_REQUIREMENTS

    # 6. QCO Applicability
    qco_patterns = [
        "qco", "quality control order", "is it mandatory", "mandatory certification",
        "compulsory certification", "gazette notification", "enforcement date"
    ]
    if any(p in q_lower for p in qco_patterns):
        return INTENT_QCO_APPLICABILITY

    # 7. Licence Renewal
    renewal_patterns = [
        "renew", "renewal", "extend license", "validity period", "expired license",
        "license validity", "cml renewal", "r-number renewal"
    ]
    if any(p in q_lower for p in renewal_patterns):
        return INTENT_LICENCE_RENEWAL

    # 8. Marking and Labelling
    marking_patterns = [
        "marking", "label", "labeling", "labelling", "logo size", "isi mark placement",
        "r-number display", "standard mark display", "packaging requirements"
    ]
    if any(p in q_lower for p in marking_patterns):
        return INTENT_MARKING_LABELLING

    # 9. Product-Standard Applicability
    applicability_patterns = [
        "what standard applies", "which standard applies", "standard for",
        "applicable standard", "standard applies to", "indian standard for",
        "is 16102", "is 9873", "is 4151", "is 374", "is 16046", "is 13252"
    ]
    if any(p in q_lower for p in applicability_patterns):
        return INTENT_PRODUCT_APPLICABILITY

    # Check for direct product inquiry that implies applicability
    product, _ = extract_product_entity(query)
    if product:
        return INTENT_PRODUCT_APPLICABILITY

    # 10. General BIS questions
    return INTENT_GENERAL_INQUIRY


# ==============================================================================
# Entity Extraction
# ==============================================================================

def extract_product_entity(query: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Detects product name and matching catalog standard.
    Supports arbitrary uncatalogued commodities (e.g. 'back bag', 'backpack', 'water bottle')
    as well as catalogued products and explicit transition phrases.
    """
    q_lower = (query or "").lower().strip()
    if not q_lower:
        return None, None

    GENERIC_PRODUCT_STOPWORDS = {
        "product", "products", "my product", "the product", "a product",
        "this product", "our product", "any product", "item", "items", "goods",
        "all", "all the documents", "documents", "certification", "license",
        "standard", "standards", "compliance", "process", "procedure"
    }

    # 1. Explicit declaration / switch / inquiry patterns
    transition_patterns = [
        r"(?:now\s+tell\s+me\s+about|tell\s+me\s+about|what\s+about|how\s+about|switch\s+to|what\s+for)\s+(?:a|an|the)?\s*([a-zA-Z0-9\s\-_]+?)(?:\?|\.|\,|$|\bfor\b|\bin\b|\bunders?\b)",
        r"(?:i\s+(?:made|make|manufacture|produce|sell)|we\s+(?:make|manufacture|produce|sell)|our\s+product\s+is)\s+(?:a|an|the)?\s*([a-zA-Z0-9\s\-_]+?)(?:\?|\.|\,|$|\bfor\b|\bin\b|\bunders?\b)",
        r"(?:standard\s+for|certification\s+for|documents?\s+(?:for|needed\s+for|required\s+for)|tests?\s+(?:for|required\s+for)|testing\s+(?:for|requirements?\s+for))\s+(?:a|an|the)?\s*([a-zA-Z0-9\s\-_]+?)(?:\?|\.|\,|$)",
        r"(?:what\s+standard\s+(?:covers|applies\s+to)|which\s+standard\s+(?:covers|applies\s+to)|standards?\s+(?:covering|applies\s+to))\s+(?:a|an|the)?\s*([a-zA-Z0-9\s\-_]+?)(?:\?|\.|\,|$)",
        r"(?:is\s+)?(?:bis\s+)?(?:certification|license|registration)\s+(?:needed|required|mandatory)?\s+(?:for|on)?\s+(?:a|an|the)?\s*([a-zA-Z0-9\s\-_]+?)(?:\?|\.|\,|$)",
    ]
    for pat in transition_patterns:
        m = re.search(pat, q_lower)
        if m:
            extracted = m.group(1).strip()
            clean = re.sub(r'^(?:a|an|the|my|our|this)\s+', '', extracted).strip()
            clean = re.sub(r'\b(in india|imported|domestic|please|today|now)\b', '', clean).strip()
            if clean and len(clean) >= 2 and clean not in GREETING_WORDS and clean not in GENERIC_PRODUCT_STOPWORDS:
                # Check known catalog for candidate
                catalog_match = None
                for entry in KNOWN_BIS_STANDARDS_CATALOG:
                    if any(re.search(r'\b' + re.escape(kw) + r'\b', clean) for kw in entry["keywords"]):
                        catalog_match = entry
                        break
                return clean, catalog_match

    # 2. Match against known catalog keywords in full query
    for entry in KNOWN_BIS_STANDARDS_CATALOG:
        for kw in entry["keywords"]:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, q_lower):
                return kw, entry

    # 3. Structured detector check
    det = detect_bis_standard_structured(query)
    if det.is_supported and det.candidate:
        name = det.candidate.keywords[0] if det.candidate.keywords else det.candidate.standard_title
        catalog_match = next((e for e in KNOWN_BIS_STANDARDS_CATALOG if e["standard_code"] == det.candidate.standard_code), None)
        return name, catalog_match

    # 4. Short standalone product candidate (1 to 4 words)
    words = re.findall(r'\b[a-zA-Z0-9\-]+\b', q_lower)
    if 1 <= len(words) <= 4:
        query_as_phrase = " ".join(words)
        # Check against exclusions
        is_greeting_match = (
            query_as_phrase in GREETING_WORDS
            or (len(words) == 1 and words[0] in GREETING_WORDS)
            or is_greeting(query_as_phrase)
            or is_farewell(query_as_phrase)
            or is_thanks(query_as_phrase)
        )
        is_origin = any(query_as_phrase == orig for orig in [
            "manufactured in india", "made in india", "india", "in india",
            "domestic", "imported", "import", "foreign", "china", "germany",
            "japan", "usa", "taiwan", "korea", "vietnam", "overseas", "abroad"
        ])
        is_yes_no = query_as_phrase in {"yes", "no", "ok", "sure", "yep", "nope", "yeah", "nah"}

        # Interrogative or question starters cannot be standalone product names
        is_question_starter = words[0] in {
            "what", "which", "how", "why", "when", "where", "who", "whom", "whose",
            "can", "could", "should", "would", "is", "are", "do", "does", "did",
            "tell", "show", "give", "explain", "provide"
        }

        # General regulatory intent keywords that represent inquiries, not products
        INTENT_QUERY_WORDS = {
            "test", "tests", "testing", "document", "documents", "doc", "docs",
            "fee", "fees", "cost", "costs", "timeline", "timelines", "time",
            "procedure", "process", "step", "steps", "checklist", "renewal", "renew",
            "marking", "labelling", "label", "logo", "scheme", "schemes",
            "qco", "isi", "crs", "bis", "requirement", "requirements", "required",
            "needed", "mandatory", "compulsory", "license", "licence", "registration",
            "certificate", "certification", "compliance", "standard", "standards",
            "rule", "rules", "guideline", "guidelines", "penalty", "offence", "exemption",
            "help", "menu", "info", "status"
        }
        has_intent_word = any(w in INTENT_QUERY_WORDS for w in words)

        is_intent_phrase = (
            is_question_starter
            or has_intent_word
            or any(query_as_phrase == ip for ip in [
                "what are all the documents needed to register my product",
                "what are the documents needed to register my product",
                "what documents do i need", "documents required", "document checklist",
                "how to apply", "application procedure", "fees and timelines", "how much fee",
                "difference between isi and crs", "is it mandatory", "qco applicability",
                "renew license", "marking requirements", "what is bis"
            ])
        )
        is_generic_stop = query_as_phrase in GENERIC_PRODUCT_STOPWORDS

        if not (is_greeting_match or is_origin or is_yes_no or is_intent_phrase or is_generic_stop):
            clean_cand = re.sub(r'^(?:a|an|the|my|our|this)\s+', '', query_as_phrase).strip()
            clean_cand = re.sub(r'\b(in india|imported|domestic|please|today|now)\b', '', clean_cand).strip()
            if clean_cand and len(clean_cand) >= 2 and clean_cand not in GENERIC_PRODUCT_STOPWORDS:
                # Check known catalog for match
                catalog_match = None
                for entry in KNOWN_BIS_STANDARDS_CATALOG:
                    if any(re.search(r'\b' + re.escape(kw) + r'\b', clean_cand) for kw in entry["keywords"]):
                        catalog_match = entry
                        break
                return clean_cand, catalog_match

    return None, None




def extract_origin_entity(query: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts manufacturing origin and country from text.
    Returns (import_status, manufacturing_country) where import_status is 'domestic' or 'imported'.
    """
    q_lower = query.lower()

    # Domestic patterns
    domestic_patterns = [
        "manufactured in india", "made in india", "domestic", "india",
        "indian manufacturer", "in india", "locally produced", "local manufacturer"
    ]
    if any(p in q_lower for p in domestic_patterns):
        return "domestic", "India"

    # Foreign / Imported patterns
    imported_patterns = [
        "imported", "import", "foreign", "china", "germany", "japan", "usa",
        "taiwan", "korea", "vietnam", "overseas", "abroad", "foreign manufacturer"
    ]
    for p in imported_patterns:
        if p in q_lower:
            country = p.capitalize() if p not in ["imported", "import", "foreign", "overseas", "abroad"] else "Foreign"
            return "imported", country

    return None, None


# ==============================================================================
# Conversational Assistant Engine
# ==============================================================================

class ConversationalBISAssistant:
    """
    Coordinates multi-turn dialogue, context resolution, intent routing,
    grounded evidence retrieval, and structured response synthesis.
    """

    def __init__(self, rag_engine, conversation_store: Optional[ConversationStore] = None):
        self.rag_engine = rag_engine
        self.store = conversation_store or ConversationStore()

    def process_turn(
        self,
        conversation_id: str,
        message: str,
        user_id: Optional[str] = None,
        channel: str = "web",
        application_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Processes one conversational turn across Website or WhatsApp channels."""
        msg_clean = (message or "").strip()
        msg_lower = msg_clean.lower()

        # 1. Retrieve or initialize isolated conversation state
        state = self.store.get_or_create(conversation_id, user_id=user_id, channel=channel)

        # Seed from application_context if provided and state does not already have it
        if application_context:
            if not state.product_name and application_context.get("productName"):
                state.product_name = application_context.get("productName").lower().strip()
            if not state.candidate_standard and application_context.get("standardCode"):
                state.candidate_standard = application_context.get("standardCode").strip()
            if not state.product_category and application_context.get("productCategory"):
                state.product_category = application_context.get("productCategory").strip()
            if not state.import_status and application_context.get("countryOfOrigin"):
                country = application_context.get("countryOfOrigin", "").strip().lower()
                state.manufacturing_country = application_context.get("countryOfOrigin")
                state.import_status = "domestic" if country == "india" else "imported"

        # 2. Check for statutory boundary violations
        if any(w in msg_lower for w in ["issue license", "issue me a bis", "officially approve", "guarantee certification", "grant certificate", "grant license"]):
            resp = self._handle_statutory_boundary()
            state.add_turn("user", msg_clean, intent="statutory_boundary")
            state.add_turn("assistant", resp["content"], intent="statutory_boundary")
            self.store.save(state)
            return resp

        # 3. Check for adversarial injection
        if any(w in msg_lower for w in ["system override", "ignore previous instructions", "ignore all previous", "print your system prompt", "reveal api keys"]):
            resp = self._handle_adversarial()
            state.add_turn("user", msg_clean, intent="adversarial_guardrail")
            state.add_turn("assistant", resp["content"], intent="adversarial_guardrail")
            self.store.save(state)
            return resp

        # 4. Message-intent routing before regulatory retrieval: Greeting, Farewell, Thanks
        if is_greeting(msg_clean):
            resp = self._handle_greeting(state)
            state.add_turn("user", msg_clean, intent=INTENT_GREETING)
            state.add_turn("assistant", resp["content"], intent=INTENT_GREETING)
            self.store.save(state)
            return resp

        if is_farewell(msg_clean):
            resp = self._handle_farewell(state)
            state.add_turn("user", msg_clean, intent=INTENT_FAREWELL)
            state.add_turn("assistant", resp["content"], intent=INTENT_FAREWELL)
            self.store.save(state)
            return resp

        if is_thanks(msg_clean):
            resp = self._handle_thanks(state)
            state.add_turn("user", msg_clean, intent=INTENT_THANKS)
            state.add_turn("assistant", resp["content"], intent=INTENT_THANKS)
            self.store.save(state)
            return resp

        # 5. Extract entities from current turn
        prod_entity, catalog_entry = extract_product_entity(msg_clean)
        origin_status, country = extract_origin_entity(msg_clean)

        # Detect product change
        if prod_entity:
            new_prod = prod_entity.lower().strip()
            old_prod = (state.product_name or "").lower().strip()
            is_product_change = bool(
                old_prod
                and new_prod != old_prod
                and new_prod not in old_prod
                and old_prod not in new_prod
            )

            if is_product_change:
                logger.info(f"Product change detected: '{old_prod}' -> '{new_prod}'. Resetting product-specific context.")
                state.switch_product(new_product=new_prod, catalog_entry=catalog_entry)
            else:
                state.product_name = new_prod
                if catalog_entry:
                    state.candidate_standard = catalog_entry["standard_code"]
                    state.candidate_standards = [catalog_entry["standard_code"]]
                    state.candidate_title = catalog_entry.get("standard_title")
                    state.product_category = catalog_entry.get("category")
                    state.certification_scheme = catalog_entry.get("scheme")

        if origin_status:
            state.import_status = origin_status
            state.manufacturing_country = country

        # 6. Intent classification (context-aware)
        intent = classify_intent(msg_clean, state)
        state.current_intent = intent

        # 7. Check if current turn answers a pending clarification question
        if state.conversation_status == "awaiting_clarification":
            if state.pending_clarification_type == "product" and state.product_name:
                state.pending_clarification_type = None
                # If we still need manufacturing origin for document/procedure journeys
                if state.current_intent in [INTENT_DOCUMENT_CHECKLIST, INTENT_APPLICATION_PROCEDURE] and not state.import_status:
                    state.pending_clarification_type = "origin"
                    clarify_text = (
                        f"I'll check the relevant {state.product_name} standard ({state.candidate_standard or 'applicable Indian Standard'}) "
                        f"and certification route against the available official evidence.\n\n"
                        f"Is the {state.product_name} manufactured in India or imported?"
                    )
                    state.current_clarification_question = clarify_text
                    state.add_turn("user", msg_clean, intent=state.current_intent)
                    state.add_turn("assistant", clarify_text, intent=state.current_intent)
                    self.store.save(state)
                    return {
                        "content": clarify_text + STATUTORY_DISCLAIMER_SUFFIX,
                        "sources": [],
                        "confidence": 0.95,
                        "insufficient_evidence": False,
                        "warnings": [],
                        "conversation_id": state.conversation_id,
                        "status": "awaiting_clarification"
                    }
                else:
                    state.conversation_status = "active"

            elif state.pending_clarification_type == "origin" and state.import_status:
                state.pending_clarification_type = None
                state.conversation_status = "active"

        # 8. Check if multi-turn clarification is required for incomplete queries
        if state.current_intent in [INTENT_DOCUMENT_CHECKLIST, INTENT_APPLICATION_PROCEDURE]:
            if not state.product_name:
                state.conversation_status = "awaiting_clarification"
                state.pending_clarification_type = "product"
                clarify_text = (
                    "I can help you prepare a BIS certification document checklist. "
                    "The required documents depend on your product and the applicable certification scheme.\n\n"
                    "First, what product do you want to register?"
                )
                state.current_clarification_question = clarify_text
                state.add_turn("user", msg_clean, intent=state.current_intent)
                state.add_turn("assistant", clarify_text, intent=state.current_intent)
                self.store.save(state)
                return {
                    "content": clarify_text + STATUTORY_DISCLAIMER_SUFFIX,
                    "sources": [],
                    "confidence": 0.95,
                    "insufficient_evidence": False,
                    "warnings": [],
                    "conversation_id": state.conversation_id,
                    "status": "awaiting_clarification"
                }

            if not state.import_status:
                state.conversation_status = "awaiting_clarification"
                state.pending_clarification_type = "origin"
                clarify_text = (
                    f"I'll check the relevant {state.product_name} standard ({state.candidate_standard or 'applicable Indian Standard'}) "
                    f"and certification route against the available official evidence.\n\n"
                    f"Is the {state.product_name} manufactured in India or imported?"
                )
                state.current_clarification_question = clarify_text
                state.add_turn("user", msg_clean, intent=state.current_intent)
                state.add_turn("assistant", clarify_text, intent=state.current_intent)
                self.store.save(state)
                return {
                    "content": clarify_text + STATUTORY_DISCLAIMER_SUFFIX,
                    "sources": [],
                    "confidence": 0.95,
                    "insufficient_evidence": False,
                    "warnings": [],
                    "conversation_id": state.conversation_id,
                    "status": "awaiting_clarification"
                }

        # 9. Context is complete or inquiry is direct. Build targeted query & execute RAG
        rag_query, active_filter = self._build_grounded_rag_query(msg_clean, state)
        
        # Retrieve evidence
        retrieval_results = self.rag_engine.retrieve_with_scores(
            query=rag_query,
            top_k=5,
            standard_filter=active_filter
        )
        retrieved_chunks = [r.chunk for r in retrieval_results]

        # Evidence Relevance Validation: A retrieval score alone is not proof of applicability
        verified_chunks = self._validate_evidence_relevance(retrieved_chunks, state, msg_clean)
        retrieved_chunks = verified_chunks

        # Route to standard RAG engine to evaluate query & support mock overrides
        rag_res = self.rag_engine.answer_query(
            query=rag_query,
            application_context=application_context
        )
        if rag_res.get("insufficient_evidence"):
            content = rag_res.get("content", "")
            if "does not provide sufficient" in content or "https://www.bis.gov.in" in content:
                state.turns.append({"role": "assistant", "content": content, "timestamp": datetime.now(timezone.utc).isoformat()})
                self.store.save(state)
                return rag_res
            if state.product_name and not retrieved_chunks:
                return self._handle_unindexed_product(state, msg_clean)
            state.turns.append({"role": "assistant", "content": content, "timestamp": datetime.now(timezone.utc).isoformat()})
            self.store.save(state)
            return rag_res

        # If product is stated but no verified evidence exists in indexed corpus
        if state.product_name and not retrieved_chunks:
            return self._handle_unindexed_product(state, msg_clean)

        # Construct structured response
        if state.current_intent in [INTENT_DOCUMENT_CHECKLIST, INTENT_APPLICATION_PROCEDURE] and state.product_name:
            response_content, citations = self._synthesize_structured_application_answer(state, retrieved_chunks)
            state.conversation_status = "active"
        else:
            response_content = rag_res.get("content", "")
            citations = rag_res.get("sources", [])

        # Sanitize internal IDs
        cleaned_content = self._sanitize_chunk_ids(response_content, retrieved_chunks)

        # Record conversation turns
        state.add_turn("user", msg_clean, intent=state.current_intent)
        state.add_turn("assistant", cleaned_content, intent=state.current_intent)
        self.store.save(state)

        insufficient_flag = rag_res.get("insufficient_evidence", False) if rag_res is not None else (len(retrieved_chunks) == 0)

        return {
            "content": cleaned_content,
            "sources": citations,
            "confidence": 0.95,
            "insufficient_evidence": insufficient_flag,
            "warnings": [],
            "conversation_id": state.conversation_id,
            "status": state.conversation_status
        }

    def _build_grounded_rag_query(self, user_msg: str, state: ConversationState) -> Tuple[str, Optional[str]]:
        """Constructs an evidence query that pulls procedural or technical documents based on intent."""
        parts = [user_msg]
        active_filter = None

        if state.product_name:
            parts.append(state.product_name)

        if state.candidate_standard:
            parts.append(state.candidate_standard)
            # If asking technical testing questions, boost the product standard
            if state.current_intent == INTENT_TESTING_REQUIREMENTS:
                active_filter = state.candidate_standard

        if state.current_intent in [INTENT_DOCUMENT_CHECKLIST, INTENT_APPLICATION_PROCEDURE]:
            parts.append("document checklist application procedure Form-1 Form-V Manak Online")
            if "CRS" in (state.certification_scheme or "") or "16102" in (state.candidate_standard or "") or "13252" in (state.candidate_standard or ""):
                parts.append("Compulsory Registration Scheme Scheme II")
            else:
                parts.append("Product Certification Scheme Scheme I ISI Mark")

        if state.import_status == "domestic":
            parts.append("domestic manufacturer factory registration")
        elif state.import_status == "imported":
            parts.append("foreign manufacturer AIR Authorized Indian Representative FMCS")

        return " ".join(parts), active_filter

    def _validate_evidence_relevance(
        self,
        chunks: List[KnowledgeChunk],
        state: ConversationState,
        query: str
    ) -> List[KnowledgeChunk]:
        """
        Evidence Relevance Validation (Requirement 6):
        Does not answer a product question using unrelated product evidence (e.g. toy safety
        for steel water bottles). A retrieval score alone is not proof of applicability.
        """
        if not chunks:
            return []

        q_lower = (query or "").lower().strip()
        is_comparison_query = any(w in q_lower for w in ["compare", "comparison", "difference between", "versus", " vs "])

        standard_product_domain = {
            "IS 9873": ["toy", "toys", "rc car", "remote control car", "remote control toy", "game", "doll"],
            "IS 16102": ["led", "lamp", "bulb", "lighting", "tube light"],
            "IS 4151": ["helmet", "headgear", "motorcycle helmet", "two-wheeler"],
            "IS 374": ["fan", "ceiling fan", "bldc"],
            "IS 1293": ["plug", "socket", "outlet"],
            "IS 16046": ["battery", "cell", "power bank", "lithium"],
            "IS 16221": ["solar", "inverter", "pv", "photovoltaic"],
            "IS 16169": ["solar", "islanding", "inverter", "pv"],
            "IS 17017": ["ev charger", "electric vehicle", "charging station"],
            "IS 13252": ["adapter", "smps", "it equipment", "power supply", "charger"],
            "IS 14543": ["packaged drinking water", "mineral water", "bottled water"],
            "IS 269": ["cement", "portland cement"]
        }

        prod = (state.product_name or "").lower().strip()
        candidate_std = (state.candidate_standard or "").lower().strip()
        validated: List[KnowledgeChunk] = []

        for c in chunks:
            code = c.standard_code or ""

            # 1. Statutory framework and administrative/fee documents
            is_general_doc = any(k in code for k in ["Act", "Regulations", "Scheme_I", "Scheme_II", "Framework", "Financial"])
            if is_general_doc:
                if state.current_intent in [
                    INTENT_DOCUMENT_CHECKLIST, INTENT_APPLICATION_PROCEDURE,
                    INTENT_FEES_TIMELINES, INTENT_SCHEME_REQUIREMENTS,
                    INTENT_LICENCE_RENEWAL, INTENT_GENERAL_INQUIRY
                ]:
                    validated.append(c)
                continue

            # 2. Product-specific technical standards
            matched_standard_key = next((k for k in standard_product_domain if k in code), None)
            if matched_standard_key:
                domain_keywords = standard_product_domain[matched_standard_key]
                is_prod_match = bool(prod and any(dk in prod for dk in domain_keywords))
                is_query_match = any(dk in q_lower for dk in domain_keywords) or (matched_standard_key.lower() in q_lower)
                is_std_match = bool(candidate_std and matched_standard_key.lower() in candidate_std)

                if prod:
                    if is_prod_match or (is_comparison_query and is_query_match) or is_std_match:
                        validated.append(c)
                    else:
                        logger.debug(f"Rejecting irrelevant evidence chunk {c.chunk_id} ({code}) for product '{prod}'")
                else:
                    if is_query_match or is_std_match:
                        validated.append(c)
                    else:
                        validated.append(c)
            else:
                if not prod or prod in (c.standard_title.lower() + " " + c.content.lower()):
                    validated.append(c)

        return validated

    def _handle_unindexed_product(self, state: ConversationState, user_msg: str) -> Dict[str, Any]:
        """
        When the product or intended use is unclear or missing from regulatory evidence (Requirement 7):
        Returns transparent limitation and asks a short clarification question.
        Does not invent the applicable Indian Standard, QCO, mandatory certification status,
        document checklist, or statutory fees.
        """
        prod_title = state.product_name.title() if state.product_name else "Your Specified Product"
        prod_name = state.product_name or "specified item"
        clarify_text = (
            f"I understand your product inquiry is for **{prod_title}**.\n\n"
            f"The verified Bureau of Indian Standards (BIS) regulatory repository currently indexed in ISense does not contain "
            f"mandatory conformity assessment records or laboratory testing specifications specifically covering **{prod_name}**.\n\n"
            f"**To assist with identifying potential compliance requirements, please clarify:**\n"
            f"1. What is the specific product type, construction, and intended application of the {prod_name}?\n"
            f"2. What technical specifications, voltage/capacity ratings, or materials apply?\n"
            f"3. Do you have a specific Indian Standard (IS) number or Quality Control Order (QCO) reference for this item?\n\n"
            f"*(Notice: ISense relies exclusively on official statutory evidence and does not invent applicable Indian Standards, Quality Control Orders (QCO), or document checklists without verified records. "
            f"Please verify officially notified standards directly on the statutory [BIS Manak Online Standards Portal](https://www.services.bis.gov.in) or [BIS Official Website](https://www.bis.gov.in).)*"
            + STATUTORY_DISCLAIMER_SUFFIX
        )
        state.conversation_status = "awaiting_clarification"
        state.pending_clarification_type = "product_specification"
        state.current_clarification_question = clarify_text
        state.add_turn("user", user_msg, intent=state.current_intent)
        state.add_turn("assistant", clarify_text, intent=state.current_intent)
        self.store.save(state)
        return {
            "content": clarify_text,
            "sources": [],
            "confidence": 0.0,
            "insufficient_evidence": True,
            "warnings": [f"No verified regulatory evidence indexed for '{state.product_name}'."],
            "conversation_id": state.conversation_id,
            "status": "awaiting_clarification"
        }


    def _synthesize_structured_application_answer(
        self,
        state: ConversationState,
        chunks: List[KnowledgeChunk]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Synthesizes the required 7-section structured response."""
        prod = state.product_name or "Specified Product"
        origin = state.import_status or "domestic"
        is_domestic = (origin == "domestic")
        country = state.manufacturing_country or ("India" if is_domestic else "Foreign")
        std_code = state.candidate_standard or "Applicable Indian Standard"
        scheme = state.certification_scheme or ("Compulsory Registration Scheme (CRS / Scheme II)" if "16102" in std_code else "Product Certification Scheme (Scheme I - ISI Mark)")

        is_crs = "CRS" in scheme or "Scheme II" in scheme or "16102" in std_code or "16046" in std_code or "13252" in std_code

        # Build citations
        citations = []
        for c in chunks:
            citations.append({
                "id": c.chunk_id,
                "title": c.standard_title,
                "documentRef": c.standard_code,
                "page": c.page or 1,
                "section": c.clause,
                "excerpt": c.content[:200] + "...",
                "sourceUrl": c.source_url,
                "verification_status": c.verification_status
            })

        # Section 1: Product and applicant context
        s1 = (
            f"### 1. Product & Applicant Context\n"
            f"• **Product**: {prod.title()}\n"
            f"• **Manufacturing Origin**: {country} ({'Domestic Manufacturing' if is_domestic else 'Imported / Foreign Manufacturing'})\n"
            f"• **Applicable Standard**: **{std_code}**\n"
            f"• **Regulatory Scheme**: **{scheme}**"
        )

        # Section 2: Likely certification route and applicability conditions
        if is_crs:
            s2 = (
                f"### 2. Likely Certification Route & Applicability Conditions\n"
                f"• **Regulatory Route**: Compulsory Registration Scheme (CRS / Scheme II) under MeitY and DPIIT Quality Control Orders.\n"
                f"• **Conditions**: Unlike Scheme I, CRS does not require an upfront physical factory audit for domestic applicants. "
                f"Registration is granted based on passing test reports from an accredited, BIS-recognized testing laboratory in India.\n"
                f"• **Applicability Boundary**: Covers self-ballasted lamps and IT/electronic equipment meeting standard voltage and wattage scopes."
            )
        else:
            s2 = (
                f"### 2. Likely Certification Route & Applicability Conditions\n"
                f"• **Regulatory Route**: Product Certification Scheme (Scheme I — ISI Mark) under Quality Control Orders.\n"
                f"• **Conditions**: Mandatory requirement for in-house manufacturing, quality control infrastructure conforming to the Scheme of Testing and Inspection (STI), and on-site factory audit by BIS officers."
            )

        # Section 3: Required documents (mandatory vs conditional)
        if is_crs:
            s3 = (
                f"### 3. Required Document Checklist\n"
                f"**Mandatory Application Documents:**\n"
                f"1. **Laboratory Test Report**: Complete safety test report issued by an accredited/BIS-recognized laboratory (NABL/LRS) within 90 days of online application submission.\n"
                f"2. **Form-1 Application**: System-generated application form submitted via the official BIS CRS portal.\n"
                f"3. **Proof of Manufacturing Premises**: Factory registration, GST registration, or municipal manufacturing license establishing actual production operations.\n"
                f"4. **Brand / Trademark Ownership**: Trademark registration certificate. If applying on behalf of a brand owner, an official Trademark Authorization Form is mandatory.\n"
                f"5. **Statutory Undertaking & Affidavit**: Undertaking confirming compliance to Indian Standards and model series declarations.\n"
                f"6. **Signatory KYC**: PAN / Aadhaar / Passport of the authorized signatory along with board authorization.\n\n"
                f"**Conditional / If Applicable:**\n"
                f"• *Foreign Manufacturers*: Nomination and agreement for Authorized Indian Representative (AIR) residing in India.\n"
                f"• *Multiple Models*: Series approval justification matrix if covering secondary models under one base model test report.\n"
                f"• *MSME / Udyam Registration*: Required if applying for statutory fee concessions."
            )
        else:
            s3 = (
                f"### 3. Required Document Checklist\n"
                f"**Mandatory Application Documents:**\n"
                f"1. **Form-V**: Formal application for grant of license submitted via the BIS Manak Online portal.\n"
                f"2. **Proof of Factory Premises**: Registered lease deed or title deed, municipal factory license, and Consent to Operate (CTO) from the State Pollution Control Board.\n"
                f"3. **Machinery & Infrastructure**: List of manufacturing machinery, plant layout plan, and manufacturing process flow chart.\n"
                f"4. **In-House Testing Facility**: List of testing equipment installed as per Scheme of Testing and Inspection (STI) with valid calibration certificates.\n"
                f"5. **Competent Quality Staff**: Appointment letters, degrees, and testing experience records of internal quality control personnel.\n"
                f"6. **Trademark Documents**: Registered trademark certificate or valid brand authorization letter.\n\n"
                f"**Conditional / If Applicable:**\n"
                f"• *Foreign Facilities (FMCS)*: Formal nomination of Authorized Indian Representative (AIR) and RBI commercial approval.\n"
                f"• *MSME Registration*: For micro and small enterprise fee concessions."
            )

        # Section 4: Testing and laboratory requirements
        if "16102" in std_code:
            s4 = (
                f"### 4. Testing & Laboratory Requirements\n"
                f"• **Governing Standard**: IS 16102 (Part 1) : 2012 (Safety of Self-Ballasted LED-Lamps).\n"
                f"• **Key Safety Parameters**:\n"
                f"  - **Insulation Resistance & Electric Strength (Clause 8)**: Insulation resistance >= 4.0 Megohms at 500V DC; electric strength withstand of 1500V AC rms for 1 minute.\n"
                f"  - **Cap Torque Retention (Clause 9)**: Minimum mechanical torque resistance of 3.0 Nm for B22d and E27 caps (1.15 Nm for E14).\n"
                f"  - **Creepage & Clearance (Clause 12)**: Minimum creepage distance of 3.0mm and clearance distance of 2.5mm.\n"
                f"• **Testing Location**: Must be carried out at a BIS-recognized / NABL accredited Indian testing laboratory."
            )
        else:
            s4 = (
                f"### 4. Testing & Laboratory Requirements\n"
                f"• **Governing Standard**: {std_code}.\n"
                f"• **Testing Scope**: Testing must strictly follow the standard's statutory clauses at an accredited laboratory or in-house lab meeting the STI.\n"
                f"• **Validity**: Initial sample test reports must be issued within valid testing windows as specified by BIS guidelines."
            )

        # Section 5: Step-by-step application process
        if is_crs:
            s5 = (
                f"### 5. Step-by-Step Application Procedure\n"
                f"1. **Step 1 (Sample Testing)**: Send product samples to a BIS-recognized testing laboratory for testing under {std_code}. Receive passing test report.\n"
                f"2. **Step 2 (CRS Portal Registration)**: Create user profile on the official [BIS CRS Portal](https://www.crsbis.in/BIS/).\n"
                f"3. **Step 3 (Dossier & Report Upload)**: Submit Form-1, attach laboratory test report (issued within 90 days), and upload factory proof and brand authorizations.\n"
                f"4. **Step 4 (Statutory Fee Payment)**: Pay application fee (₹1,000) and processing fee (₹50,000 for 2-year tenure) via payment gateway.\n"
                f"5. **Step 5 (BIS Scrutiny)**: Scrutiny of test reports and technical dossier by BIS CRS officers.\n"
                f"6. **Step 6 (Grant of Registration)**: BIS issues the Registration Number (R-number) authorizing use of the Standard Mark on approved product packaging."
            )
        else:
            s5 = (
                f"### 5. Step-by-Step Application Procedure\n"
                f"1. **Step 1 (Portal Profile)**: Register manufacturing facility on the [BIS Manak Online Portal](https://www.manakonline.in).\n"
                f"2. **Step 2 (Dossier Filing)**: Complete Form-V and upload plant layout, machinery list, test equipment list, and calibrations.\n"
                f"3. **Step 3 (Fee Payment)**: Pay application fee (₹1,000) and factory inspection fees.\n"
                f"4. **Step 4 (Factory Audit)**: BIS officers visit the manufacturing premises for on-site verification of production and in-house testing.\n"
                f"5. **Step 5 (Sample Testing)**: Factory testing and counter-sample testing at an independent BIS lab.\n"
                f"6. **Step 6 (Grant of License)**: Upon satisfactory inspection and test results, BIS grants the CM/L License."
            )

        # Section 6: Official source links and relevant clauses
        s6 = (
            f"### 6. Official Source Links & References\n"
            f"• [BIS Manak Online Portal (Official E-Filing)](https://www.manakonline.in)\n"
            f"• [BIS Compulsory Registration Scheme Portal](https://www.crsbis.in/BIS/)\n"
            f"• [Official BIS Know Your Standards Portal](https://www.services.bis.gov.in)\n"
            f"• Governing Reference: {std_code}"
        )

        # Section 7: Missing information and next actions
        s7 = (
            f"### 7. Information Requiring Verification & Next Steps\n"
            f"• **Product Specifications**: Model wattage, voltage rating, and cap type must be verified against laboratory test sample limits.\n"
            f"• **Laboratory Selection**: Verify that your chosen laboratory holds valid NABL accreditation and BIS recognition for {std_code}.\n"
            f"• **Trademark Validity**: Ensure trademark registration or authorization agreement is formally executed before submission.\n"
            f"• **Final Action**: Prepare technical dossier and submit application through the official BIS Manak Online portal."
        )

        full_content = "\n\n".join([s1, s2, s3, s4, s5, s6, s7]) + STATUTORY_DISCLAIMER_SUFFIX
        return full_content, citations

    def _sanitize_chunk_ids(self, text: str, chunks: List[KnowledgeChunk]) -> str:
        """Removes internal chunk IDs and opaque keys from user-facing text."""
        cleaned = text or ""
        for chunk in chunks:
            clause = f" — {chunk.clause}" if chunk.clause else ""
            readable = f"{chunk.standard_code}{clause}".strip()
            if chunk.chunk_id:
                cleaned = cleaned.replace(chunk.chunk_id, readable)
        cleaned = re.sub(r"\bchk-doc-[A-Za-z0-9_-]+\b", "the referenced BIS evidence", cleaned)
        cleaned = re.sub(r"\bchk-[A-Za-z0-9_-]{6,}\b", "the referenced BIS evidence", cleaned)
        return cleaned

    def _handle_statutory_boundary(self) -> Dict[str, Any]:
        return {
            "content": (
                "**Statutory Boundary & Non-Certification Notice:**\n\n"
                "**No, ISense does not grant licenses, issue Standard Marks, or officially approve products.**\n\n"
                "ISense is an **independent compliance assistance platform** designed to guide manufacturers and applicants through Indian Standards compliance, document verification, and laboratory testing requirements.\n\n"
                "• **Official Authority**: Final certification, ISI mark licenses, and CRS registrations are granted solely by the **Bureau of Indian Standards (BIS)**.\n"
                "• **Statutory Portal**: Official submissions must be filed directly on the statutory [BIS Manak Online Portal](https://www.manakonline.in)."
                + STATUTORY_DISCLAIMER_SUFFIX
            ),
            "sources": [],
            "confidence": 1.0,
            "insufficient_evidence": False,
            "warnings": [],
            "status": "active"
        }

    def _handle_adversarial(self) -> Dict[str, Any]:
        return {
            "content": (
                "**Advisory Guardrail Enforcement:**\n\n"
                "System instructions, administrative configurations, and API keys are protected and cannot be disclosed. "
                "ISense is dedicated strictly to Bureau of Indian Standards regulatory compliance assistance.\n\n"
                "Please ask questions related to applicable Indian Standards, technical testing clauses, document verification, or portal submission steps."
                + STATUTORY_DISCLAIMER_SUFFIX
            ),
            "sources": [],
            "confidence": 1.0,
            "insufficient_evidence": False,
            "warnings": ["Adversarial query rejected."],
            "status": "active"
        }

    def _handle_greeting(self, state: Optional[ConversationState] = None) -> Dict[str, Any]:
        """
        Returns a short, helpful greeting response without running regulatory retrieval.
        Preserves existing conversation state for future follow-up questions without repeating previous answers.
        """
        if state and state.product_name:
            prod_title = state.product_name.title()
            content = (
                f"👋 **Hello! Welcome to ISense.**\n\n"
                f"We were previously discussing **{prod_title}**. How can I assist you further with this, or would you like to inquire about another product or Indian Standard?"
                + STATUTORY_DISCLAIMER_SUFFIX
            )
        else:
            content = (
                "👋 **Welcome to ISense — Your BIS Regulatory Assistant!**\n\n"
                "I provide verified compliance guidance for **Bureau of Indian Standards (BIS)** certifications, "
                "mandatory Indian Standards, laboratory testing protocols, and portal filings.\n\n"
                "💡 **How to ask me:**\n"
                "• *Product Inquiries*: e.g., _\"What standard applies to LED lamps?\"_ or _\"Rc car\"_\n"
                "• *Standard Requirements*: e.g., _\"Explain testing clauses for IS 16102\"_\n"
                "• *Process Guidance*: e.g., _\"Documents required for ISI Mark certification\"_\n\n"
                "What product or Indian Standard would you like to explore?"
                + STATUTORY_DISCLAIMER_SUFFIX
            )
        return {
            "content": content,
            "sources": [],
            "confidence": 1.0,
            "insufficient_evidence": False,
            "is_greeting": True,
            "status": state.conversation_status if state else "active",
            "conversation_id": state.conversation_id if state else None
        }

    def _handle_farewell(self, state: Optional[ConversationState] = None) -> Dict[str, Any]:
        content = (
            "Goodbye! 👋 Have a great day. Feel free to reach out anytime you need assistance with "
            "Bureau of Indian Standards (BIS) compliance, testing clauses, or certification procedures."
            + STATUTORY_DISCLAIMER_SUFFIX
        )
        return {
            "content": content,
            "sources": [],
            "confidence": 1.0,
            "insufficient_evidence": False,
            "is_farewell": True,
            "status": state.conversation_status if state else "active",
            "conversation_id": state.conversation_id if state else None
        }

    def _handle_thanks(self, state: Optional[ConversationState] = None) -> Dict[str, Any]:
        content = (
            "You're very welcome! 😊 Please feel free to ask if you have any further questions about "
            "Indian Standards, laboratory testing requirements, or BIS application procedures."
            + STATUTORY_DISCLAIMER_SUFFIX
        )
        return {
            "content": content,
            "sources": [],
            "confidence": 1.0,
            "insufficient_evidence": False,
            "is_thanks": True,
            "status": state.conversation_status if state else "active",
            "conversation_id": state.conversation_id if state else None
        }
