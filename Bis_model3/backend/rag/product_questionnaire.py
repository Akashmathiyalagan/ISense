"""Product-aware intake questionnaire generation for ISense.

The questionnaire collects user-provided product facts. It is not a BIS
classification engine and must not state that any certification is mandatory.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote

MAX_FIELDS = 8
MAX_OPTIONS = 8
ALLOWED_TYPES = {"checkbox", "radio", "text"}


def _field(field_id: str, label: str, input_type: str, options: Optional[List[str]] = None,
           required: bool = False, help_text: str = "") -> Dict[str, Any]:
    return {
        "id": field_id,
        "label": label,
        "type": input_type if input_type in ALLOWED_TYPES else "checkbox",
        "options": (options or [])[:MAX_OPTIONS],
        "required": bool(required),
        "helpText": help_text,
    }


def fallback_questionnaire(
    product: str,
    catalogue_candidates: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Safe offline questionnaire; common products get tailored questions.

    For products not recognised here, the generic questions still collect
    useful details. When an LLM is configured, the endpoint tries to generate
    a tailored schema dynamically before using this fallback.
    """
    p = product.lower()
    fields: List[Dict[str, Any]] = []

    candidates = [
        item for item in (catalogue_candidates or [])
        if isinstance(item, dict) and item.get("is_number") and item.get("title")
    ]
    if candidates:
        choices = []
        for item in candidates[:6]:
            option = f"{item['title']} ({item['is_number']})"
            if option not in choices:
                choices.append(option[:100])
        if len(choices) >= 2:
            fields.append(_field(
                "candidate_product_scope",
                f"Which BIS catalogue description is closest to your {product.strip()}?",
                "radio",
                choices + ["None of these / not sure"],
                True,
                "These are catalogue-title matches only, not a determination that a standard applies. Choose the closest product description.",
            ))
            fields.append(_field(
                "product_subtype",
                f"What specific type or model of {product.strip()} do you have?",
                "text",
                [],
                True,
                "Describe its design, construction, model or purpose so ISense can distinguish the candidate scopes.",
            ))
            fields.append(_field(
                "intended_use",
                "What is the intended use and user group?",
                "radio",
                ["Household / consumer", "Office / institutional", "Children / toy", "Commercial / industrial", "Medical / specialist", "Other / not sure"],
                True,
            ))
            return {
                "product": product.strip(),
                "title": f"Clarify the BIS scope for {product.strip()}",
                "description": "ISense found catalogue candidates. Your answers help distinguish their product scopes; the catalogue itself does not establish applicability.",
                "fields": fields[:MAX_FIELDS],
                "schema_source": "catalogue_aware_fallback",
                "catalogue_candidates": candidates[:6],
                "redirectPath": f"/apps?product={quote(product.strip())}",
            }

    if any(x in p for x in ("water bottle", "bottle", "flask", "thermos")):
        fields.extend([
            _field("container_type", "What type of bottle or container is it?", "checkbox", [
                "Single-wall bottle", "Double-wall / vacuum-insulated bottle", "Thermos flask",
                "Infant feeding bottle", "Sports bottle", "Other / not sure"], True),
            _field("material", "What material is it made from?", "checkbox", [
                "Stainless steel", "Plastic", "Glass", "Copper", "Aluminium", "Multiple materials", "Other / not sure"], True),
            _field("capacity", "What is its capacity?", "radio", [
                "Up to 250 ml", "251–500 ml", "501–750 ml", "751 ml–1 litre", "More than 1 litre", "Custom / not sure"], True),
            _field("intended_use", "What will it be used for?", "checkbox", [
                "Drinking water", "Hot and cold beverages", "Infant feeding", "Outdoor / sports use", "Commercial / institutional use", "Other"], True),
        ])
    elif any(x in p for x in ("backpack", "back bag", "school bag", "schoolbag", "bag")):
        fields.extend([
            _field("bag_type", "What type of bag is it?", "checkbox", [
                "School bag for children", "College backpack", "Travel backpack", "Laptop bag", "Handbag / other bag", "Other / not sure"], True),
            _field("material", "What material is it made from?", "checkbox", [
                "Polyester / nylon", "Canvas / cotton", "Leather / imitation leather", "Plastic / PVC", "Mixed materials", "Other / not sure"], True),
            _field("intended_user", "Who is it designed for?", "radio", [
                "Children under 14", "Teenagers", "Adults", "General use / not sure"], True),
            _field("features", "Which features apply?", "checkbox", [
                "Wheels / trolley", "Laptop compartment", "Reflective elements", "Water-resistant", "None / other"], False),
        ])
    elif any(x in p for x in ("rc car", "toy car", "toy", "remote control car")):
        fields.extend([
            _field("toy_type", "What kind of product is it?", "checkbox", [
                "Remote-controlled toy car", "Ride-on toy", "Model / hobby vehicle for adults", "Other / not sure"], True),
            _field("intended_user", "Who is it intended for?", "radio", [
                "Children under 3", "Children aged 3–8", "Children aged 9–13", "Age 14+ / hobby use", "Not sure"], True),
            _field("power_source", "What powers it?", "checkbox", [
                "Replaceable batteries", "Rechargeable battery", "Mains adapter / charger included", "Other / not sure"], True),
            _field("features", "Which features apply?", "checkbox", [
                "Remote control", "App / Bluetooth control", "Lights / sound", "Charging cable included", "Other"], False),
        ])
    else:
        fields.extend([
            _field("product_type", "Which product type best describes it?", "text", [], True,
                  "Enter the product subtype or model if known."),
            _field("material", "What is the main material or composition?", "checkbox", [
                "Metal", "Plastic / polymer", "Glass / ceramic", "Textile / leather", "Electronic / electrical components", "Mixed materials", "Other / not sure"], False),
            _field("intended_use", "What is its intended use?", "checkbox", [
                "Household / consumer use", "Children's product / toy", "Commercial / industrial use", "Medical / health-related use", "Electrical / electronic use", "Other / not sure"], True),
            _field("specifications", "Any key size, capacity, rating or model details?", "text", [], False,
                  "For example: capacity, dimensions, voltage, model or grade, if applicable."),
        ])

    fields.extend([
        _field("origin", "Where is it manufactured?", "radio", [
            "Manufactured in India", "Imported / manufactured outside India", "Not decided / not sure"], True),
        _field("help_needed", "What BIS guidance do you need?", "checkbox", [
            "Whether certification is required", "Applicable Indian Standard / QCO", "Documents for application",
            "Testing and laboratory requirements", "Fees and application process"], True),
    ])
    return {
        "product": product.strip(),
        "title": f"Tell us more about your {product.strip()}",
        "description": "Select the options that apply. This helps ISense search for relevant official BIS evidence; it does not itself determine certification applicability.",
        "fields": fields[:MAX_FIELDS],
        "schema_source": "safe_fallback",
        "redirectPath": f"/apps?product={quote(product.strip())}",
    }


