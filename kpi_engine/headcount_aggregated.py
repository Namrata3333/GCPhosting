# ✅ FINAL: headcount_aggregated.py — uses distinct PSNo like q7.py, grouped by Segment and Month
import pandas as pd

def run(df):
    df = df.copy()
    
    # Ensure correct datetime parsing
    df['Date_a'] = pd.to_datetime(df['Date_a'], errors='coerce')
    df = df.dropna(subset=['Date_a', 'Segment', 'PSNo'])

    # Create month column in format like 'Jan', 'Feb', etc.
    df['Month'] = df['Date_a'].dt.strftime('%b')

    # Include relevant fields
    df = df[['PSNo', 'Status', 'FinalCustomerName', 'Segment', 'Date_a', 'BU', 'DU', 'Month']]

    # Compute unique headcount (distinct PSNo) by Segment and Month
    grouped = df.groupby(['Segment', 'Month'])['PSNo'].nunique().reset_index()
    grouped = grouped.rename(columns={'PSNo': 'Headcount'})

    # Format headcount to 1 decimal (optional)
    grouped['Headcount'] = grouped['Headcount'].astype(float).round(1)

    return grouped
