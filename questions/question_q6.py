import streamlit as st
import pandas as pd
from google.cloud import storage
import os
import json
from io import BytesIO
from dotenv import load_dotenv


load_dotenv('.env.template')
@st.cache_data
def load_data():
    try:
        # Initialize GCS client
        service_account_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        bucket_name = os.getenv("GCS_BUCKET_NAME")

        if not service_account_json or not bucket_name:
            raise ValueError("Missing GOOGLE_APPLICATION_CREDENTIALS_JSON or GCS_BUCKET_NAME in environment.")
        
        client = storage.Client.from_service_account_info(json.loads(service_account_json))
        bucket = client.bucket(bucket_name)

        # File paths within GCS
        revenue_file = "revenue.csv"
        hours_file = "netavailablehours.csv"

        # Load revenue data
        with BytesIO() as buffer:
            blob = bucket.blob(revenue_file)
            if not blob.exists():
                raise FileNotFoundError(f"File not found in GCS: {revenue_file}")
            blob.download_to_file(buffer)
            buffer.seek(0)
            df_revenue = pd.read_csv(buffer)

        # Load hours data
        with BytesIO() as buffer:
            blob = bucket.blob(hours_file)
            if not blob.exists():
                raise FileNotFoundError(f"File not found in GCS: {hours_file}")
            blob.download_to_file(buffer)
            buffer.seek(0)
            df_hours = pd.read_csv(buffer)
            
        

    except Exception as e:
        raise RuntimeError(f"Failed to load data: {e}")

    # Convert numbers to float
    df_revenue['Revenue'] = df_revenue['Revenue'].replace('[\$,]', '', regex=True).astype(float)
    df_hours['NetAvailableHours'] = df_hours['NetAvailableHours'].replace('[\$,]', '', regex=True).astype(float)

    df_revenue['Month'] = df_revenue['Month'].astype(str).str.strip()
    df_hours['Month'] = df_hours['Month'].astype(str).str.strip()

    # Add Quarter column
    month_to_qtr = {'Jan': 'Q4', 'Feb': 'Q4', 'Mar': 'Q4',
                    'Apr': 'Q1', 'May': 'Q1', 'Jun': 'Q1',
                    'Jul': 'Q2', 'Aug': 'Q2', 'Sep': 'Q2',
                    'Oct': 'Q3', 'Nov': 'Q3', 'Dec': 'Q3'}
    df_revenue['Quarter'] = df_revenue['Month'].map(month_to_qtr)
    df_hours['Quarter'] = df_hours['Month'].map(month_to_qtr)

    return df_revenue, df_hours

def pivot_summary(df, value_field, index_field='FinalCustomerName'):
    df_grouped = df.groupby([index_field, 'Month'])[value_field].sum().reset_index()
    df_pivot = df_grouped.pivot(index=index_field, columns='Month', values=value_field).fillna(0)
    month_order = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    df_pivot = df_pivot[[m for m in month_order if m in df_pivot.columns]]
    if value_field != 'Realized Rate':
        df_pivot = df_pivot.astype(int)
    else:
        df_pivot = df_pivot.round(2)
    return df_pivot

def apply_filters(df_revenue, df_hours, min_rate, max_rate, segment, bu, du, quarter):
    # 🔄 Group hours at a more granular level
    group_keys = ['FinalCustomerName', 'Segment', 'BU', 'DU', 'Month']
    df_hours_grouped = df_hours.groupby(group_keys)['NetAvailableHours'].sum().reset_index()

    # 🔄 Merge revenue and hours on same keys
    merged = pd.merge(
        df_revenue,
        df_hours_grouped,
        on=group_keys,
        how='inner'
    )

    # 🔧 Realized Rate Calculation
    merged['Revenue'] = merged['Revenue'].fillna(0)
    merged['NetAvailableHours'] = merged['NetAvailableHours'].fillna(0)
    merged['Realized Rate'] = merged.apply(
        lambda row: round(row['Revenue'] / row['NetAvailableHours'], 2) if row['NetAvailableHours'] > 0 else 0,
        axis=1
    )

    # ✅ Apply filters
    if segment != "All":
        merged = merged[merged['Segment'] == segment]
    if bu != "All":
        merged = merged[merged['BU'] == bu]
    if du != "All":
        merged = merged[merged['DU'] == du]
    if quarter != "All":
        merged = merged[merged['Quarter'] == quarter]

    # ✅ Apply Realized Rate filter
    merged = merged[(merged['Realized Rate'] >= min_rate) & (merged['Realized Rate'] <= max_rate)]

    return merged

def run(df=None, user_question=None):
    st.title("Realized Rate by Account")

    df_revenue, df_hours = load_data()

    # Sidebar Filters
    st.sidebar.header("🔍 Filters")
    min_rate = st.sidebar.number_input("Minimum Realized Rate", min_value=0.0, max_value=1000.0, value=0.0, step=0.1)
    max_rate = st.sidebar.number_input("Maximum Realized Rate", min_value=0.0, max_value=1000.0, value=1000.0, step=0.1)

    segment_list = ['All'] + sorted(df_revenue['Segment'].dropna().unique())
    segment = st.sidebar.selectbox("Segment", segment_list)

    bu_list = ['All'] + sorted(df_revenue['BU'].dropna().unique())
    bu = st.sidebar.selectbox("BU", bu_list)

    du_list = ['All'] + sorted(df_revenue['DU'].dropna().unique())
    du = st.sidebar.selectbox("DU", du_list)

    quarter_list = ['All'] + ['Q1', 'Q2', 'Q3', 'Q4']
    quarter = st.sidebar.selectbox("Quarter", quarter_list)

    # Apply filters
    filtered_df = apply_filters(df_revenue, df_hours, min_rate, max_rate, segment, bu, du, quarter)

    # ✅ Show account-level match % summary
    full_group_keys = ['FinalCustomerName', 'Segment', 'BU', 'DU', 'Month']
    df_hours_grouped = df_hours.groupby(full_group_keys)['NetAvailableHours'].sum().reset_index()
    full_df = pd.merge(df_revenue, df_hours_grouped, on=full_group_keys, how='inner')
    full_df['Revenue'] = full_df['Revenue'].fillna(0)
    full_df['NetAvailableHours'] = full_df['NetAvailableHours'].fillna(0)
    full_df['Realized Rate'] = full_df.apply(
        lambda row: round(row['Revenue'] / row['NetAvailableHours'], 2) if row['NetAvailableHours'] > 0 else 0,
        axis=1
    )
    total_accounts = full_df['FinalCustomerName'].nunique()
    filtered_accounts = filtered_df['FinalCustomerName'].nunique()
    pct = round((filtered_accounts / total_accounts) * 100, 1) if total_accounts else 0
    st.markdown(f"✅ **{filtered_accounts} of {total_accounts} accounts** met the selected Realized Rate threshold (**{pct}%**)")

    # Output tables
    st.subheader("Realized Rate by FinalCustomerName")
    st.dataframe(pivot_summary(filtered_df, 'Realized Rate'))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 💰 Total Revenue by Month")
        st.dataframe(pivot_summary(filtered_df, 'Revenue'))
    with col2:
        st.markdown("### ⏱️ Total Net Available Hours by Month")
        st.dataframe(pivot_summary(filtered_df, 'NetAvailableHours'))
