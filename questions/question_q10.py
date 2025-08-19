import pandas as pd
import streamlit as st
import calendar
from google.cloud import storage
import os
import json
from io import BytesIO
from dotenv import load_dotenv


load_dotenv('.env.template')

def run(query):
    st.header("📊 Fresher UT% Monthly Trends by Bucket")

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

        required_fields = ['FresherAgeingCategory', 'Segment', 'Month', 'Year',
                           'TotalBillableHours', 'NetAvailableHours']

        column_map = {
            'DU': 'Delivery_Unit',
            'BU': 'Business_Unit'
        }

        for standard_col, actual_col in column_map.items():
            if actual_col in df.columns:
                df.rename(columns={actual_col: standard_col}, inplace=True)
                required_fields.append(standard_col)

        missing_cols = [col for col in required_fields if col not in df.columns]
        if missing_cols:
            st.error(f"Missing required columns: {', '.join(missing_cols)}")
            return

        df['Year'] = df['Year'].astype(str).str.extract(r'(\d{4})').astype(int)
        df["Utilization %"] = (df["TotalBillableHours"] / df["NetAvailableHours"]) * 100
        df = df.replace([float('inf'), float('-inf')], pd.NA).dropna(subset=['Utilization %'])

        df = df[df['FresherAgeingCategory'].notna()]

        # Format Month-Year column for pivot
        df['MonthYear'] = df.apply(lambda row: f"{calendar.month_abbr[int(row['Month'])]}-{row['Year']}", axis=1)
        df['MonthOrder'] = df['Year'] * 100 + df['Month']  # For proper sorting

        # --- Insights ---
        latest_month = df.sort_values(["Year", "Month"], ascending=[True, True]).dropna(subset=["Utilization %"]).iloc[-1]
        latest_year = latest_month["Year"]
        latest_month_num = latest_month["Month"]
        latest_month_name = calendar.month_name[int(latest_month_num)]

        summary = df[(df["Year"] == latest_year) & (df["Month"] == latest_month_num)]
        category_summary = summary.groupby("FresherAgeingCategory")["Utilization %"].mean().sort_values(ascending=False)

        top_increase = category_summary.dropna().head(3)
        top_decrease = category_summary.dropna().sort_values().head(3)

        # --- UT% Table ---
        pivot_ut = df.pivot_table(index='FresherAgeingCategory',
                                  columns='MonthYear',
                                  values='Utilization %',
                                  aggfunc='mean')

        sorted_cols = df[['MonthYear', 'MonthOrder']].drop_duplicates().sort_values('MonthOrder')['MonthYear']
        pivot_ut = pivot_ut[sorted_cols]

        styled_ut = pivot_ut.style.format(
            lambda x: f"{int(round(x))}%" if pd.notnull(x) else ""
        ).set_properties(**{
            'border': '1px solid lightgrey',
            'border-collapse': 'collapse'
        })

        st.dataframe(styled_ut, use_container_width=True)

        # --- TotalBillableHours and NetAvailableHours Tables (Side by Side) ---
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("🔹 **TotalBillableHours**")
            billable_pivot = df.pivot_table(index='FresherAgeingCategory',
                                            columns='MonthYear',
                                            values='TotalBillableHours',
                                            aggfunc='sum')
            billable_pivot = billable_pivot[sorted_cols]

            styled_billable = billable_pivot.style.format(
                "{:,.0f}"
            ).set_properties(**{'border': '1px solid lightgrey', 'border-collapse': 'collapse'})
            st.dataframe(styled_billable, use_container_width=True)

        with col2:
            st.markdown("🔹 **NetAvailableHours**")
            available_pivot = df.pivot_table(index='FresherAgeingCategory',
                                             columns='MonthYear',
                                             values='NetAvailableHours',
                                             aggfunc='sum')
            available_pivot = available_pivot[sorted_cols]

            styled_available = available_pivot.style.format(
                "{:,.0f}"
            ).set_properties(**{'border': '1px solid lightgrey', 'border-collapse': 'collapse'})
            st.dataframe(styled_available, use_container_width=True)

    except Exception as e:
        st.error(f"Error running analysis: {e}")
