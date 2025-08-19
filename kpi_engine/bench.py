# kpi_engine/bench.py

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
    df['Billability'] = df['Billability'].str.strip().str.upper()
    df['BenchFlag'] = df['Billability'].apply(lambda x: 1 if x == 'BENCH' else 0)
    return df.dropna(subset=['Month'])

def total_bench_count(df):
    return df['BenchFlag'].sum()

def bench_percentage(df):
    total = len(df)
    bench = total_bench_count(df)
    return round((bench / total) * 100, 2) if total > 0 else 0.0

def bench_by_client(df):
    return df[df['BenchFlag'] == 1].groupby('Client').size().reset_index(name='BenchCount')

def bench_by_location(df):
    return df[df['BenchFlag'] == 1].groupby('Location').size().reset_index(name='BenchCount')

def bench_trend(df):
    return df.groupby('Month')['BenchFlag'].sum().reset_index(name='BenchCount')

def bench_summary(df):
    trend = bench_trend(df).sort_values('BenchCount', ascending=False)
    summary = [
        f"Total bench headcount is {total_bench_count(df)}.",
        f"Bench percentage across all resources is {bench_percentage(df)}%.",
        f"Month with highest bench: {trend.iloc[0].to_dict() if not trend.empty else 'N/A'}"
    ]
    return summary
