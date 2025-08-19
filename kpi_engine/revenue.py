import pandas as pd

def calculate_revenue(pnl_df: pd.DataFrame,
                      segment: str = None,
                      customer: str = None,
                      quarter: str = None,
                      group_by: list = ['FinalCustomerName', 'Quarter']) -> pd.DataFrame:
    """
    Calculate total Revenue based on P&L data.

    Revenue is filtered by:
      - Type == 'Revenue'
      - Group1 in ['ONSITE', 'OFFSHORE', 'INDIRECT REVENUE']

    Optional filters:
      - segment
      - customer
      - quarter

    Parameters:
      - group_by: list of columns to group results by
    """
    df = pnl_df.copy()
    df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
    df['Quarter'] = df['Month'].dt.to_period('Q').astype(str)

    df = df[(df['Type'].str.lower() == 'revenue') &
            (df['Group1'].str.upper().isin(['ONSITE', 'OFFSHORE', 'INDIRECT REVENUE']))]

    if segment:
        df = df[df['Segment'].str.lower() == segment.lower()]
    if customer:
        df = df[df['FinalCustomerName'].str.lower() == customer.lower()]
    if quarter:
        df = df[df['Quarter'] == quarter]

    grouped = df.groupby(group_by)['Amount in USD'].sum().reset_index()
    grouped.rename(columns={'Amount in USD': 'Revenue'}, inplace=True)
    return grouped