def _parse_schema(raw: str, product: str) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(text[start:end + 1])
    except Exception:
        return None
    raw_fields = data.get("fields")
    if not isinstance(raw_fields, list):
        return None
    fields = []
    seen = set()
    for item in raw_fields[:MAX_FIELDS]:
        if not isinstance(item, dict):
            continue
        fid = re.sub(r"[^a-zA-Z0-9_]+", "_", str(item.get("id", "field"))).strip("_").lower()[:40]
        label = str(item.get("label", "")).strip()[:180]
        typ = str(item.get("type", "checkbox")).lower()
        options = item.get("options", [])
        if not fid or fid in seen or not label or typ not in ALLOWED_TYPES:
            continue
        if typ in {"checkbox", "radio"}:
            if not isinstance(options, list):
                continue
            options = [str(v).strip()[:100] for v in options if str(v).strip()][:MAX_OPTIONS]
            if len(options) < 2:
                continue
        else:
            options = []
        seen.add(fid)
        fields.append(_field(fid, label, typ, options, item.get("required", False), str(item.get("helpText", ""))[:240]))
    if len(fields) < 2:
        return None
    return {
        "product": product.strip(),
        "title": str(data.get("title") or f"Tell us more about your {product.strip()}")[:140],
        "description": "Select the options that apply. These answers help identify relevant official evidence; they do not themselves establish legal applicability.",
        "fields": fields,
        "schema_source": "llm_generated_validated",
        "redirectPath": f"/apps?product={quote(product.strip())}",
    }


