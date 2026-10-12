"""Curated, source-linked BIS product guidance for questionnaire completions.

This is a small official-source registry that supplements RAG where an indexed
document is missing. It deliberately returns conditional candidates and
uncertainty rather than guessing an IS number for unsupported product variants.
Review the linked BIS listings/product manuals whenever standards or QCOs change.
"""
from typing import Any, Dict, List, Optional


BIS_SCHEME_I_URL = (
    "https://www.bis.gov.in/product-certification/"
    "products-under-compulsory-certification/scheme-i-mark-scheme/?lang=en"
)
BIS_KNOW_STANDARD_URL = "https://www.bis.gov.in/Know-Your-Standard/?lang=en"
BIS_CERTIFICATION_PROCESS_URL = (
    "https://www.bis.gov.in/product-certification/product-certification-process/?lang=en"
)
BIS_CERTIFICATION_FAQ_URL = (
    "https://www.bis.gov.in/product-certification/product-certification-faq/?lang=en"
)
MANAKONLINE_URL = "https://www.manakonline.in/"
POTABLE_BOTTLES_QCO_2024_URL = (
    "https://www.bis.gov.in/wp-content/uploads/2024/03/"
    "Potable-Water-Bottles-Quality-ControlOrder-2024.pdf"
)
QCO_AMENDMENTS_FEB_2026_URL = (
    "https://www.bis.gov.in/wp-content/uploads/2026/02/"
    "Amendments-in-Quality-Control-Order.pdf"
)
IS17803_LABS_URL = "https://lims.bis.gov.in/home/search_is_number/?is_number__doc_no=17803"
IS17526_MANUAL_URL = "https://www.bis.gov.in/wp-content/uploads/2024/12/PM-IS-17526-1.pdf"
IS17790_MANUAL_URL = "https://www.bis.gov.in/wp-content/uploads/2024/12/PM-IS-17790-Dec-24.pdf"
TOY_MANUAL_URL = "https://www.bis.gov.in/wp-content/uploads/2020/08/PM-Toys-final-Aug2020.pdf"
IS10228_PORTAL_URL = "https://standards.bis.gov.in/website/standard-details"


def _source(document_ref: str, section: str, source_url: str) -> Dict[str, Any]:
    return {
        "documentRef": document_ref,
        "title": document_ref,
        "section": section,
        "sourceUrl": source_url,
    }


def _common_sources() -> List[Dict[str, Any]]:
    return [
        _source("BIS Scheme-I product list and QCO references", "Compulsory certification list", BIS_SCHEME_I_URL),
        _source("BIS Product Certification Process", "Scheme-I process and guidance", BIS_CERTIFICATION_PROCESS_URL),
        _source("BIS Product Certification FAQs", "Assessment, testing and licence process", BIS_CERTIFICATION_FAQ_URL),
        _source("BIS Know Your Standard", "Search by IS number or product keyword", BIS_KNOW_STANDARD_URL),
    ]


def _product_certification_steps() -> str:
    return (
        "*Typical manufacturer certification path (confirm the current product manual first):*\n"
        "1. Confirm the exact product scope, applicable IS edition, latest amendments, Quality Control Order (QCO), and any valid exemption.\n"
        "2. Open the current BIS product manual and Scheme of Inspection and Testing (SIT), where published. Use them to confirm product varieties, sampling, test requirements and the required documents.\n"
        "3. Ensure the factory's manufacturing controls, quality-control arrangements and required test facilities are ready; arrange product testing through a BIS-accepted route.\n"
        "4. Submit the appropriate application online through Manak Online and pay the current fees shown by BIS.\n"
        "5. BIS assesses the application and manufacturing/testing arrangements and evaluates product samples. Respond to document queries and any non-conformities.\n"
        "6. Apply the Standard Mark only after the relevant licence is granted, and continue to follow surveillance, marking and renewal requirements.\n\n"
        f"Application portal: {MANAKONLINE_URL}\n"
        f"Do not rely on old fee amounts or timelines; use the current BIS portal and product manual."
    )


