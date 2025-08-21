# question_q7.py

import matplotlib
matplotlib.use('Agg') # Set the backend before any other matplotlib import or usage

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import seaborn as sns
from scipy.interpolate import make_interp_spline
import numpy as np
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

            overall_fte = chart_data.sum(axis=1)
            if not overall_fte.empty:
                first_month = overall_fte.index[0]
                last_month = overall_fte.index[-1]
                fte_change = overall_fte.iloc[-1] - overall_fte.iloc[0]
                pct_change = (fte_change / overall_fte.iloc[0]) * 100 if overall_fte.iloc[0] else 0
                st.markdown(f"🔍 **Overall FTE (Headcount)** grew from **{overall_fte.iloc[0]:.1f}** in **{first_month}** to **{overall_fte.iloc[-1]:.1f}** in **{last_month}**, a change of **{fte_change:.1f} FTEs ({pct_change:.1f}%)**.")
            
            total_count = df['PSNo'].nunique()
            if total_count > 0:
                billable_pct = df[df['Status'] == 'Billable']['PSNo'].nunique() / total_count * 100
                nonbillable_pct = df[df['Status'] == 'Non Billable']['PSNo'].nunique() / total_count * 100
                onsite_pct = df[df['Onsite/Offshore'] == 'Onsite']['PSNo'].nunique() / total_count * 100
                offshore_pct = df[df['Onsite/Offshore'] == 'Offshore']['PSNo'].nunique() / total_count * 100
                st.markdown(f"🔍 **Headcount Breakdown**: **{billable_pct:.1f}% Billable**, **{nonbillable_pct:.1f}% Non-Billable**, **{onsite_pct:.1f}% Onsite**, **{offshore_pct:.1f}% Offshore**.")

            col1, col2 = st.columns([1, 1])
            with col1:
                st.markdown(f"### 📋 MoM FTE per {groupby_col}")
                st.dataframe(monthly_headcount.rename(columns={groupby_col: groupby_col, "FTE": "FTE (Headcount)"}), use_container_width=True)

            with col2:
                st.markdown(f"### 📈 MoM FTE Trend (Top 6 by {groupby_col})")
                
                fig, ax = plt.subplots(figsize=(8, 5))
                for spine in ax.spines.values():
                    spine.set_color('#D3D3D3')
                    spine.set_linewidth(0.6)
                pastel_palette = sns.color_palette("pastel", len(top_groups))
                x = np.arange(len(chart_data.index))
                x_labels = chart_data.index
                for idx, val in enumerate(top_groups):
                    y = chart_data[val].values
                    if len(x) >= 4:
                        x_smooth = np.linspace(x.min(), x.max(), 300)
                        spline = make_interp_spline(x, y, k=3)
                        y_smooth = spline(x_smooth)
                        ax.plot(x_smooth, y_smooth, label=val, color=pastel_palette[idx], linewidth=2)
                    else:
                        ax.plot(x, y, label=val, color=pastel_palette[idx], linewidth=2)
                ax.set_title("Monthly FTE (Smoothed Trend)", fontsize=13)
                ax.set_xlabel("Month")
                ax.set_ylabel("FTE (Headcount)")
                ax.set_xticks(x)
                ax.set_xticklabels(x_labels, rotation=45)
                ax.legend(loc='upper left', fontsize=8)
                ax.grid(False)
                st.pyplot(fig)
                plt.close(fig) # Added this line to close the first figure

            st.markdown("### 📊 Headcount Composition by Month")
            
            stacked_data = df.groupby(['Month', 'Status'])['PSNo'].nunique().unstack().fillna(0)
            stacked_data2 = df.groupby(['Month', 'Onsite/Offshore'])['PSNo'].nunique().unstack().fillna(0)
            fig1, axs = plt.subplots(1, 2, figsize=(14, 5))
            for spine in axs[0].spines.values():
                spine.set_color('#D3D3D3')
                spine.set_linewidth(0.6)
            for spine in axs[1].spines.values():
                spine.set_color('#D3D3D3')
                spine.set_linewidth(0.6)
            stacked_data.plot(kind='bar', stacked=True, ax=axs[0], color=['#B0E57C', '#FFE0B2'], edgecolor='#D3D3D3')
            axs[0].set_title("Monthly Billable vs Non-Billable")
            axs[0].set_xlabel("Month")
            axs[0].set_ylabel("Headcount")
            axs[0].legend(loc='upper left', fontsize=8)
            axs[0].tick_params(axis='x', rotation=45)
            stacked_data2.plot(kind='bar', stacked=True, ax=axs[1], color=['#ADD8E6', '#FFDAB9'], edgecolor='#D3D3D3')
            axs[1].set_title("Monthly Onsite vs Offshore")
            axs[1].set_xlabel("Month")
            axs[1].set_ylabel("Headcount")
            axs[1].legend(loc='upper left', fontsize=8)
            axs[1].tick_params(axis='x', rotation=45)
            st.pyplot(fig1)
            plt.close(fig1) # It is better to use `plt.close(fig1)` instead of `plt.close('all')`