def build_questionnaire(
    product: str,
    llm_provider: Any = None,
    catalogue_candidates: Optional[List[Dict[str, Any]]] = None,
    scope_evidence: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    product = " ".join((product or "").split())[:120]
    if not product:
        raise ValueError("Product name is required")
    if llm_provider is not None:
        provider_name = type(llm_provider).__name__
        if provider_name not in {"UnavailableLLMProvider"}:
            candidates = [
                item for item in (catalogue_candidates or [])
                if isinstance(item, dict) and item.get("is_number") and item.get("title")
            ][:8]
            evidence = [
                item for item in (scope_evidence or [])
                if isinstance(item, dict) and item.get("text")
            ][:6]
            candidate_block = "\n".join(
                f"- {item.get('is_number')}: {item.get('title')} "
                f"(department: {item.get('technical_department') or 'not supplied'}; "
                f"type: {item.get('standard_type') or 'not supplied'}; "
                "metadata only; applicability not established)"
                for item in candidates
            ) or "No matching catalogue title was found."
            evidence_block = "\n".join(
                f"- {item.get('standard_code', 'Standard not labelled')} — "
                f"{item.get('standard_title', 'Title not supplied')} / "
                f"{item.get('clause', 'scope not labelled')}: "
                f"{str(item.get('text', ''))[:650]} "
                f"(source: {item.get('source_url', 'URL not supplied')})"
                for item in evidence
            ) or "No matching indexed scope excerpts were available."

            prompt = (
                f"User entered this product name: {product!r}.\\n\\n"
                "FIRST REVIEW THE MATCHING BIS CATALOGUE RECORDS AND AVAILABLE OFFICIAL SCOPE EXCERPTS BELOW. "
                "The catalogue entries are only number/title metadata, not proof that a standard applies.\\n\\n"
                f"CATALOGUE CANDIDATES:\\n{candidate_block}\\n\\n"
                f"AVAILABLE OFFICIAL SCOPE EVIDENCE:\\n{evidence_block}\\n\\n"
                "Generate a SHORT, product-specific clarification questionnaire that helps distinguish the competing candidate scopes. "
                "This is not a fixed generic form. Use the differences between the candidate titles and supplied scope excerpts to decide "
                "which attributes actually discriminate between them. If no candidates were found, ask a small number of questions to identify "
                "the product subtype and intended use before standards research continues. "
                "Generate only 2 to 5 fields, and do not ask the user to select a standard number they are unlikely to understand. "
                "Ask about subtype, intended user/use, construction/material, performance/rating, installation/environment, or other attributes "
                "ONLY when relevant to this product and candidate scope. Avoid asking generic questions about origin, business role, or desired help "
                "unless those facts are needed for the requested route. Do not ask for facts already clear from the product name. "
                "Never invent an IS number, title, clause, test or regulatory requirement, and never assert that a candidate is applicable or mandatory. "
                "Return ONLY JSON with keys title and fields. Each field must have id, label, type (radio, checkbox, or text), "
                "options (2-8 concise options for radio/checkbox, empty for text), required (boolean), and helpText. "
                "Use clear, professional, easy-to-answer language."
            )
            try:
                result = llm_provider.generate(
                    query=prompt,
                    system_instruction=(
                        "You generate a UI intake form schema only. Output valid JSON, no markdown. "
                        "Do not provide regulatory advice. All options are user-input choices, not legal conclusions."
                    ),
                    retrieved_chunks=[],
                    application_context={"task": "product_intake_schema", "product": product},
                )
                if getattr(result, "is_success", False):
                    parsed = _parse_schema(result.text, product)
                    if parsed:
                        return parsed
            except Exception:
                pass
    return fallback_questionnaire(product, catalogue_candidates=catalogue_candidates)
