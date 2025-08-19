# kpi_engine/headcount.py

import pandas as pd
from google.cloud import storage
from io import BytesIO
import json
import os
from dotenv import load_dotenv


load_dotenv('.env.template')

def load_resource_data(filepath, sheet_name="ResourceMaster"):
    try:
        # Initialize GCS client
        client = storage.Client.from_service_account_info(
            json.loads(os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")))
        bucket = client.bucket(os.getenv("GCS_BUCKET_NAME"))
        
        # Treat filepath as GCS path (same format as local)
        blob = bucket.blob(filepath)
        
        # Download and process
        with BytesIO() as file_obj:
            blob.download_to_file(file_obj)
            file_obj.seek(0)
            df = pd.read_excel(file_obj, sheet_name=sheet_name)  # Same pandas call
            
        return df
        
    except Exception as e:
        # Same error type and message format
        raise RuntimeError(f"Failed to load data: {e}")


def preprocess_resource_data(df):
    df.columns = df.columns.str.strip()
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    df['Headcount'] = 1  # Each row is one resource
    return df.dropna(subset=['Month'])

def total_headcount(df):
    return df['Headcount'].sum()

def headcount_by_client(df):
    return df.groupby('Client')['Headcount'].sum().reset_index()

def headcount_by_type(df):
    return df.groupby('Type')['Headcount'].sum().reset_index()

def headcount_by_location(df):
    return df.groupby('Location')['Headcount'].sum().reset_index()

def headcount_trend(df):
    return df.groupby('Month')['Headcount'].sum().reset_index()

def headcount_summary(df):
    summary = [
        f"Total headcount: {total_headcount(df)}",
        f"Top client by headcount: {headcount_by_client(df).sort_values('Headcount', ascending=False).iloc[0].to_dict()}",
        f"Peak headcount month: {headcount_trend(df).sort_values('Headcount', ascending=False).iloc[0].to_dict()}"
    ]
    return summary
