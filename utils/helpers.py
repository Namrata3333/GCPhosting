import pandas as pd

def extract_latest_quarters(date_series, n=2):
    qtrs = pd.PeriodIndex(date_series.dt.to_period("Q")).unique()
    qtrs = sorted(qtrs)[-n:]
    return [str(q) for q in qtrs]

def extract_relevant_quarters(df, quarters):
    df['Quarter'] = df['Date'].dt.to_period('Q').astype(str)
    return df[df['Quarter'].isin(quarters)].copy()

def format_in_inr_cr(value):
    try:
        return f"₹{value/1e7:.1f} Cr"
    except:
        return "-"