def _water_bottle_guidance(answers: Dict[str, Any]) -> Dict[str, Any]:
    material = str(answers.get("material", "")).strip().casefold()
    insulation = str(answers.get("insulation", "")).strip().casefold()
    insulation_type = str(answers.get("insulation_type", "")).strip().casefold()
    activity = str(answers.get("business_activity", "")).strip().casefold()
    origin = str(answers.get("origin", "")).strip().casefold()
    help_needed = str(answers.get("help_needed", "")).strip().casefold()

    sources = _common_sources()
    metal_materials = ("stainless", "steel", "copper", "aluminium", "aluminum")
    is_metallic = any(word in material for word in metal_materials)
    is_stainless = "stainless" in material or "steel" in material
    is_vacuum = "vacuum" in insulation_type
    is_insulated = insulation == "insulated"

    if not is_metallic:
        content = (
            "*Product identified: potable water bottle*\n\n"
            f"Material provided: *{answers.get('material', 'not specified')}*.\n\n"
            "*I cannot responsibly assign IS 17803:2022 to this material.* The official BIS listing describes IS 17803:2022 as "
            "*Potable Water Bottles (Copper, Stainless Steel, Aluminium)*. It is a metallic-bottle standard; the source does not establish "
            "that it is the applicable standard for a plastic or glass bottle.\n\n"
            "*Next steps*\n"
            "1. Confirm the exact material and construction from the product specification.\n"
            "2. Search the current BIS Know Your Standard portal by product and material.\n"
            "3. Check the live Scheme-I/QCO list before concluding whether certification is compulsory.\n"
            "4. If the result is still unclear, ask BIS to confirm the applicable standard. I won't invent a number."
        )
        sources.extend([
            _source("Potable Water Bottles Quality Control Order, 2024", "Schedule: IS 17803:2022 covers copper, stainless steel and aluminium potable water bottles", POTABLE_BOTTLES_QCO_2024_URL),
        ])
        return {"content": content, "sources": sources, "insufficient_evidence": True}

    sources.extend([
        _source("Potable Water Bottles Quality Control Order, 2024", "IS 17803:2022 and product scope", POTABLE_BOTTLES_QCO_2024_URL),
        _source("BIS amendments to Quality Control Orders, February 2026", "Latest amendment affecting the Potable Water Bottles QCO", QCO_AMENDMENTS_FEB_2026_URL),
        _source("BIS LIMS: IS 17803:2022 test facilities", "Laboratory search by IS number", IS17803_LABS_URL),
    ])

    if is_stainless and is_insulated and is_vacuum:
        sources.extend([
            _source("BIS Product Manual: IS 17526:2021", "Domestic stainless-steel vacuum flask/bottle", IS17526_MANUAL_URL),
            _source("BIS Scheme-I product list: IS 17790:2022", "Insulated flask for domestic use", BIS_SCHEME_I_URL),
            _source("BIS Product Manual: IS 17790:2022", "Insulated flask for domestic use; scope, sampling and grouping guidelines", IS17790_MANUAL_URL),
        ])
        standards_text = (
            "1. *IS 17526:2021 — Domestic Stainless Steel Vacuum Flask/Bottle.* This is the more specific BIS listing to check for a domestic stainless-steel vacuum flask/bottle.\n"
            "2. *IS 17803:2022 — Potable Water Bottles (Copper, Stainless Steel, Aluminium).* BIS also lists this standard with the Potable Water Bottles QCO.\n"
            "3. *IS 17790:2022 — Insulated Flask for Domestic Use.* Check its product manual if the actual design falls within that product scope."
        )
        caveat = (
            "Because the answers describe a stainless-steel vacuum-insulated drinking bottle, the official BIS list contains more than one potentially relevant product category. "
            "Use the product manuals and obtain BIS confirmation of the exact scope/licence coverage; do not assume one standard automatically replaces the others."
        )
    elif is_stainless and is_insulated:
        sources.extend([
            _source("BIS Product Manual: IS 17526:2021", "Domestic stainless-steel vacuum flask/bottle; use if the design is a vacuum flask/bottle", IS17526_MANUAL_URL),
            _source("BIS Product Manual: IS 17790:2022", "Insulated flask for domestic use", IS17790_MANUAL_URL),
        ])
        standards_text = (
            "1. *IS 17803:2022 — Potable Water Bottles (Copper, Stainless Steel, Aluminium).* This is the listed metallic potable-bottle standard.\n"
            "2. *IS 17526:2021 — Domestic Stainless Steel Vacuum Flask/Bottle* may be relevant if this is a stainless-steel vacuum flask/bottle.\n"
            "3. *IS 17790:2022 — Insulated Flask for Domestic Use* may be relevant if the product falls within that manual's stated scope."
        )
        caveat = (
            "You selected 'insulated' but did not confirm vacuum construction. The exact design determines which product manual applies. "
            "Check the scope and amendments with BIS before selecting a single standard."
        )
    else:
        standards_text = (
            "*IS 17803:2022 — Potable Water Bottles (Copper, Stainless Steel, Aluminium).* "
            "This matches the official BIS product listing for metallic potable water bottles. "
            "You selected a metallic material and did not identify the bottle as insulated."
        )
        caveat = (
            "Confirm that the product is a potable water bottle within the standard's scope, and check the latest Scheme-I/QCO amendments and exemptions before concluding that a licence is required."
        )

    content = (
        f"*Product identified: {answers.get('product_name', 'water bottle')}*\n\n"
        "*Potentially relevant Indian Standard(s) from official BIS listings:*\n"
        f"{standards_text}\n\n"
        f"*Scope note:* {caveat}\n\n"
        "*Certification/QCO check*\n"
        "The current BIS Scheme-I list links IS 17803:2022 to the Potable Water Bottles Quality Control Order, 2024 and lists a further QCO amendment dated 13 February 2026. "
        "The 2026 amendment changes an exemption provision for certain Udyam-registered manufacturing enterprises subject to investment, turnover and Chartered Accountant certification conditions. "
        "Whether any exemption applies must be checked against the actual order and business facts; do not assume it.\n\n"
    )

    if "personal use" in activity:
        content += (
            "*For personal use:* You do not apply for a manufacturer's product-certification licence as a consumer. If the product claims an ISI mark, check the marking/licence details against official BIS records. "
            "For testing details, use the official product manual and the BIS laboratory search linked below.\n\n"
        )
    else:
        content += _product_certification_steps() + "\n\n"
        if "import" in activity or "imported" in origin:
            content += (
                "*Import note:* Before importing or selling, confirm the current QCO scope and import-related requirements with BIS. Do not assume that a domestic manufacturer's application route is interchangeable with an importer's obligations.\n\n"
            )

    if "test" in help_needed:
        content += (
            f"*Testing lookup:* BIS LIMS lists test facilities for IS 17803:2022 here: {IS17803_LABS_URL}\n"
            "The applicable product manual/SIT determines the specific tests and sampling plan.\n\n"
        )
    if "mark" in help_needed:
        content += "Use only the marking and licence scope authorized by BIS; verify the active licence and the standard edition before using a Standard Mark.\n\n"

    content += (
        "The standard number is a scope-based candidate, not a certificate or a guarantee of compliance. "
        "If the product design or QCO applicability is unclear, ask BIS to confirm the exact scope before testing or marking."
    )
    return {"content": content, "sources": sources, "insufficient_evidence": False}


