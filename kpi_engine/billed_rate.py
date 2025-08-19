# kpi_engine/billed_rate.py

import pandas as pd
from google.cloud import storage
import json
import os
from io import BytesIO
from dotenv import load_dotenv

load_dotenv('.env.template')

def load_data(pnl_path: str, ut_path: str, pnl_sheet: str = "LnTPnL", ut_sheet: str = "LNTData") -> tuple:
    """Load data from Excel files."""
    try:
        # Initialize GCS client
        client = storage.Client.from_service_account_info(
            json.loads(os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")))
        bucket = client.bucket(os.getenv("GCS_BUCKET_NAME"))

        # Load P&L data
        with BytesIO() as pnl_buffer:
            bucket.blob(pnl_path).download_to_file(pnl_buffer)
            pnl_buffer.seek(0)
            pnl_df = pd.read_excel(pnl_buffer, sheet_name=pnl_sheet)

        # Load UT data
        with BytesIO() as ut_buffer:
            bucket.blob(ut_path).download_to_file(ut_buffer)
            ut_buffer.seek(0)
            ut_df = pd.read_excel(ut_buffer, sheet_name=ut_sheet)

        return pnl_df, ut_df
        
    except Exception as e:
        raise RuntimeError(f"Failed to load data: {e}")  # Same error handling

def calculate_billed_rate(pnl_df: pd.DataFrame, ut_df: pd.DataFrame) -> float:
    """Calculate Billed Rate = Revenue / Total Billable Hours"""
    try:
        # Filter revenue from P&L table
        revenue = pnl_df.loc[
            pnl_df["Group1"].str.upper().isin(["ONSITE", "OFFSHORE", "INDIRECT REVENUE"]),
            "Amount in USD"
        ].sum()

        # Total billable hours from UT table
        total_billable_hours = ut_df["TotalBillableHours"].sum()

        if total_billable_hours == 0:
            return 0.0

        return revenue / total_billable_hours
    except Exception as e:
        raise RuntimeError(f"Error in calculating billed rate: {e}")
