# ✅ FINAL Q1 — Margin % is (Revenue - Cost)/Revenue | Tabs by Segment, DU, BU, Customer | 1 Decimal Formatting
import pandas as pd
from dateutil.relativedelta import relativedelta
import streamlit as st
import re

pd.options.display.float_format = '{:,.1f}'.format  # Force 1 decimal display globally

def compute_margin(df, groupby_fields):
    df = df.copy()
    pivot = df.pivot_table(index=["Month"] + groupby_fields, columns="Type", values="Amount", aggfunc="sum").reset_index()
    pivot["Revenue"] = pivot.get("Revenue", 0)
    pivot["Cost"] = pivot.get("Cost", 0)
    return pivot

def extract_threshold(user_question, default_threshold=30):
    if user_question:
        patterns = [
            r"margin\s*<\s*(\d+)",
            r"less than\s*(\d+)",
            r"below\s*(\d+)",
            r"under\s*(\d+)",
            r"margin.*?(\d+)\s*%"
        ]
        for pattern in patterns:
            match = re.search(pattern, user_question.lower())
            if match:
                return float(match.group(1))
    return default_threshold

def extract_month(user_question):
    months = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12
    }
    if user_question:
        user_question = user_question.lower()
        for name, num in months.items():
            if name in user_question:
                year_match = re.search(rf"{name}\s*(\d{{4}})", user_question)
                if year_match:
                    year = int(year_match.group(1))
                    return pd.Timestamp(year=year, month=num, day=1)
    return None

def margin_analysis(df, group_field, threshold, target_month):
    group_name = group_field if isinstance(group_field, str) else " × ".join(group_field)
    df_margin = compute_margin(df, [group_field] if isinstance(group_field, str) else group_field)

    if target_month:
        filtered_data = df_margin[df_margin["Month"].dt.to_period("M") == target_month.to_period("M")]
        time_label = target_month.strftime("%B %Y")
    else:
        latest_month = df_margin["Month"].max()
        quarter_start = latest_month - relativedelta(months=2)
        filtered_data = df_margin[(df_margin["Month"] >= quarter_start) & (df_margin["Month"] <= latest_month)]
        time_label = "the last quarter"

    group_cols = [group_field] if isinstance(group_field, str) else group_field
    grouped = filtered_data.groupby(group_cols).agg({
        "Revenue": "sum",
        "Cost": "sum"
    }).reset_index()

    grouped["Margin %"] = ((grouped["Revenue"] - grouped["Cost"]) / grouped["Revenue"]) * 100
    grouped["Revenue (Million USD)"] = (grouped["Revenue"] / 1e6)
    grouped["Cost (Million USD)"] = (grouped["Cost"] / 1e6)

    filtered_df = grouped[(grouped["Margin %"] < threshold) & (grouped["Revenue (Million USD)"] > 0)]
    top_10 = filtered_df.sort_values("Margin %", ascending=False).head(10)

    total_entities = grouped.shape[0]
    low_margin_count = filtered_df.shape[0]
    proportion = (low_margin_count / total_entities * 100) if total_entities else 0

    st.markdown(
        f"🔍 **{group_name}** - For **{time_label}**, **{low_margin_count} entities** had average margin below "
        f"**{threshold}%**, which is **{proportion:.1f}%** of all **{total_entities} entities**."
    )

    if not top_10.empty:
        st.dataframe(
            top_10.reset_index(drop=True).style.format({
                "Revenue": "{:,.1f}",
                "Cost": "{:,.1f}",
                "Margin %": "{:,.1f}",
                "Revenue (Million USD)": "{:,.1f}",
                "Cost (Million USD)": "{:,.1f}"
            }),
            use_container_width=True
        )
    else:
        st.info("No records found below margin threshold.")

def run(df, user_question=None):
    df = df.copy()
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    df = df.dropna(subset=["Month"])
    df["Client"] = df.get("FinalCustomerName", "Unknown")
    df["Segment"] = df.get("Segment", "Unknown")
    df["BU"] = df.get("Exec DG", "Unknown")
    df["DU"] = df.get("Exec DU", "Unknown")

    threshold = extract_threshold(user_question)
    target_month = extract_month(user_question)

    tabs = st.tabs(["📋 By Client", "🚛 By Segment", "🏢 By BU", "🏭 By DU"])

    with tabs[0]:
        margin_analysis(df, "Client", threshold, target_month)

    with tabs[1]:
        margin_analysis(df, "Segment", threshold, target_month)

    with tabs[2]:
        margin_analysis(df, "BU", threshold, target_month)

    with tabs[3]:
        margin_analysis(df, "DU", threshold, target_month)