def _school_bag_guidance(answers: Dict[str, Any]) -> Dict[str, Any]:
    activity = str(answers.get("business_activity", "")).strip().casefold()
    sources = _common_sources()
    sources.append(_source("BIS Standards Portal: IS 10228:1982", "Specification for school bag; check status, revisions and amendments", IS10228_PORTAL_URL))

    content = (
        "*Product identified: school bag/backpack*\n\n"
        "*IS 10228:1982 — Specification for school bag* is a relevant BIS standard to check for a school bag. The BIS Standards Portal currently labels certification for this standard as *voluntary*; this does not establish a general compulsory ISI-mark requirement for every backpack.\n\n"
        "If the product is a laptop, trekking, travel or other non-school backpack, do not assume IS 10228 covers it. Confirm the product scope and current standard status in BIS Know Your Standard and the live Scheme-I/QCO list.\n\n"
    )
    if "personal use" in activity:
        content += (
            "For a personal-use purchase, you normally do not apply for a manufacturer's BIS licence. If the seller claims a BIS mark, check the licence/marking details in official BIS records.\n\n"
        )
    else:
        content += (
            "Before starting certification, confirm whether the exact bag category is under compulsory certification or voluntary certification. If seeking voluntary certification, follow the current product-specific BIS process rather than assuming a QCO applies.\n\n"
            + _product_certification_steps()
            + "\n\n"
        )
    content += "This mapping is specifically for school bags and should not be generalized to all backpack types."
    return {"content": content, "sources": sources, "insufficient_evidence": False}


