"""
app.py
------
Streamlit entry point for layout and UI
Run with: streamlit run app.py
"""

import streamlit as st

from processor import process_claims
from styles import (
    APP_CSS,
    HEADER_HTML,
    EMPTY_STATE_HTML,
    build_tier_cards,
    metric_card_html,
)

st.set_page_config(
    page_title="Signos | Claims Tier Analyzer",
    page_icon="🏥",
    layout="wide",
)
st.markdown(APP_CSS, unsafe_allow_html=True)

st.markdown(HEADER_HTML, unsafe_allow_html=True)

with st.expander("Tier Definitions", expanded=False):
    for card_html in build_tier_cards():
        st.markdown(card_html, unsafe_allow_html=True)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

uploaded = st.file_uploader(
    "Upload Claims File (.xlsx)",
    type=["xlsx", "xls"],
    label_visibility="collapsed",
)

if uploaded:
    with st.spinner("Analysing claims..."):
        display_df, raw_df, stats, errors, med_df, untiered_med_df = process_claims(uploaded.read())

    # Surface any non-fatal errors (e.g. unclassified ICD spend)
    for err in errors:
        st.markdown(
            f'<div style="background:rgba(245,158,11,.06); border:1px solid rgba(245,158,11,.2); '
            f'border-radius:8px; padding:10px 14px; color:#D97706; font-size:.83rem; margin-top:.75rem;">'
            f'{err}</div>',
            unsafe_allow_html=True,
        )

    if display_df is not None:

        # Metric cards
        st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
        match_pct = (stats["med_matched"] / stats["med_rows"] * 100) if stats["med_rows"] else 0

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(metric_card_html(
                "Grand Total",
                f"${stats['grand_total']:,.0f}",
                "Medical + RX",
            ), unsafe_allow_html=True)
        with c2:
            st.markdown(metric_card_html(
                "Medical Paid",
                f"${stats['grand_med']:,.0f}",
                f"{stats['med_rows']:,} claims · {stats['med_matched']:,} matched",
            ), unsafe_allow_html=True)
        with c3:
            st.markdown(metric_card_html(
                "RX Paid",
                f"${stats['grand_rx']:,.0f}",
                f"{stats['rx_rows']:,} RX claims",
            ), unsafe_allow_html=True)
        with c4:
            st.markdown(metric_card_html(
                "Tier Match Rate",
                f"{match_pct:.1f}%",
                "of medical claims",
            ), unsafe_allow_html=True)

        # Results table
        st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)
        st.markdown("#### Spend by Metabolic Tier")
        st.dataframe(display_df, width='stretch', hide_index=True)

        # CSV download
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button(
                label="⬇ Download Results as CSV",
                data=raw_df.to_csv(index=False).encode("utf-8"),
                file_name="claims_tier_analysis.csv",
                mime="text/csv"
            )
        with c2:
            st.download_button(
                label="⬇ Download Tiered Medical Claims",
                data = med_df.to_csv(index=False).encode("utf-8"),
                file_name = "claims_tiered.csv",
                mime="text/csv"
            )
        with c3:
            st.download_button(
                label="⬇ Download Untiered Medical Claims",
                data = untiered_med_df.to_csv(index=False).encode("utf-8"),
                file_name = "claims_untiered.csv",
                mime="text/csv"
            )

else:
    st.markdown(EMPTY_STATE_HTML, unsafe_allow_html=True)