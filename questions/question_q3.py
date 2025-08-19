# question_q3.py

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm
import numpy as np
import re

def run(df, user_question=None):
    import streamlit as st

    # Standardize column names
    df.columns = df.columns.str.strip()

    # Identify amount column
    amount_col = next((col for col in df.columns if col.lower() in ['amount in usd', 'amountinusd', 'amount']), None)
    if not amount_col:
        st.error("❌ Column not found: Amount in USD")
        return

    # Extract segment from user prompt if any
    selected_segment = None
    if user_question:
        segments = df['Segment'].dropna().unique().tolist()
        pattern = r'\b(?:' + '|'.join(map(re.escape, segments)) + r')\b'
        match = re.search(pattern, user_question, flags=re.IGNORECASE)
        if match:
            selected_segment = match.group(0)
            df = df[df['Segment'].str.lower() == selected_segment.lower()]
            st.markdown(f"📌 **Filtered Segment**: `{selected_segment}`")

    # Clean and convert Month
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    df = df.dropna(subset=['Month'])
    df['Quarter'] = df['Month'].dt.to_period('Q')

    # Get latest and previous quarter
    latest_month = df['Month'].max()
    latest_q = latest_month.to_period('Q')
    prev_q = (latest_month - pd.DateOffset(months=3)).to_period('Q')

    # ✅ Use updated C&B logic from Group Description
    cb_keywords = [
        "Onsite Salaries & Allowances", "Cost of Onsite TPCs/Retainers",
        "C&B Cost Offshore", "Professional Fee - Retainers/TPC"
    ]
    df_cb = df[df['Group Description'].isin(cb_keywords)]

    df_cost = df[df['Type'].str.lower() == 'cost']
    df_rev = df[df['Type'].str.lower() == 'revenue']

    cb_summary = df_cb.groupby(['Segment', 'Quarter'])[amount_col].sum().unstack(fill_value=0)
    cost_summary = df_cost.groupby(['Segment', 'Quarter'])[amount_col].sum().unstack(fill_value=0)
    rev_summary = df_rev.groupby(['Segment', 'Quarter'])[amount_col].sum().unstack(fill_value=0)

    for q in [prev_q, latest_q]:
        for summary in [cb_summary, cost_summary, rev_summary]:
            if q not in summary.columns:
                summary[q] = 0

    cb_summary = cb_summary[[prev_q, latest_q]] / 1e6
    cost_summary = cost_summary[[prev_q, latest_q]] / 1e6
    rev_summary = rev_summary[[prev_q, latest_q]] / 1e6

    # Compute total changes
    total_q1_cb = cb_summary[prev_q].sum()
    total_q2_cb = cb_summary[latest_q].sum()
    cb_change = ((total_q2_cb - total_q1_cb) / total_q1_cb) * 100 if total_q1_cb else 0

    total_q1_rev = rev_summary[prev_q].sum()
    total_q2_rev = rev_summary[latest_q].sum()
    rev_change = ((total_q2_rev - total_q1_rev) / total_q1_rev) * 100 if total_q1_rev else 0

    increased_segments = cb_summary[cb_summary[latest_q] > cb_summary[prev_q]].index.tolist()

    # Header insights
    st.markdown("### 📊 C&B Cost Insights")
    st.markdown(f"- 💰 **Overall C&B change** from {prev_q} to {latest_q}: **{cb_change:+.1f}%**")
    st.markdown(f"- ✅ **Overall Revenue change** from {prev_q} to {latest_q}: **{rev_change:+.1f}%**")
    if increased_segments:
        st.markdown(f"- 📈 **Segments with increased C&B**: {', '.join(increased_segments)}")

    # Prepare display table
    merged = pd.DataFrame(index=cb_summary.index)
    merged['C&B Q1'] = cb_summary[prev_q]
    merged['C&B Q2'] = cb_summary[latest_q]
    merged['Total Cost Q1'] = cost_summary[prev_q]
    merged['Total Cost Q2'] = cost_summary[latest_q]
    merged['Revenue Q1'] = rev_summary[prev_q]
    merged['Revenue Q2'] = rev_summary[latest_q]

    merged['% C&B Change'] = ((merged['C&B Q2'] - merged['C&B Q1']) / merged['C&B Q1'].replace(0, 1)) * 100
    merged['% Rev Change'] = ((merged['Revenue Q2'] - merged['Revenue Q1']) / merged['Revenue Q1'].replace(0, 1)) * 100
    merged['C&B vs Revenue Growth (pp)'] = merged['% C&B Change'] - merged['% Rev Change']

    # Add total row
    total_row = merged.sum(numeric_only=True)
    total_row.name = 'Total'
    merged = pd.concat([merged, total_row.to_frame().T])

    # Format
    def fmt(x): return f"{x:,.1f}"
    def fmt_pct(x): return f"{x:.2f}%" if pd.notnull(x) else "—"
    styled = merged.copy()
    styled[['C&B Q1', 'C&B Q2', 'Total Cost Q1', 'Total Cost Q2', 'Revenue Q1', 'Revenue Q2']] = \
        styled[['C&B Q1', 'C&B Q2', 'Total Cost Q1', 'Total Cost Q2', 'Revenue Q1', 'Revenue Q2']].applymap(fmt)
    styled[['% C&B Change', '% Rev Change', 'C&B vs Revenue Growth (pp)']] = \
        styled[['% C&B Change', '% Rev Change', 'C&B vs Revenue Growth (pp)']].applymap(fmt_pct)

    def highlight_mismatch(val):
        try:
            return 'background-color: #ffe6e6' if float(val.strip('%')) > 0 else ''
        except:
            return ''

    st.markdown("#### 🧾 C&B vs Revenue Comparison by Segment")
    st.dataframe(
        styled.style
            .applymap(highlight_mismatch, subset=['C&B vs Revenue Growth (pp)'])
            .set_properties(**{'white-space': 'normal', 'text-align': 'left'})
            .set_table_styles([{'selector': 'th', 'props': [('text-align', 'left')]}])
    )
