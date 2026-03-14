# Claims Tier Analyzer

A Streamlit web app that ingests a medical and RX claims workbook, classifies
records by ICD-10 code into three metabolic tiers, and summarises total paid
amounts per tier.

---

## Tiers

| Tier | Label | Description | Example Codes |
|------|-------|-------------|---------------|
| **Tier 1** | Direct Metabolic | Primary metabolic diagnoses Signos directly addresses through glucose management and weight loss | E11.x (T2D), E66.x (Obesity), R73.01–R73.09 (Prediabetes), E88.81 (Metabolic Syndrome), Z68.30–Z68.45 (BMI 30+) |
| **Tier 2** | Metabolic Comorbidities | Conditions strongly linked to metabolic dysfunction where weight loss and improved glucose control show downstream clinical benefit | I10–I16 (Hypertension), E78.x (Dyslipidemia), G47.3x (Sleep Apnea), K76.0 / K75.81 (NAFLD), E28.2 (PCOS) |
| **Tier 3** | Metabolic Complications | Serious outcomes from long-term unmanaged metabolic disease; highest cost per member and largely preventable with early intervention | I20–I25 (Ischemic Heart Disease), I50.x (Heart Failure), I60–I69 (Stroke/CVD), N18.x (CKD), E11.2x–E11.6x (Diabetic Complications), I70.2 / I73.9 (PVD) |

---

## Project Structure

```
claims_app/
├── app.py            # Streamlit entry point — layout and UI only
├── processor.py      # File ingestion and pandas processing
├── tiers.py          # ICD-10 tier definitions and matching logic
├── styles.py         # CSS and HTML constants
└── test_tiers.py     # Standalone tests for ICD matching (no Streamlit required)
```

Each module has a single responsibility. `tiers.py` and `processor.py` have no
Streamlit dependency, so they can be imported and tested independently or
reused in a different frontend (e.g. FastAPI, CLI).

---

## Requirements

- Python 3.10+
- See dependencies below

---

## Setup

```bash
# 1. Clone or download the project
cd claims_app

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Mac / Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Running the App

```bash
streamlit run app.py
```

The app will open automatically at `http://localhost:8501`.

---

## Running the Tests

The test suite validates all ICD matching logic and requires no Streamlit
instance — run it directly with Python:

```bash
python test_tiers.py
```

Expected output:

```
✅ E11.9       T2D unspecified
✅ E11.9       T2D no complications
...
──────────────────────────────────────────────────
  35 passed · 0 failed out of 35 tests

✅ best_tier_for_row(['I10', 'E11.40', 'Z99.9'])
```

---

## Input File Format

The app expects an `.xlsx` workbook with two sheets:

### Medical Claims

| Column | Description |
|--------|-------------|
| `member_id` | Member identifier |
| `service_date` | Date of service |
| `icd_code_primary` | Primary ICD-10 diagnosis code |
| `icd_description_primary` | Description of primary diagnosis |
| `icd_code_Secondary` | Secondary ICD-10 code (optional) |
| `icd_description_secondary` | Description of secondary diagnosis |
| `icd_code_tertiary` | Tertiary ICD-10 code (optional) |
| `icd_description_tertiary` | Description of tertiary diagnosis |
| `billed_amount` | Amount billed (used as paid amount) |
| `allowed_amount` | Allowed amount (fallback if billed_amount absent) |

### RX Claims

| Column | Description |
|--------|-------------|
| `member_id` | Member identifier |
| `paid_date` | Date paid |
| `drug_name` | Drug name |
| `therapeutic_class` | Drug therapeutic class |
| `plan_paid_amount` | Amount paid by plan |
| `member_paid_amount` | Amount paid by member |

> The app will also accept variations like `paid_amount` or `total_paid` if
> the exact column names above are not present.

---

## Output

The app displays a summary table with one row per tier:

| Column | Description |
|--------|-------------|
| Tier | Tier name |
| Medical Claims Paid | Sum of `billed_amount` for claims matching this tier |
| RX Claims Paid | RX total distributed pro-rata by each tier's medical spend share |
| Subtotal | Medical + RX for this tier |

A **Grand Total** row is appended at the bottom. The full results can be
downloaded as a CSV using the button below the table.

> **Note on RX allocation:** The RX Claims tab contains no ICD codes, so RX
> spend cannot be directly attributed to a tier. Instead, the total RX spend
> is distributed across tiers in proportion to each tier's share of medical
> spend. If your RX data includes a member ID that can be joined back to
> medical claims, per-tier RX attribution can be made exact — open an issue
> or update `processor.py` accordingly.

---

## ICD Matching Logic

Matching is handled in `tiers.py`. Each tier defines a list of rules evaluated
in order:

| Rule type | Syntax | Behaviour |
|-----------|--------|-----------|
| `exact` | `exact:E8881` | Matches only that normalised code |
| `prefix` | `prefix:E11` | Matches any code starting with E11 |
| `range` | `range:I20-I25` | Lexicographic range match on normalised codes |

Codes are normalised before matching (dots and spaces stripped, uppercased),
so `E11.9`, `e11.9`, and `E119` all resolve identically.

**Multi-code rows:** When a claim has codes across multiple tiers, it is
assigned to the **lowest-numbered tier** (Tier 1 takes priority over Tier 2,
which takes priority over Tier 3). To invert this so the most severe tier
wins, reverse the sort in `best_tier_for_row()` in `tiers.py`.

**Tier evaluation order:** Tier 3's specific `E11.2x–E11.6x` diabetic
complication range is evaluated *before* Tier 1's broad `E11` prefix to
ensure complication codes are not misclassified as uncomplicated T2D.

---

## Extending the App

**Adding a new ICD code to a tier** — edit the `rules` list for that tier
in `tiers.py`, then run `test_tiers.py` to verify no regressions.

**Adding a new tier** — add an entry to the `TIERS` dict in `tiers.py` and
append the tier name to `TIER_ORDER`. Add a corresponding card in `styles.py`
and a CSS class. No changes needed in `processor.py` or `app.py`.

**Changing the paid amount column** — update `MED_PAY_CANDIDATES` or
`RX_PAY_CANDIDATES` at the top of `processor.py`.

**Using the processor outside Streamlit** — `processor.py` can be imported
into any Python script:

```python
from processor import process_claims

with open("claims.xlsx", "rb") as f:
    display_df, raw_df, stats, errors = process_claims(f.read())
```