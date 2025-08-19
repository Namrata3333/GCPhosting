# ✅ FILE: kpi_engine/net_available_hours_aggregated.py

import pandas as pd
from google.cloud import storage
from io import BytesIO
import json
import os
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv('.env.template')

def get_net_available_hours_aggregated(ut_path):
    
    try:
        # Initialize GCS client using credentials from environment variables
        client = storage.Client.from_service_account_info(
            json.loads(os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")))
        bucket = client.bucket(os.getenv("GCS_BUCKET_NAME"))

        # Download the file from GCS into an in-memory buffer
        with BytesIO() as buffer:
            blob = bucket.blob(ut_path)
            blob.download_to_file(buffer)
            buffer.seek(0)
            
            # Read the Excel data from the buffer
            df = pd.read_excel(buffer)
            df.columns = df.columns.str.strip()
            
        
        
    except Exception as e:
        raise RuntimeError(f"Failed to get net available hours data: {e}")
    

    df['Date_a'] = pd.to_datetime(df['Date_a'], errors='coerce')
    df['Month'] = df['Date_a'].dt.month.map({
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    })

    if 'Segment' not in df.columns:
        df['Segment'] = 'Unknown'
    if 'Exec DG' in df.columns:
        df['BU'] = df['Exec DG']
    else:
        df['BU'] = 'Unknown'
    if 'Exec DU' in df.columns:
        df['DU'] = df['Exec DU']
    else:
        df['DU'] = 'Unknown'

    grouped = df.groupby(['FinalCustomerName', 'Segment', 'BU', 'DU', 'Month'])['NetAvailableHours'].sum().reset_index()
    grouped = grouped.rename(columns={'NetAvailableHours': 'NetAvailableHours'})
    return grouped
