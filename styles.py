"""
styles.py
---------
CSS and HTML constants for the Streamlit UI.
"""

from tiers import TIERS, TIER_ORDER

# ── Global CSS ─────────────────────────────────────────────────────────────────

APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap');

/* ── Tier legend cards ── */
.tier-card { border-radius: 8px; padding: 12px 16px; margin-bottom: 8px; border-left: 3px solid; }
.tier-label { font-weight: 600; font-size: .8rem; letter-spacing: .06em; text-transform: uppercase; }
.tier-codes { color: #94A3B8; font-size: .82rem; margin-top: 3px; line-height: 1.55; }

/* ── Metric cards ── */
.metric-card {
    background: #111827; border: 1px solid #1E2D42; border-radius: 10px;
    padding: 16px 20px; text-align: center;
}
.metric-label { color: #64748B; font-size: .75rem; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; }
.metric-value { color: #F1F5F9; font-size: 1.45rem; font-weight: 700; margin-top: 4px; }
.metric-sub   { color: #4B5563; font-size: .75rem; margin-top: 2px; }

/* ── Warning / note ── */
.note {
    background: rgba(245,158,11,.06); border: 1px solid rgba(245,158,11,.2);
    border-radius: 8px; padding: 10px 14px; color: #D97706;
    font-size: .83rem; margin-top: .75rem;
}

/* ── Streamlit component overrides ── */
[data-testid="stFileUploader"] > div {
    background: #111827 !important;
    border: 1.5px dashed #1F2D45 !important;
    border-radius: 10px !important;
}
div[data-testid="stExpander"] {
    background: #111827 !important;
    border: 1px solid #1E2D42 !important;
    border-radius: 10px !important;
}
.stDownloadButton > button {
    background: linear-gradient(135deg, #0EA5E9, #6366F1) !important;
    color: #fff !important; border: none !important;
    font-weight: 600 !important; border-radius: 8px !important;
    padding: 0.5rem 1.4rem !important;
}
.stDownloadButton > button:hover { filter: brightness(1.1) !important; }
</style>
"""

# ── Header HTML ────────────────────────────────────────────────────────────────

HEADER_HTML = """
<div style="padding-bottom:1.2rem; margin-bottom:1.5rem; border-bottom:1px solid #1E2D42;">
  <div style="display:flex; align-items:baseline; gap:14px; flex-wrap:wrap;">
    <span style="font-family:'DM Serif Display',serif; font-size:1.85rem; color:#F1F5F9; letter-spacing:-.4px;">
      Claims Tier Analyzer
    </span>
    <span style="font-size:.72rem; font-weight:700; letter-spacing:.15em; text-transform:uppercase;
                 background:linear-gradient(135deg,#0EA5E9,#6366F1);
                 -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
      by Signos
    </span>
  </div>
  <div style="color:#4B5563; font-size:.88rem; margin-top:5px;">
    Upload a claims workbook to measure medical &amp; RX spend across three metabolic tiers.
  </div>
</div>
"""

# ── Empty state HTML ───────────────────────────────────────────────────────────

EMPTY_STATE_HTML = """
<div style="background:#111827; border:1.5px dashed #1F2D45; border-radius:10px;
            padding:2.5rem; text-align:center; color:#4B5563; margin-top:.5rem;">
  <div style="font-size:2rem; margin-bottom:.5rem;">📂</div>
  <div style="font-weight:500; color:#64748B;">Drop your claims .xlsx file above to begin</div>
  <div style="font-size:.82rem; margin-top:.4rem;">
    Requires a workbook with
    <strong style="color:#4B5563;">Medical Claims</strong> and
    <strong style="color:#4B5563;">RX Claims</strong> tabs
  </div>
</div>
"""

# ── RX pro-rata note ───────────────────────────────────────────────────────────

RX_NOTE_HTML = """
<div style="color:#374151; font-size:.78rem; margin-top:10px;">
  Note: RX claims carry no ICD codes — RX totals are distributed across tiers
  pro-rata based on each tier's share of medical spend.
</div>
"""


# ── Tier legend cards (generated from TIERS so they stay in sync) ──────────────

def build_tier_cards() -> list[str]:
    """
    Return each tier card as a separate HTML string.
    Streamlit only renders unsafe_allow_html correctly for the first
    st.markdown call inside an expander — so callers should iterate
    this list and call st.markdown once per item.
    """
    color_map = {
        "Tier 1 – Direct Metabolic":        ("#0EA5E9", "rgba(14,165,233,.07)"),
        "Tier 2 – Metabolic Comorbidities":  ("#F59E0B", "rgba(245,158,11,.07)"),
        "Tier 3 – Metabolic Complications":  ("#EF4444", "rgba(239,68,68,.07)"),
    }
    cards = []
    for tier_name in TIER_ORDER:
        meta = TIERS[tier_name]
        border_color, bg_color = color_map[tier_name]
        cards.append(
            f'<div style="background:{bg_color}; border-left:3px solid {border_color}; '
            f'border-radius:8px; padding:12px 16px; margin-bottom:8px;">'
            f'<div style="color:{border_color}; font-weight:600; font-size:.8rem; '
            f'letter-spacing:.06em; text-transform:uppercase;">{tier_name}</div>'
            f'<div style="color:#94A3B8; font-size:.82rem; margin-top:3px; line-height:1.55;">'
            f'{meta["icd_summary"]}</div></div>'
        )

    # RX note as its own entry so it also renders correctly
    cards.append(RX_NOTE_HTML.strip())
    return cards


# ── Metric card HTML helper (inline styles only) ──────────────────────────────

def metric_card_html(label: str, value: str, sub: str = "") -> str:
    return f"""
    <div style="background:#111827; border:1px solid #1E2D42; border-radius:10px;
                padding:16px 20px; text-align:center;">
      <div style="color:#64748B; font-size:.75rem; font-weight:600;
                  letter-spacing:.08em; text-transform:uppercase;">{label}</div>
      <div style="color:#F1F5F9; font-size:1.45rem; font-weight:700;
                  margin-top:4px;">{value}</div>
      <div style="color:#4B5563; font-size:.75rem; margin-top:2px;">{sub}</div>
    </div>"""