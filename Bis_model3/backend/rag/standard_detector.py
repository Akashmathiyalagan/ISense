import re
from typing import List, Dict, Any, Optional
from rag.models import CandidateStandard, DetectionResult

# Authoritative BIS Product Classification Catalog
KNOWN_BIS_STANDARDS_CATALOG: List[Dict[str, Any]] = [
    {
        "keywords": ["solar inverter", "photovoltaic inverter", "grid tie inverter", "solar pcu", "pv inverter"],
        "standard_code": "IS 16221 (Part 2) : 2015 / IS 16169 : 2014",
        "standard_title": "Safety of Power Converters for Photovoltaic Power Systems & Islanding Prevention",
        "category": "Solar & Renewable Equipment",
        "scheme": "Compulsory Registration Scheme (CRS) — MNRE Quality Order",
        "division": "Solar Energy Division (ETD 28)",
        "scope_summary": "Anti-Islanding trip time (< 2.0s), DC ground fault isolation, and conversion efficiency (> 95%).",
        "checklist": [
            "Anti-Islanding Test Report (IS 16169)",
            "DC Overvoltage & Ground Fault Isolation Report",
            "Manufacturer Factory Registration & QAP",
            "PCB Trace Clearance & Creepage Certificate"
        ]
    },
    {
        "keywords": ["ceiling fan", "bldc fan", "table fan", "pedestal fan", "exhaust fan", "electric fan"],
        "standard_code": "IS 374 : 2019",
        "standard_title": "Electric Ceiling Type Fans and Regulators — Safety & Performance Specification",
        "category": "Household Electrical Appliances",
        "scheme": "DPIIT Quality Control Order (QCO) / ISI Mark Scheme",
        "division": "Electrotechnical Division (ETD 32)",
        "scope_summary": "Air Delivery (min 210 m3/min for 1200mm sweep), Service Value (min 5.0 m3/min/W), and 1000N Shackle Safety Pin.",
        "checklist": [
            "Air Delivery Wind Tunnel Test Report",
            "Suspension Shackle Tensile Strength Test",
            "Motor Temperature Rise & Insulation Test",
            "BEE Star Rating Registration Dossier"
        ]
    },
    {
        "keywords": ["helmet", "two-wheeler helmet", "protective headgear", "motorcycle helmet", "crash helmet"],
        "standard_code": "IS 4151 : 2020",
        "standard_title": "Protective Helmets for Two-Wheeler Riders — Specification",
        "category": "Automotive & Road Safety",
        "scheme": "MoRTH Mandatory Helmet Order / ISI Mark Scheme (Scheme I)",
        "division": "Transport Engineering Division (TED 18)",
        "scope_summary": "Impact Deceleration Attenuation (< 300g), Dynamic Retention Elongation (< 25mm), and Visor Light Transmittance (>= 85%).",
        "checklist": [
            "Impact Deceleration Attenuation Test (Clause 9.1)",
            "Retention Dynamic Extension Test (Clause 9.2)",
            "Visor Optical Transmittance & Clarity Test",
            "Manufacturer Factory Audit & In-house Test Rig"
        ]
    },
    {
        "keywords": ["led bulb", "led lamp", "self-ballasted led", "led tube", "bulb", "lamp"],
        "standard_code": "IS 16102 (Part 1) : 2012",
        "standard_title": "Self-Ballasted LED-Lamps for General Lighting Services - Part 1: Safety Requirements",
        "category": "Electronics & Lighting",
        "scheme": "MeitY Compulsory Registration Scheme (CRS) & DPIIT QCO",
        "division": "Electrotechnical Division (ETD 23)",
        "scope_summary": "Cap torque retention (min 3.0 Nm), insulation resistance (min 4.0 MOhm at 500V DC), and photobiological safety.",
        "checklist": [
            "NABL Accredited Safety Test Report (IS 16102 Part 1)",
            "Photobiological Blue Light Safety Certificate",
            "Cap Torque Retention Test Certificate",
            "Quality Assurance Plan (QAP) for SMD Assembly"
        ]
    },
    {
        "keywords": ["lithium battery", "power bank", "li-ion cell", "secondary battery", "battery pack"],
        "standard_code": "IS 16046 (Part 2) : 2018",
        "standard_title": "Secondary Cells and Batteries Containing Alkaline or Non-Acid Electrolytes (Lithium Systems)",
        "category": "Electronics & IT Products",
        "scheme": "MeitY Compulsory Registration Scheme (CRS)",
        "division": "Batteries & Energy Storage (LITD 10)",
        "scope_summary": "Continuous charging endurance at constant voltage, external short circuit protection, and 130°C thermal abuse containment.",
        "checklist": [
            "External Short-Circuit Test Report",
            "Thermal Abuse & Drop Test (1.0m)",
            "Cell UN 38.3 Transportation Compliance",
            "Factory Quality Plan for Cell Balancing"
        ]
    },
    {
        "keywords": ["children toy", "toy for children", "toy intended for children", "educational toy", "plastic toy", "wooden toy", "electric toy", "non-electric toy"],
        "standard_code": "IS 9873 (Part 1) : 2018",
        "standard_title": "Safety of Toys Part 1: Safety Aspects Related to Mechanical and Physical Properties",
        "category": "Consumer Goods & Toys",
        "scheme": "Toys Quality Control Order / ISI Mark Scheme; scope and current edition must be checked for the exact product",
        "division": "Consumer Products Division (CPD 24)",
        "scope_summary": "Candidate only for products that fall within the applicable toy definition and scope. The current BIS Scheme-I listing shows IS 9873 (Part 1):2018; BIS has also published IS 9873 (Part 1):2025 and extended its implementation date to 22 March 2027. Check current QCO scope and adult-collector-model exclusions before assigning this standard.",
        "checklist": [
            "Mechanical Abuse & Small Parts Test Report",
            "Toxic Elements Migration Analysis (IS 9873 Part 3)",
            "Phthalate Content Chemical Lab Test",
            "Factory Quality Control & Tracking Protocol"
        ]
    },
    {
        "keywords": ["plug", "socket", "smart plug", "socket-outlet", "wall outlet"],
        "standard_code": "IS 1293 : 2019",
        "standard_title": "Plugs & Socket-Outlets up to 250V and Information Technology Safety",
        "category": "Smart Devices & IoT",
        "scheme": "DPIIT QCO & MeitY CRS Mandatory Order",
        "division": "Electrical Accessories (ETD 14)",
        "scope_summary": "Solid 6A/16A pin dimensional tolerances, 750°C Glow Wire flammability resistance, and 4.0mm creepage distance.",
        "checklist": [
            "Glow Wire Flammability Test (IS 1293 Clause 13)",
            "Socket Pin Insertion & Withdrawal Force Log",
            "Insulation Resistance under Damp Heat",
            "Manufacturer Factory Quality Plan"
        ]
    },
    {
        "keywords": ["power adapter", "smps", "fast charger", "usb charger", "mobile charger", "laptop adapter"],
        "standard_code": "IS 13252 (Part 1) : 2010",
        "standard_title": "Information Technology Equipment — Safety (General Requirements)",
        "category": "Power Supplies & Adapters",
        "scheme": "MeitY Compulsory Registration Scheme (CRS)",
        "division": "Electronics & IT Division (LITD 06)",
        "scope_summary": "Creepage distance (min 4.0mm primary-to-secondary), 3000V AC dielectric insulation withstand, and UL94 V-0 flame casing.",
        "checklist": [
            "Dielectric Hi-Pot Safety Test Report (3000V AC)",
            "Transformer Insulation Class & Thermal Rise Log",
            "UL94 V-0 Flammability Certificate of Casing",
            "NABL Accredited Laboratory Test Report"
        ]
    },
    {
        "keywords": ["ev charger", "electric vehicle charger", "evse", "wallbox", "charging station"],
        "standard_code": "IS 17017 (Part 1) : 2018",
        "standard_title": "Electric Vehicle Conductive Charging System — General Requirements",
        "category": "Electric Vehicles & Clean Mobility",
        "scheme": "Automotive Industry Quality Control Order / BIS Scheme",
        "division": "Electrotechnical Division (ETD 51)",
        "scope_summary": "Control pilot duty cycle interlock, 5000N drive-over mechanical crush test, and IP54 minimum ingress rating.",
        "checklist": [
            "Control Pilot Interlock Protocol Test Report",
            "Ingress Protection (IP54 / IP65) Test Report",
            "Connector Drive-Over Mechanical Resistance Log",
            "Dielectric Hi-Pot & RCD Trip Calibration Log"
        ]
    },
    {
        "keywords": ["drinking water", "packaged water", "mineral water", "bottled water"],
        "standard_code": "IS 14543 : 2016",
        "standard_title": "Packaged Drinking Water (Other Than Packaged Natural Mineral Water) — Specification",
        "category": "Food & Water Safety",
        "scheme": "Food Safety and Standards Authority (FSSAI) & BIS Mandatory ISI Mark",
        "division": "Food and Agriculture Division (FAD 14)",
        "scope_summary": "Total Dissolved Solids (TDS 75-500 mg/l), microbiological zero-tolerance (E. coli, coliforms), and heavy metal traces.",
        "checklist": [
            "Complete Microbiological & Pesticide Residue Lab Report",
            "Reverse Osmosis & UV Disinfection Verification Log",
            "In-house Testing Laboratory Equipment Calibration",
            "Groundwater Source Extraction NOC & Pollution Clearance"
        ]
    },
    {
        "keywords": ["cement", "portland cement", "opc 43", "opc 53", "ppc"],
        "standard_code": "IS 269 : 2015",
        "standard_title": "Ordinary Portland Cement — Specification",
        "category": "Construction & Civil Materials",
        "scheme": "DPIIT Mandatory Quality Control Order / ISI Mark Scheme",
        "division": "Civil Engineering Division (CED 02)",
        "scope_summary": "Compressive strength (min 43 MPa or 53 MPa at 28 days), initial setting time (min 30 min), and sound le chatelier (< 10mm).",
        "checklist": [
            "28-Day Compressive Strength Test Report",
            "Chemical Analysis (Loss on Ignition & Insoluble Residue)",
            "Setting Time & Soundness Autoclave Test Logs",
            "Plant Quarry Limestone Concession & Clinker Analysis"
        ]
    },
    {
        "keywords": ["tmt bar", "rebar", "reinforcing steel", "deformed steel bar", "steel reinforcement", "steel bar"],
        "standard_code": "IS 1786 : 2008",
        "standard_title": "High Strength Deformed Steel Bars and Wires for Concrete Reinforcement",
        "category": "Steel & Metallurgical Products",
        "scheme": "Ministry of Steel Mandatory QCO / ISI Mark Scheme",
        "division": "Metallurgical Engineering Division (MTD 04)",
        "scope_summary": "Yield strength (Fe 500D / Fe 550D min 500/550 MPa), elongation (min 16%), and bend/rebend ductility test.",
        "checklist": [
            "Tensile & Proof Stress Stress-Strain Curves",
            "Mandrel Bend and Rebend Crack Test Report",
            "Chemical Composition Spectrometer Log (C, S, P)",
            "Rolling Mill Billet Traceability Dossier"
        ]
    }
]

