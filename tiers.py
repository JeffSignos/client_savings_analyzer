"""
tiers.py
--------
ICD-10 tier definitions and matching logic.
"""

import re

# ── Tier Definitions ───────────────────────────────────────────────────────────
# IMPORTANT: Tier 3 is evaluated first so specific E11.2x-E11.6x diabetic
# complication codes are matched before the broad Tier 1 E11 prefix.

TIERS: dict[str, dict] = {
    "Tier 3 – Metabolic Complications": {
        "color": "#EF4444",
        "label": "Tier 3",
        "description": (
            "Serious outcomes from long-term unmanaged metabolic disease. "
            "Highest cost per member; largely preventable with early intervention."
        ),
        "icd_summary": (
            "I20–I25 (Ischemic Heart Disease), I50.x (Heart Failure), "
            "I60–I69 (Stroke/CVD), N18.x (CKD), "
            "E11.2x–E11.6x (Diabetic Complications), I70.2, I73.9 (PVD)"
        ),
        "rules": [
            "range:I20-I25",      # Ischemic Heart Disease
            "prefix:I50",         # Heart Failure
            "range:I60-I69",      # Stroke / Cerebrovascular
            "prefix:N18",         # Chronic Kidney Disease
            "range:E1120-E1169",  # Diabetic Complications E11.2x-E11.6x
            "prefix:I702",        # Peripheral Vascular Disease I70.2
            "exact:I739",         # Peripheral Vascular Disease I73.9
        ],
    },
    "Tier 1 – Direct Metabolic": {
        "color": "#0EA5E9",
        "label": "Tier 1",
        "description": (
            "Primary metabolic diagnoses Signos directly addresses through "
            "glucose management and weight loss."
        ),
        "icd_summary": (
            "E10.x (T1D), E11.x (T2D), E66.x (Obesity),"
            " R73.01–R73.09 (Prediabetes), R73.9 (Abnormal Glucose), E88.81 (Metabolic Syndrome), "
            "Z68.30–Z68.45 (BMI 30+), R63.5 (Abnormal Weight Gain)"
        ),
        "rules": [
            "prefix:E11",         # Type 2 Diabetes (non-complication codes)
            "prefix:E10",         # Type 1 Diabetes
            "prefix:E66",         # Obesity
            "range:R7301-R7309",  # Prediabetes R73.01-R73.09
            "exact:R739",         # Abnormal Glucose R73.9
            "exact:E8881",        # Metabolic Syndrome E88.81
            "range:Z6830-Z6845",  # BMI 30+ Z68.30-Z68.45
            "exact:R635",         # Abnormal Weight Gain R63.5
        ],
    },
    "Tier 2 – Metabolic Comorbidities": {
        "color": "#F59E0B",
        "label": "Tier 2",
        "description": (
            "Conditions strongly linked to metabolic dysfunction where weight loss "
            "and improved glucose control show downstream clinical benefit."
        ),
        "icd_summary": (
            "I10–I16 (Hypertension), E78.x (Dyslipidemia), "
            "G47.3x (Sleep Apnea), K76.0, K75.81 (NAFLD), E28.2 (PCOS)"
        ),
        "rules": [
            "range:I10-I16",  # Hypertension
            "prefix:E78",     # Dyslipidemia
            "prefix:G473",    # Sleep Apnea G47.3x
            "exact:K760",     # NAFLD K76.0
            "exact:K7581",    # NAFLD K75.81
            "exact:E282",     # PCOS E28.2
        ],
    },
}

# Display order for the output table (Tier 1 → 2 → 3)
TIER_ORDER: list[str] = [
    "Tier 1 – Direct Metabolic",
    "Tier 2 – Metabolic Comorbidities",
    "Tier 3 – Metabolic Complications",
]

NO_TIER = "Unclassified / Not Metabolic"


# ── Matching helpers ───────────────────────────────────────────────────────────

def _norm(code: str) -> str:
    """Strip dots/spaces and uppercase for consistent comparison."""
    return re.sub(r"[^A-Z0-9]", "", code.upper())


def _in_range(code: str, lo: str, hi: str) -> bool:
    """Lexicographic range check on normalised ICD codes."""
    n = max(len(lo), len(hi), len(code))
    return lo.ljust(n, "0") <= code.ljust(n, "0") <= hi.ljust(n, "9")


def assign_tier(icd_raw: str) -> str:
    """
    Return the tier name for a single ICD code string.
    Returns NO_TIER if no match is found.
    """
    if not isinstance(icd_raw, str) or not icd_raw.strip():
        return NO_TIER
    code = _norm(icd_raw)
    for tier_name, meta in TIERS.items():
        for rule in meta["rules"]:
            kind, value = rule.split(":", 1)
            if kind == "exact" and code == _norm(value):
                return tier_name
            elif kind == "prefix" and code.startswith(_norm(value)):
                return tier_name
            elif kind == "range":
                lo, hi = value.split("-", 1)
                if _in_range(code, _norm(lo), _norm(hi)):
                    return tier_name
    return NO_TIER


def best_tier_for_row(icd_values: list) -> str:
    """
    Given multiple ICD code values for a single claim row, return the
    highest-priority (lowest TIER_ORDER index) tier matched across all codes.
    """
    matched = [
        assign_tier(str(v)) for v in icd_values
        if v is not None and str(v).strip() not in ("", "nan", "None")
    ]
    matched = [t for t in matched if t in TIER_ORDER]
    if not matched:
        return NO_TIER
    return sorted(matched, key=lambda t: TIER_ORDER.index(t))[0]