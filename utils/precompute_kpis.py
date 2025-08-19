import os
import sys
import pandas as pd
from google.cloud import storage
import json
from io import BytesIO
from dotenv import load_dotenv

# Ensure repo root is on sys.path for imports from kpi_engine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables (assumes .env or .env.template exists)
load_dotenv('.env.template')

# Import functions that now expect a DataFrame directly
from kpi_engine.revenue_aggregated import get_revenue_aggregated
from kpi_engine.net_available_hours_aggregated import get_net_available_hours_aggregated
from kpi_engine.headcount import get_headcount_data
from kpi_engine.realized_rate import get_realized_rate_data
from kpi_engine.revenue_per_person import get_revenue_per_person_data

# GCS file paths (object names)
gcs_pnl_file = "LnTPnL.xlsx"
gcs_ut_file = "LNTData.xlsx"

# Output folder path
precomputed_dir = "sample_data/precomputed"
os.makedirs(precomputed_dir, exist_ok=True)

def load_excel_from_gcs(file_path):
    """Downloads an Excel file from GCS into a DataFrame."""
    try:
        service_account_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        bucket_name = os.getenv("GCS_BUCKET_NAME")

        if not service_account_json or not bucket_name:
            raise ValueError("Missing GOOGLE_APPLICATION_CREDENTIALS_JSON or GCS_BUCKET_NAME.")
        
        client = storage.Client.from_service_account_info(json.loads(service_account_json))
        bucket = client.bucket(bucket_name)
        
        blob = bucket.blob(file_path)
        
        if not blob.exists():
            raise FileNotFoundError(f"File not found in GCS: {file_path}")
            
        with BytesIO() as buffer:
            blob.download_to_file(buffer)
            buffer.seek(0)
            df = pd.read_excel(buffer)
            
        return df

    except Exception as e:
        raise RuntimeError(f"Failed to load data from GCS: {e}")

# Load data from GCS
print("⏳ Loading data from Google Cloud Storage...")
df_pnl = load_excel_from_gcs(gcs_pnl_file)
df_ut = load_excel_from_gcs(gcs_ut_file)
print("✅ Data loaded successfully from GCS.")

# Precompute and save revenue
df_revenue = get_revenue_aggregated(df_pnl, df_ut)
df_revenue.to_csv(os.path.join(precomputed_dir, "revenue.csv"), index=False)
print("✅ Precomputed revenue.csv saved.")

# Precompute and save net available hours
df_net_hours = get_net_available_hours_aggregated(df_ut)
df_net_hours.to_csv(os.path.join(precomputed_dir, "netavailablehours.csv"), index=False)
print("✅ Precomputed netavailablehours.csv saved.")

# Precompute and save headcount
df_headcount = get_headcount_data(df_ut)
df_headcount.to_csv(os.path.join(precomputed_dir, "headcount.csv"), index=False)
print("✅ Precomputed headcount.csv saved.")

# Precompute and save realized rate
df_realized = get_realized_rate_data(df_pnl, df_ut)
df_realized.to_csv(os.path.join(precomputed_dir, "realized_rate.csv"), index=False)
print("✅ Precomputed realized_rate.csv saved.")

# Precompute and save revenue per person
df_rpp = get_revenue_per_person_data(df_pnl, df_ut)
df_rpp.to_csv(os.path.join(precomputed_dir, "revenue_per_person.csv"), index=False)
print("✅ Precomputed revenue_per_person.csv saved.")

print("🎉 All KPI precomputations completed successfully.")
