import pandas as pd
import streamlit as st
from google.cloud import storage
import os
import json
from io import BytesIO
from dotenv import load_dotenv


load_dotenv('.env.template')
def run(prompt=None):
    st.title("Utilization % Trends")

    @st.cache_data
    def load_data():
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
        df['Date_a'] = pd.to_datetime(df['Date_a'], errors='coerce')
        df['Month_Year'] = df['Date_a'].dt.strftime('%b')
        df['Quarter'] = df['Date_a'].dt.to_period("Q").astype(str)
        df['Year'] = df['Date_a'].dt.year
        df['NetAvailableHours'] = pd.to_numeric(df['NetAvailableHours'], errors='coerce')
        df['TotalBillableHours'] = pd.to_numeric(df['TotalBillableHours'], errors='coerce')
        return df

    df = load_data()

    # Fix month order
    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    df['Month_Year'] = pd.Categorical(df['Month_Year'], categories=month_order, ordered=True)

    # Sidebar filters
    st.sidebar.header("Filters")
    segments = st.sidebar.multiselect("Segment:", df['Segment'].dropna().unique())
    bus = st.sidebar.multiselect("BU:", df['BusinessUnit'].dropna().unique())
    dus = st.sidebar.multiselect("DU:", df['Delivery_Unit'].dropna().unique())
    quarters = st.sidebar.multiselect("Quarter:", df['Quarter'].dropna().unique())

    df_filtered = df.copy()
    if segments:
        df_filtered = df_filtered[df_filtered['Segment'].isin(segments)]
    if bus:
        df_filtered = df_filtered[df_filtered['BusinessUnit'].isin(bus)]
    if dus:
        df_filtered = df_filtered[df_filtered['Delivery_Unit'].isin(dus)]
    if quarters:
        df_filtered = df_filtered[df_filtered['Quarter'].isin(quarters)]

    def show_tables(df, group_cols, level_name):
        st.subheader(f"Utilization % by {level_name}")

        # Group by and calculate correct UT%
        agg = df.groupby(group_cols + ['Month_Year'])[['TotalBillableHours', 'NetAvailableHours']].sum().reset_index()
        agg['UT%'] = (agg['TotalBillableHours'] / agg['NetAvailableHours']) * 100
        ut_df = agg.pivot_table(index=group_cols, columns='Month_Year', values='UT%').fillna(0)

        # Weighted average for Total row
        billable_totals = df.groupby(['Month_Year'])['TotalBillableHours'].sum()
        available_totals = df.groupby(['Month_Year'])['NetAvailableHours'].sum()
        total_ut = (billable_totals / available_totals * 100).round(2)
        ut_df.loc['Total'] = total_ut

        st.dataframe(ut_df.style.format("{:.2f}"))

        # Side-by-side raw data tables
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("🔷 **TotalBillableHours**")
            b_pivot = df.groupby(group_cols + ['Month_Year'])['TotalBillableHours'].sum().reset_index()
            b_df = b_pivot.pivot_table(index=group_cols, columns='Month_Year', values='TotalBillableHours').fillna(0)
            b_df.loc['Total'] = b_df.sum(numeric_only=True)
            st.dataframe(b_df.style.format("{:,.0f}"))

        with col2:
            st.markdown("🔷 **NetAvailableHours**")
            a_pivot = df.groupby(group_cols + ['Month_Year'])['NetAvailableHours'].sum().reset_index()
            a_df = a_pivot.pivot_table(index=group_cols, columns='Month_Year', values='NetAvailableHours').fillna(0)
            a_df.loc['Total'] = a_df.sum(numeric_only=True)
            st.dataframe(a_df.style.format("{:,.0f}"))

    # Tabs: BU, DU, Segment
    tabs = st.tabs(["🏢 BU Level", "🏭 DU Level", "📊 Segment Level"])

    with tabs[0]:
        show_tables(df_filtered, ['BusinessUnit'], "BU")

    with tabs[1]:
        show_tables(df_filtered, ['Delivery_Unit'], "DU")

    with tabs[2]:
        show_tables(df_filtered, ['Segment'], "Segment")
