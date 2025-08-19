# ✅ UPDATED: margin.py (with Group1-based Revenue logic)
import pandas as pd
from google.cloud import storage
from io import BytesIO
import json
import os
from dotenv import load_dotenv


load_dotenv('.env.template')

def load_pnl_data(filepath, sheet_name="LnTPnL"):
    try:
        # Initialize GCS client
        client = storage.Client.from_service_account_info(
            json.loads(os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")))
        bucket = client.bucket(os.getenv("GCS_BUCKET_NAME"))

        # Download and process (preserving original parameters)
        with BytesIO() as buffer:
            bucket.blob(filepath).download_to_file(buffer)
            buffer.seek(0)
            df = pd.read_excel(
                buffer, 
                sheet_name=sheet_name, 
                engine="openpyxl"  # ← Preserve original engine
            )
        return df

    except Exception as e:
        raise RuntimeError(f"Failed to load data: {e}")  # Same error message

def preprocess_pnl_data(df):
    df.columns = df.columns.str.strip()

    # Dynamic column renaming
    column_map = {}

    if 'Company Code' in df.columns:
        column_map['Company Code'] = 'Client'
    elif 'Company_Code' in df.columns:
        column_map['Company_Code'] = 'Client'

    if 'Amount in USD' in df.columns:
        column_map['Amount in USD'] = 'Amount'
    elif 'Amount' in df.columns:
        column_map['Amount'] = 'Amount'

    if 'Month' in df.columns:
        column_map['Month'] = 'Month'

    if 'Type' in df.columns:
        column_map['Type'] = 'Type'

    if 'Segment' in df.columns:
        column_map['Segment'] = 'Segment'

    df = df.rename(columns=column_map)

    # Convert Month column to datetime safely
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')

    # Check for Group1 column before revenue mapping
    if 'Group1' not in df.columns:
        raise ValueError("Required column 'Group1' not found in the dataset for revenue logic.")

    # Coerce Amount column and drop missing
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df = df.dropna(subset=['Month', 'Amount', 'Client'])

    # Reclassify Group1 values as 'Revenue'
    valid_group1 = ['ONSITE', 'OFFSHORE', 'INDIRECT REVENUE']
    df['Type'] = df['Type'].fillna('')
    df.loc[df['Group1'].isin(valid_group1), 'Type'] = 'Revenue'

    # Keep only Cost and Revenue rows
    df = df[df['Type'].isin(['Cost', 'Revenue'])]

    return df

def compute_margin(df):
    # Add Quarter column
    df['Quarter'] = df['Month'].dt.to_period("Q").astype(str)

    # Grouping by Quarter, Month, Client, and optionally Segment
    groupby_cols = ['Quarter', 'Month', 'Client']
    if 'Segment' in df.columns:
        groupby_cols.append('Segment')

    grouped = df.groupby(groupby_cols + ['Type'])['Amount'].sum().unstack().fillna(0)

    grouped['Revenue'] = grouped.get('Revenue', 0)
    grouped['Cost'] = grouped.get('Cost', 0)
    grouped['Margin'] = grouped['Revenue'] - grouped['Cost']
    grouped['Margin %'] = (grouped['Margin'] / grouped['Revenue'].replace(0, 1)) * 100

    return grouped.reset_index()
