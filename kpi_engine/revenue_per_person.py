import pandas as pd

def calculate_revenue_per_person(pnl_df: pd.DataFrame, ut_df: pd.DataFrame,
                                 segment: str = None,
                                 quarter: str = None) -> pd.DataFrame:
    """
    Calculates revenue per person for each Segment/DU/customer combination.
    
    Revenue = Sum of 'Amount in USD' where Type='Revenue' and Group1 in ['ONSITE', 'OFFSHORE', 'INDIRECT REVENUE']
    Person Count = Count of unique PSNo from ut_df
    Revenue per Person = Revenue / Person Count
    """

    # Prepare and clean P&L data
    pnl_df = pnl_df.copy()
    pnl_df['Month'] = pd.to_datetime(pnl_df['Month'], errors='coerce')
    pnl_df['Quarter'] = pnl_df['Month'].dt.to_period('Q').astype(str)

    pnl_df = pnl_df[
        (pnl_df['Type'].str.lower() == 'revenue') &
        (pnl_df['Group1'].str.upper().isin(['ONSITE', 'OFFSHORE', 'INDIRECT REVENUE']))
    ]

    if segment:
        pnl_df = pnl_df[pnl_df['Segment'].str.lower() == segment.lower()]
    if quarter:
        pnl_df = pnl_df[pnl_df['Quarter'] == quarter]

    # Aggregate Revenue
    revenue_grouped = pnl_df.groupby([
        'Segment', 'PVDG', 'PVDU', 'Exec DG', 'Exec DU',
        'FinalCustomerName', 'Contract ID', 'Date', 'wbs id'
    ], dropna=False)['Amount in USD'].sum().reset_index()
    revenue_grouped.rename(columns={'Amount in USD': 'Revenue'}, inplace=True)

    # Prepare and clean UT data
    ut_df = ut_df.copy()
    ut_df['date_a'] = pd.to_datetime(ut_df['date_a'], errors='coerce')
    ut_df['Quarter'] = ut_df['date_a'].dt.to_period('Q').astype(str)

    if segment:
        ut_df = ut_df[ut_df['Segment'].str.lower() == segment.lower()]
    if quarter:
        ut_df = ut_df[ut_df['Quarter'] == quarter]

    # Group UT to count unique persons per group
    headcount_grouped = ut_df.groupby([
        'Segment', 'PVDG', 'PVDU', 'Exec DG', 'Exec DU',
        'FinalCustomerName', 'Contract ID', 'Date', 'wbs id'
    ], dropna=False)['PSNo'].nunique().reset_index()
    headcount_grouped.rename(columns={'PSNo': 'Headcount'}, inplace=True)

    # Merge Revenue and Headcount
    merged = pd.merge(revenue_grouped, headcount_grouped,
                      on=['Segment', 'PVDG', 'PVDU', 'Exec DG', 'Exec DU',
                          'FinalCustomerName', 'Contract ID', 'Date', 'wbs id'],
                      how='inner')

    # Calculate Revenue per Person
    merged['RevenuePerPerson'] = merged['Revenue'] / merged['Headcount']
    merged = merged.sort_values(by='RevenuePerPerson', ascending=False)

    return merged