def _rc_toy_guidance(answers: Dict[str, Any]) -> Dict[str, Any]:
    vehicle_type = str(answers.get("vehicle_type", "")).strip().casefold()
    power_source = str(answers.get("power_source", "")).strip().casefold()
    activity = str(answers.get("business_activity", "")).strip().casefold()
    sources = _common_sources()
    sources.extend([
        _source("BIS Scheme-I product list: Toys QCO", "Non-electric toy IS 9873 series and electric toy IS 15644:2006; check current transitions", BIS_SCHEME_I_URL),
        _source("BIS Product Manual for Safety of Toys", "Test requirements must match the toy type and current applicable standard edition", TOY_MANUAL_URL),
    ])

    is_toy = "toy" in vehicle_type
    is_powered = any(word in power_source for word in ("rechargeable", "replaceable", "battery"))
    if not is_toy:
        content = (
            "*Product identified: RC/model vehicle*\n\n"
            "The answers do not establish whether this is a toy within the Toys Quality Control Order or an adult hobby/model vehicle. "
            "That classification affects which safety standards and regulatory route may apply, so I will not assign a mandatory IS number from the name alone.\n\n"
            "Confirm the intended market, age group, functions and current QCO scope in the official BIS listing or with BIS before choosing a standard."
        )
        return {"content": content, "sources": sources, "insufficient_evidence": True}

    content = (
        "*Product identified: remote-control car described as a toy*\n\n"
        "*Potentially relevant safety standards from the BIS Toys listing:*\n"
        "• *IS 15644:2006 — Safety of Electric Toys* is the primary electric-toy standard to check if this toy has functions that depend on electricity.\n"
        "• The *IS 9873 series* covers additional toy-safety aspects such as mechanical/physical properties, flammability and migration of certain elements where applicable.\n\n"
        "You selected a powered source: "
        f"*{answers.get('power_source', 'not specified')}*. "
        "The exact primary standard and additional parts depend on the product design, intended age group and scope of the standard.\n\n"
        "Important edition note: BIS's current standards portal lists a 2025 revision of IS 9873 (Part 1), and the Scheme-I page references the Toys QCO plus a 2026 transition order. "
        "Confirm the edition and transition provision currently applicable to your application before testing; do not rely only on an older downloaded checklist.\n\n"
    )
    if "personal use" in activity:
        content += (
            "For personal use, you do not apply for a manufacturer's product licence. Check whether the toy carries a genuine BIS mark and verify the licence/product scope with BIS.\n\n"
        )
    else:
        content += (
            "For a manufacturer or business, use the current Toys product manual to map the applicable tests, material/age-related requirements and sample plan; then use the online BIS application route, testing and factory assessment steps described in the current BIS guidance.\n\n"
            + _product_certification_steps()
            + "\n\n"
        )

    content += "This is a standards-screening result, not a final legal applicability decision or a confirmation that the product is compliant."
    return {"content": content, "sources": sources, "insufficient_evidence": False}


def build_product_standard_guidance(
    product_name: str,
    answers: Dict[str, Any],
    category: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Return source-linked guidance for questionnaire products in the curated registry.

    Return None for other products so the existing RAG assistant remains the
    fallback. A returned insufficient_evidence flag means the assistant could
    not responsibly identify a product-specific standard from this small registry.
    """
    name = " ".join((product_name or "").casefold().split())
    category_value = (category or "").casefold()

    if category_value == "water_bottle" or any(
        term in name for term in ("water bottle", "bottle", "flask", "thermos", "tumbler")
    ):
        merged = dict(answers or {})
        merged["product_name"] = product_name
        return _water_bottle_guidance(merged)

    if category_value == "backpack" or any(
        term in name for term in ("backpack", "back pack", "back bag", "school bag", "rucksack", "bag")
    ):
        merged = dict(answers or {})
        merged["product_name"] = product_name
        return _school_bag_guidance(merged)

    if category_value == "rc_car" or any(
        term in name for term in ("rc car", "remote control car", "toy car", "toy vehicle")
    ):
        merged = dict(answers or {})
        merged["product_name"] = product_name
        return _rc_toy_guidance(merged)

    return None
