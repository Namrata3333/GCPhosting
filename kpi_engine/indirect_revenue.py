# kpi_engine/indirect_revenue.py

import pandas as pd
from google.cloud import storage
from io import BytesIO
import json
import os
from dotenv import load_dotenv

load_dotenv('.env.template')


def load_data(pnl_path: str) -> pd.DataFrame:
    try:
        # Initialize GCS client (shared configuration)
        client = storage.Client.from_service_account_info(
            json.loads(os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")))
        bucket = client.bucket(os.getenv("GCS_BUCKET_NAME"))

        # Download and process file
        with BytesIO() as buffer:
            bucket.blob(pnl_path).download_to_file(buffer)
            buffer.seek(0)
            df= pd.read_excel(buffer, sheet_name="LnTPnL")  # Same sheet name
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load data: {e}")  # Same error format

def calculate_indirect_revenue(df: pd.DataFrame) -> float:
    try:
        indirect_revenue = df[df["Type"] == "Indirect Revenue"]["Amount in USD"].sum()
        return indirect_revenue
    except Exception as e:
        raise RuntimeError(f"Error calculating Indirect Revenue: {e}")
