"""
processor.py
------------
Reads the claims Excel workbook, assigns ICD tiers, and builds the
summary dataframe. No streamlit imports — usable from any frontend or CLI.
"""

import io
import pandas as pd

from tiers import TIER_ORDER, NO_TIER, best_tier_for_row

MED_PAY_CANDIDATES = ["billed_amount", "allowed_amount", "paid_amount", "total_paid"]
RX_PAY_CANDIDATES  = ["plan_paid_amount", "paid_amount", "billed_amount", "allowed_amount"]
ICD_CANDIDATES = ["icd_code", "primary_icd_code", "secondary_icd_code"]
MEDICAL_TAB_CANDIDATES = ['med', 'med_claims', 'medical', 'medical_claims', 'sheet_1', 'sheet1']
RX_TAB_CANDIDATES = ['rx', 'rx_claims', 'sheet_2', 'sheet2']

def _find_tab(excel_file, candidates):
    sheet_names = excel_file.sheet_names
    sheet_names = [name.lower().replace(" ", "_") for name in sheet_names]
    for i in candidates:
        if i in sheet_names:
            print(sheet_names.index(i))
            return sheet_names.index(i)
    #TODO error for no index found

def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def _find_pay_col(df, candidates):
    return next((c for c in candidates if c in df.columns), None)


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0)

def process_claims(file_bytes):
    """
    Parse a claims workbook and return a tier summary.

    Parameters
    ----------
    file_bytes : bytes
        Raw bytes of the uploaded .xlsx file.

    Returns
    -------
    display_df : pd.DataFrame 
        Currency-formatted dataframe for on-screen display.
    raw_df : pd.DataFrame 
        Numeric dataframe suitable for CSV export.
    stats : dict
        Summary statistics for the metric cards.
    errors : list
        Any non-fatal error messages to surface in the UI.
    """
    errors = []
    buf = io.BytesIO(file_bytes)
    med_index = _find_tab(pd.ExcelFile(buf), MEDICAL_TAB_CANDIDATES)
    rx_index = _find_tab(pd.ExcelFile(buf), RX_TAB_CANDIDATES)
 
    try:
        med = _normalise_columns(pd.read_excel(buf, sheet_name=med_index))
    except Exception as e:
        return None, None, {}, [f"Could not read 'Medical Claims' sheet: {e}"]

    med_pay_col = _find_pay_col(med, MED_PAY_CANDIDATES)
    if not med_pay_col:
        return None, None, {}, ["No recognisable paid-amount column found in Medical Claims."]

    icd_cols = [c for c in med.columns if "icd_code" in c]
    if not icd_cols:
        return None, None, {}, ["No ICD code columns found in Medical Claims."]

    med[med_pay_col] = _to_numeric(med[med_pay_col])
    med["_tier"] = med.apply(
        lambda r: best_tier_for_row([r[c] for c in icd_cols]), axis=1
    )
    med_df = med[med["_tier"].isin(TIER_ORDER)]
    med_by_tier = med_df.groupby("_tier")[med_pay_col].sum()
    untiered_med_df = med.loc[med["_tier"] == NO_TIER]
    med_unclass_amt = float(med.loc[med["_tier"] == NO_TIER, med_pay_col].sum())
    med_matched_rows = int((med["_tier"] != NO_TIER).sum())
    total_med_rows = len(med)

    if med_unclass_amt > 0:
        errors.append(
            f"${med_unclass_amt:,.2f} in medical claims could not be matched "
            f"to a metabolic tier (unclassified ICD codes)."
        )

    buf.seek(0)
    try:
        rx = _normalise_columns(pd.read_excel(buf, sheet_name=rx_index))
        rx = rx[rx['therapeutic_class'].str.contains('ANTIHYPERGLYCEMICS|ANTI-OBESITY DRUGS', na=False)]
        rx_pay_col = _find_pay_col(rx, RX_PAY_CANDIDATES)
        rx[rx_pay_col] = _to_numeric(rx[rx_pay_col])
        rx_total = float(rx[rx_pay_col].sum()) if rx_pay_col else 0.0
        rx_rows  = len(rx)
    except Exception:
        rx_total, rx_rows = 0.0, 0

    rows = []
    for tier in TIER_ORDER:
        med_paid = float(med_by_tier.get(tier, 0.0))
        rows.append({
            "Tier": tier,
            "Amount Paid": med_paid,
        })

    rows.append({
        "Tier":        "RX Claims",
        "Amount Paid": rx_total,
    })

    grand_total = sum(r["Amount Paid"] for r in rows)
    rows.append({
        "Tier":        "GRAND TOTAL",
        "Amount Paid": grand_total,
    })

    raw_df = pd.DataFrame(rows)

    display_df = raw_df.copy()
    display_df["Amount Paid"] = display_df["Amount Paid"].apply(lambda x: f"${x:,.2f}")

    grand_med = sum(r["Amount Paid"] for r in rows if r["Tier"] not in ("RX Claims", "GRAND TOTAL"))
    stats = {
        "med_rows":    total_med_rows,
        "med_matched": med_matched_rows,
        "rx_rows":     rx_rows,
        "grand_med":   grand_med,
        "grand_rx":    rx_total,
        "grand_total": grand_med + rx_total,
        "unclass_amt": med_unclass_amt,
    }

    return display_df, raw_df, stats, errors, med_df, untiered_med_df