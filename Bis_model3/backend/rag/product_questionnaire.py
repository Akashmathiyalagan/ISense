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
    """Create a compact evidence-aware fallback when Gemini is unavailable.

    Candidate catalogue titles drive the questions when available. With no
    candidates, ask only the minimum product-identification questions needed
    to search again; do not inject a fixed six-question business form.
    """
    product = " ".join((product or "").split())[:120]
    candidates = [
        item for item in (catalogue_candidates or [])
        if isinstance(item, dict) and item.get("is_number") and item.get("title")
    ][:6]

    if candidates:
        choices = []
        for item in candidates:
            option = f"{item['title']} ({item['is_number']})"
            if option not in choices:
                choices.append(option[:100])
        choices.append("None of these / not sure")
        fields = [
            _field(
                "candidate_product_scope",
                f"Which catalogue description is closest to your {product}?",
                "radio",
                choices,
                True,
                "These are preliminary catalogue title matches. Choosing one does not mean the standard applies.",
            ),
            _field(
                "product_subtype",
                f"What exact type, design or model of {product} is it?",
                "text",
                [],
                True,
                "Describe its function and construction so ISense can distinguish the candidate scopes.",
            ),
            _field(
                "intended_use",
                "What is its intended use or user group?",
                "radio",
                [
                    "Household / consumer",
                    "Office / institutional",
                    "Children / toy",
                    "Commercial / industrial",
                    "Medical / specialist",
                    "Other / not sure",
                ],
                True,
            ),
        ]
        description = (
            "ISense found possible BIS catalogue matches. These questions focus on distinguishing their scopes; "
            "the catalogue itself does not establish applicability."
        )
        schema_source = "catalogue_aware_fallback"
    else:
        fields = [
            _field(
                "product_subtype",
                f"What exact type or version of {product} do you mean?",
                "text",
                [],
                True,
                "Describe its function, design and where it is used.",
            ),
            _field(
                "intended_use",
                "What is its intended use or user group?",
                "radio",
                [
                    "Household / consumer",
                    "Office / institutional",
                    "Children / toy",
                    "Commercial / industrial",
                    "Medical / specialist",
                    "Other / not sure",
                ],
                True,
            ),
            _field(
                "distinguishing_specs",
                "What key specification could help identify the product?",
                "text",
                [],
                False,
                "For example: material, dimensions, load/rating, voltage, model or grade—only if relevant.",
            ),
        ]
        description = (
            "No sufficiently specific catalogue match was found yet. These short questions gather the product facts "
            "needed to search the BIS catalogue and indexed scope documents again."
        )
        schema_source = "minimal_research_fallback"

    return {
        "product": product,
        "title": f"Identify the BIS scope for {product}",
        "description": description,
        "fields": fields[:MAX_FIELDS],
        "schema_source": schema_source,
        "catalogue_candidates": candidates,
        "redirectPath": f"/apps?product={quote(product)}",
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
