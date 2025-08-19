import pandas as pd

def calculate_realized_rate_quarterly(pnl_df: pd.DataFrame, ut_df: pd.DataFrame, segment_filter: str = None, drop_threshold: float = 3.0):
    # Standardize Month format
    pnl_df['Month'] = pd.to_datetime(pnl_df['Month'], errors='coerce')
    ut_df['Month'] = pd.to_datetime(ut_df['Month'], errors='coerce')

    # Drop rows with missing join keys
    pnl_df.dropna(subset=['FinalCustomerName', 'Month'], inplace=True)
    ut_df.dropna(subset=['FinalCustomerName', 'Month'], inplace=True)

    # Filter revenue rows only
    pnl_df = pnl_df[
        (pnl_df['Group1'].str.upper().isin(['ONSITE', 'OFFSHORE', 'INDIRECT REVENUE'])) &
        (pnl_df['Type'].str.lower() == 'revenue')
    ]

    # Apply segment filter if specified
    if segment_filter:
        pnl_df = pnl_df[pnl_df['Segment'] == segment_filter]

    # Aggregate revenue
    revenue_df = pnl_df.groupby(['FinalCustomerName', 'Month'], as_index=False)["Amount in USD"].sum()
    revenue_df.rename(columns={"Amount in USD": "Revenue"}, inplace=True)

    # Aggregate UT data
    ut_df = ut_df.dropna(subset=['NetAvailableHours'])
    ut_df = ut_df[ut_df['NetAvailableHours'] != 0]
    ut_grouped = ut_df.groupby(['FinalCustomerName', 'Month'], as_index=False)['NetAvailableHours'].sum()
    ut_grouped.rename(columns={'NetAvailableHours': 'AvailableHours'}, inplace=True)

    # Merge P&L and UT data
    merged_df = pd.merge(revenue_df, ut_grouped, on=['FinalCustomerName', 'Month'], how='inner')

    # Compute realized rate per month
    merged_df = merged_df[merged_df['AvailableHours'] != 0]
    merged_df['RealizedRate'] = merged_df['Revenue'] / merged_df['AvailableHours']

    # Compute quarter from Month
    merged_df['Quarter'] = merged_df['Month'].dt.to_period('Q')

    # Aggregate to quarterly level
    qtr_df = merged_df.groupby(['FinalCustomerName', 'Quarter'], as_index=False).agg({
        'Revenue': 'sum',
        'AvailableHours': 'sum'
    })
    qtr_df = qtr_df[qtr_df['AvailableHours'] != 0]
    qtr_df['RealizedRate'] = qtr_df['Revenue'] / qtr_df['AvailableHours']

    # Sort by FinalCustomerName and Quarter to compute difference
    qtr_df.sort_values(['FinalCustomerName', 'Quarter'], inplace=True)
    qtr_df['PrevRealizedRate'] = qtr_df.groupby('FinalCustomerName')['RealizedRate'].shift(1)
    qtr_df['RateDrop'] = qtr_df['PrevRealizedRate'] - qtr_df['RealizedRate']

    # Filter accounts where rate drop > threshold
    qtr_df_filtered = qtr_df[qtr_df['RateDrop'] > drop_threshold]

    return qtr_df_filtered[['FinalCustomerName', 'Quarter', 'PrevRealizedRate', 'RealizedRate', 'RateDrop']].reset_index(drop=True)


# This function can now be called in q6.py and passed pnl_df, ut_df, segment, threshold from the UI.
