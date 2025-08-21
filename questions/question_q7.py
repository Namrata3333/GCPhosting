# question_q7.py

import pandas as pd
import streamlit as st
import numpy as np
import altair as alt
from google.cloud import storage
import os
import json
from io import BytesIO
from dotenv import load_dotenv

load_dotenv('.env.template')

@st.cache_data
def load_data():
    try:
        service_account_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        bucket_name = os.getenv("GCS_BUCKET_NAME")

        if not service_account_json or not bucket_name:
            raise ValueError("Missing GOOGLE_APPLICATION_CREDENTIALS_JSON or GCS_BUCKET_NAME in environment.")
        
        client = storage.Client.from_service_account_info(json.loads(service_account_json))
        bucket = client.bucket(bucket_name)
        
        filepath = "LNTData.xlsx"
        blob = bucket.blob(filepath)
        
        if not blob.exists():
            raise FileNotFoundError(f"File not found in GCS: {filepath}")
            
        with BytesIO() as buffer:
            blob.download_to_file(buffer)
            buffer.seek(0)
            df = pd.read_excel(buffer)
        
        return df

    except Exception as e:
        st.error(f"Failed to load data from GCS: {e}")
        return pd.DataFrame()

def run(df, user_question):
    df = load_data()
    if df.empty:
        return

    df['Date_a'] = pd.to_datetime(df['Date_a'], errors='coerce')
    df = df.dropna(subset=['Date_a', 'FinalCustomerName', 'PSNo'])
    df['Month'] = df['Date_a'].dt.to_period('M').astype(str)

    tab1, tab2 = st.tabs(["Client-wise View", "Segment-wise View"])

    for tab, groupby_col in zip([tab1, tab2], ['FinalCustomerName', 'Segment']):
        with tab:
            monthly_headcount = df.groupby([groupby_col, 'Month'])['PSNo'].nunique().reset_index()
            monthly_headcount = monthly_headcount.rename(columns={'PSNo': 'FTE'})
            monthly_headcount['FTE'] = monthly_headcount['FTE'].round(1)

            fte_pivot = monthly_headcount.pivot(index='Month', columns=groupby_col, values='FTE').fillna(0)
            top_groups = fte_pivot.mean().sort_values(ascending=False).head(6).index
            chart_data = fte_pivot[top_groups]

            # Overall headcount change summary
            overall_fte = chart_data.sum(axis=1)
            if not overall_fte.empty:
                first_month = overall_fte.index[0]
                last_month = overall_fte.index[-1]
                fte_change = overall_fte.iloc[-1] - overall_fte.iloc[0]
                pct_change = (fte_change / overall_fte.iloc[0]) * 100 if overall_fte.iloc[0] else 0
                st.markdown(f"🔍 **Overall FTE (Headcount)** grew from **{overall_fte.iloc[0]:.1f}** "
                            f"in **{first_month}** to **{overall_fte.iloc[-1]:.1f}** in **{last_month}**, "
                            f"a change of **{fte_change:.1f} FTEs ({pct_change:.1f}%)**.")
            
            # Headcount breakdown
            total_count = df['PSNo'].nunique()
            if total_count > 0:
                billable_pct = df[df['Status'] == 'Billable']['PSNo'].nunique() / total_count * 100
                nonbillable_pct = df[df['Status'] == 'Non Billable']['PSNo'].nunique() / total_count * 100
                onsite_pct = df[df['Onsite/Offshore'] == 'Onsite']['PSNo'].nunique() / total_count * 100
                offshore_pct = df[df['Onsite/Offshore'] == 'Offshore']['PSNo'].nunique() / total_count * 100
                st.markdown(f"🔍 **Headcount Breakdown**: **{billable_pct:.1f}% Billable**, "
                            f"**{nonbillable_pct:.1f}% Non-Billable**, "
                            f"**{onsite_pct:.1f}% Onsite**, "
                            f"**{offshore_pct:.1f}% Offshore**.")

            col1, col2 = st.columns([1, 1])
            with col1:
                st.markdown(f"### 📋 MoM FTE per {groupby_col}")
                st.dataframe(
                    monthly_headcount.rename(columns={groupby_col: groupby_col, "FTE": "FTE (Headcount)"}),
                    use_container_width=True
                )

            with col2:
                st.markdown(f"### 📈 MoM FTE Trend (Top 6 by {groupby_col})")

                chart_data_reset = chart_data.reset_index().melt(
                    id_vars="Month", var_name=groupby_col, value_name="FTE"
                )

                trend_chart = (
                    alt.Chart(chart_data_reset)
                    .mark_line(point=True)
                    .encode(
                        x=alt.X("Month:T", title="Month"),
                        y=alt.Y("FTE:Q", title="FTE (Headcount)"),
                        color=alt.Color(f"{groupby_col}:N", legend=alt.Legend(title=groupby_col)),
                        tooltip=["Month", groupby_col, "FTE"]
                    )
                    .properties(width=500, height=450, title="Monthly FTE (Trend)")
                )

                st.altair_chart(trend_chart, use_container_width=True)

            st.markdown("### 📊 Headcount Composition by Month")

            # Billable vs Non-Billable
            stacked_data = df.groupby(['Month', 'Status'])['PSNo'].nunique().reset_index(name="Headcount")

            billable_chart = (
                alt.Chart(stacked_data)
                .mark_bar()
                .encode(
                    x=alt.X("Month:T", title="Month"),
                    y=alt.Y("Headcount:Q", title="Headcount"),
                    color=alt.Color("Status:N", legend=alt.Legend(title="Status")),
                    tooltip=["Month", "Status", "Headcount"]
                )
                .properties(width=300, height=450, title="Monthly Billable vs Non-Billable")
            )

            # Onsite vs Offshore
            stacked_data2 = df.groupby(['Month', 'Onsite/Offshore'])['PSNo'].nunique().reset_index(name="Headcount")

            onsite_chart = (
                alt.Chart(stacked_data2)
                .mark_bar()
                .encode(
                    x=alt.X("Month:T", title="Month"),
                    y=alt.Y("Headcount:Q", title="Headcount"),
                    color=alt.Color("Onsite/Offshore:N", legend=alt.Legend(title="Location")),
                    tooltip=["Month", "Onsite/Offshore", "Headcount"]
                )
                .properties(width=300, height=450, title="Monthly Onsite vs Offshore")
            )

            combined_chart = alt.hconcat(
            billable_chart,
            onsite_chart
            ).resolve_scale(
            y='independent'  # so their y-scales don’t clash
            ).configure_concat(
            spacing=400  # <-- add gap between the charts
            )

            st.altair_chart(combined_chart, use_container_width=True)