# kpi_engine/resources.py

import pandas as pd
import json
from google.cloud import storage
import os
from io import BytesIO
from dotenv import load_dotenv

load_dotenv('.env.template')
def load_pnl_data(filepath: str, sheet_name: str = "LnTPnL") :
    """
    Load the PnL data from the provided Excel file and sheet.
    """
    try:
        # Initialize GCS client
        client = storage.Client.from_service_account_info(
            json.loads(os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")))
        bucket = client.bucket(os.getenv("GCS_BUCKET_NAME"))
        
        # Download from GCS
        with BytesIO() as buffer:
            bucket.blob(filepath).download_to_file(buffer)
            buffer.seek(0)
            df = pd.read_excel(buffer, sheet_name=sheet_name)  # Same pandas call
            
        return df

    except Exception as e:
        raise RuntimeError(f"Failed to load  data: {e}")  # Same error message

def preprocess_pnl_data(df):
    df.columns = df.columns.str.strip()
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    return df.dropna(subset=['Month'])

def calculate_total_resources(df):
    return df['Total Resources'].sum()

def calculate_resources_by_client(df):
    return df.groupby('Client')['Total Resources'].sum().reset_index()

def calculate_resources_by_type(df):
    return df.groupby('Type')['Total Resources'].sum().reset_index()

def calculate_resources_by_location(df):
    return df.groupby('Location')['Total Resources'].sum().reset_index()

def calculate_resources_trend(df):
    return df.groupby('Month')['Total Resources'].sum().reset_index()