def extract_exact_standard_code(text: str) -> Optional[str]:
    """Extracts exact Indian Standard number from query or context string."""
    pattern = re.compile(r'\bIS\s*(\d{2,6}(?:\s*\([^\)]+\))?(?:\s*:\s*\d{4})?)\b', re.IGNORECASE)
    match = pattern.search(text)
    if match:
        raw_code = match.group(0).upper()
        # Normalize spacing
        return re.sub(r'\s+', ' ', raw_code)
    return None

def detect_bis_standard(product_name: str, category: str = "") -> Dict[str, Any]:
    """
    Refactored BIS standard detection:
    - Recognizes exact standard codes when present in query or product.
    - Matches product keywords strictly as candidate identification.
    - Handles ambiguous products and multi-category matches.
    - Rejects unsupported products without inventing a default standard.
    - Returns structured dictionary compatible with existing callers,
      including candidate classification, verification status, and ambiguity flags.
    """
    combined_query = f"{product_name} {category}".strip()
    query_lower = combined_query.lower()

    # 1. Exact standard code detection
    exact_code = extract_exact_standard_code(combined_query)
    if exact_code:
        # Match with catalog if possible
        for item in KNOWN_BIS_STANDARDS_CATALOG:
            item_code_clean = item["standard_code"].upper().replace(" ", "")
            exact_clean = exact_code.upper().replace(" ", "")
            if exact_clean in item_code_clean or item_code_clean in exact_clean:
                cand = dict(item)
                cand["is_verified"] = True
                cand["confidence"] = 0.98
                cand["match_type"] = "exact_code_match"
                return cand
        # Exact code mentioned that is not in hardcoded catalog
        return {
            "standard_code": exact_code,
            "standard_title": f"Indian Standard {exact_code}",
            "category": category or "Specified Technical Standard",
            "scheme": "BIS Scheme of Conformity Assessment",
            "division": "Bureau of Indian Standards Technical Directorate",
            "scope_summary": f"Scope and testing parameters under {exact_code}.",
            "checklist": [
                f"Accredited Laboratory Test Report ({exact_code})",
                "Technical Construction Dossier",
                "Factory Quality Assurance Manual"
            ],
            "keywords": [exact_code.lower()],
            "is_verified": False,
            "confidence": 0.90,
            "match_type": "exact_code_query"
        }

    # Avoid auto-classifying adult hobby/collector RC vehicles as children's toys.
    # Do not infer toy-QCO applicability from the phrase "RC car" alone.
    rc_vehicle_terms = ("rc car", "remote control car", "remote-controlled car", "rc vehicle", "model car")
    adult_model_terms = (
        "age 14+", "age 14 +", "14+ / hobby", "age 14 and over",
        "hobby use", "adult hobby", "adult collector", "scale model",
        "model / hobby vehicle", "model/hobby vehicle", "adult model",
    )
    if any(term in query_lower for term in rc_vehicle_terms) and any(term in query_lower for term in adult_model_terms):
        return {
            "standard_code": "No Verified Standard Identified",
            "standard_title": "RC / hobby vehicle — scope confirmation required",
            "category": "RC / Model Vehicles",
            "scheme": "Toy QCO applicability not established from the available product description",
            "division": "Bureau of Indian Standards",
            "scope_summary": (
                "The user's answers describe an adult hobby/model vehicle. Do not automatically assign children's-toy standards. "
                "Determine whether it is genuinely an adult collector's scale model, a product intended for children, or another regulated product. "
                "Confirm the current QCO and standard scope from official BIS sources before identifying a mandatory IS number."
            ),
            "checklist": [
                "Product datasheet and intended market/age group",
                "Official BIS scope confirmation for the specific RC/model vehicle",
                "Current QCO and applicable edition check"
            ],
            "keywords": list(rc_vehicle_terms),
            "is_verified": False,
            "confidence": 0.0,
            "match_type": "scope_confirmation_required",
            "is_supported": False,
            "suggested_questions": [
                "Is this model marketed and designed exclusively for adult collectors, or is it sold/intended as a children's toy?",
                "What voltage, battery type and radio-control functions are included?"
            ]
        }

    # 2. Check for ambiguous descriptions (e.g., 'charger' could be mobile charger IS 13252 or EV charger IS 17017)
    if re.search(r'\bcharger\b', query_lower) and not any(k in query_lower for k in ["ev", "electric vehicle", "mobile", "phone", "usb"]):
        ev_item = next(s for s in KNOWN_BIS_STANDARDS_CATALOG if "17017" in s["standard_code"])
        it_item = next(s for s in KNOWN_BIS_STANDARDS_CATALOG if "13252" in s["standard_code"])
        return {
            "standard_code": "Ambiguous: IS 13252 (Part 1) or IS 17017 (Part 1)",
            "standard_title": "Ambiguous Product Specification — Clarification Required",
            "category": "Power Supplies / Clean Mobility",
            "scheme": "Dependent on Product Type (CRS for Mobile/IT, Scheme I for EV)",
            "division": "Multiple Divisions (LITD 06 / ETD 51)",
            "scope_summary": "Query matches multiple regulatory categories: Mobile/IT power adapter vs Electric Vehicle conductive charger.",
            "checklist": [
                "Clarify whether product is a consumer mobile/IT charger or an EV conductive charging system",
                "Provide product voltage, wattage ratings, and intended application"
            ],
            "keywords": ["charger"],
            "is_verified": False,
            "confidence": 0.40,
            "is_ambiguous": True,
            "match_type": "ambiguous_candidate",
            "all_candidates": [it_item["standard_code"], ev_item["standard_code"]],
            "suggested_questions": [
                "Is this a mobile/IT power supply adapter (IS 13252) or an Electric Vehicle charging station (IS 17017)?"
            ]
        }

    # 3. Product classification candidate matching
    matched_candidates = []
    for item in KNOWN_BIS_STANDARDS_CATALOG:
        for kw in item["keywords"]:
            if re.search(r'\b' + re.escape(kw) + r'(?:s|es)?\b', query_lower):
                matched_candidates.append(item)
                break

    if matched_candidates:
        primary = dict(matched_candidates[0])
        primary["is_verified"] = False
        primary["confidence"] = 0.85 if len(matched_candidates) == 1 else 0.65
        primary["match_type"] = "candidate_keyword_match"
        if len(matched_candidates) > 1:
            primary["all_candidates"] = [c["standard_code"] for c in matched_candidates]
            primary["is_ambiguous"] = True
        return primary

    # 4. Fallback: UNSUPPORTED PRODUCT
    # Avoid inventing a fake standard or unconditionally returning IS 13252!
    return {
        "standard_code": "No Verified Standard Identified",
        "standard_title": "Standard Applicability Under Review",
        "category": category or "Unclassified Category",
        "scheme": "Subject to BIS Notification Review",
        "division": "Bureau of Indian Standards Central Advisory",
        "scope_summary": f"No official BIS mandatory standard was matched for '{product_name}'. Please verify technical parameters or consult official BIS Manak Online.",
        "checklist": [
            "Technical Data Sheet & Product Intended Use Description",
            "Bill of Materials & Construction Schematic",
            "Consult BIS Manak Online Product-to-Standard Matrix"
        ],
        "keywords": [],
        "is_verified": False,
        "confidence": 0.0,
        "match_type": "unsupported_product",
        "is_supported": False
    }

def detect_bis_standard_structured(query: str, category: str = "") -> DetectionResult:
    """Returns a structured DetectionResult Pydantic model for internal RAG pipeline."""
    raw = detect_bis_standard(query, category)
    cand = CandidateStandard(
        standard_code=raw["standard_code"],
        standard_title=raw["standard_title"],
        category=raw.get("category", ""),
        scheme=raw.get("scheme", ""),
        division=raw.get("division", ""),
        scope_summary=raw.get("scope_summary", ""),
        checklist=raw.get("checklist", []),
        keywords=raw.get("keywords", []),
        is_verified=raw.get("is_verified", False),
        confidence=raw.get("confidence", 0.0),
        match_type=raw.get("match_type", "unmatched")
    )
    is_supported = raw.get("is_supported", True) and raw["standard_code"] != "No Verified Standard Identified"
    return DetectionResult(
        query=query,
        candidate=cand if is_supported else None,
        is_exact_match=raw.get("match_type") == "exact_code_match",
        is_ambiguous=raw.get("is_ambiguous", False),
        is_supported=is_supported,
        suggested_questions=raw.get("suggested_questions", []),
        clarification_notice=raw.get("scope_summary") if not is_supported else None
    )
