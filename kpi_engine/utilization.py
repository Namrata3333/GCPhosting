# utilization.py

import pandas as pd
import os
import streamlit as st
from google.cloud import storage
from io import BytesIO
import json
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv('.env.template')
@st.cache_data
def load_ut_data():
    try:
        # Initialize GCS client using credentials from environment variables
        client = storage.Client.from_service_account_info(
            json.loads(os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")))
        bucket = client.bucket(os.getenv("GCS_BUCKET_NAME"))

        # Define the file path within the GCS bucket
        filepath = "LNTData.xlsx"
        blob = bucket.blob(filepath)

        # Check if the file exists in the GCS bucket
        if not blob.exists():
            raise FileNotFoundError(f"File not found in GCS bucket: {filepath}")

        # Download the file into an in-memory buffer
        with BytesIO() as buffer:
            blob.download_to_file(buffer)
            buffer.seek(0)
            
            # Read the Excel data from the buffer
            df = pd.read_excel(buffer)
            
        
        
    except Exception as e:
        raise RuntimeError(f"Failed to load UT data: {e}")
    
    # Clean and standardize column names
    df.columns = df.columns.str.strip()
    
    # Calculate UT%
    df["UT%"] = (df["TotalBillableHours"] / df["NetAvailableHours"]) * 100
    df["Month"] = pd.to_datetime(df["Month"])
    df["Quarter"] = df["Month"].dt.to_period("Q")
    df["Year"] = df["Month"].dt.year.astype(str)
    
    return df


# ✅ Monthly trend for UT%
def get_ut_mom_trend(df, level="DU"):
    trend = df.groupby([pd.Grouper(key="Month", freq="M"), level])["UT%"].mean().reset_index()
    trend["Month"] = trend["Month"].dt.strftime("%Y-%m")
    return trend.pivot(index="Month", columns=level, values="UT%").fillna(0)


# ✅ Quarterly trend for UT%
def get_ut_qoq_trend(df, level="DU"):
    trend = df.groupby(["Quarter", level])["UT%"].mean().reset_index()
    trend["Quarter"] = trend["Quarter"].astype(str)
    return trend.pivot(index="Quarter", columns=level, values="UT%").fillna(0)


# ✅ Yearly trend for UT%
def get_ut_yoy_trend(df, level="DU"):
    trend = df.groupby(["Year", level])["UT%"].mean().reset_index()
    return trend.pivot(index="Year", columns=level, values="UT%").fillna(0)


# ✅ Agent-level UT%
def get_agent_ut(df):
    return df.groupby("EmployeeID")["UT%"].mean().reset_index().rename(columns={"UT%": "Avg UT%"})


# ✅ Filter by segment, DU, BU, account
def filter_ut(df, segment=None, du=None, bu=None, account=None):
    if segment:
        df = df[df["Segment"] == segment]
    if du:
        df = df[df["DU"] == du]
    if bu:
        df = df[df["BU"] == bu]
    if account:
        df = df[df["Account"] == account]
    return df
