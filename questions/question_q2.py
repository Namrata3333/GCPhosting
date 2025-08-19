# question_q2.py

import pandas as pd
import re

def run(df, user_question=None):
    import streamlit as st

    df.columns = df.columns.str.strip()
    df['Month'] = pd.to_datetime(df['Month'])

    # ✅ Apply Group1-based Revenue logic
    valid_group1 = ['ONSITE', 'OFFSHORE', 'INDIRECT REVENUE']
    df['Type'] = df['Type'].fillna('')
    df.loc[df['Group1'].isin(valid_group1), 'Type'] = 'Revenue'

    latest_month = df['Month'].max()
    prev_month = (latest_month - pd.DateOffset(months=1)).replace(day=1)

    segment = "Transportation"
    if user_question:
        for seg in df['Segment'].dropna().unique():
            if seg.lower() in user_question.lower():
                segment = seg
                break

    df = df[df['Segment'] == segment]

    revenue_df = df[df['Type'] == 'Revenue']
    cost_df = df[df['Type'] == 'Cost']

    revenue_m = revenue_df.groupby(['Client', 'Month'])['Amount'].sum().unstack(fill_value=0)
    cost_m = cost_df.groupby(['Client', 'Month'])['Amount'].sum().unstack(fill_value=0)
    margin_m = (revenue_m - cost_m) / revenue_m.replace(0, 1) * 100

    seg_rev = revenue_df.groupby('Month')['Amount'].sum()
    seg_cost = cost_df.groupby('Month')['Amount'].sum()
    seg_margin_pct = ((seg_rev - seg_cost) / seg_rev.replace(0, 1)) * 100

    try:
        margin_change = seg_margin_pct[latest_month] - seg_margin_pct[prev_month]
        margin_summary = f"{segment} margin {'increased' if margin_change > 0 else 'reduced'} {abs(margin_change):.1f}% from {prev_month.strftime('%b')} to {latest_month.strftime('%b')}, {'up' if margin_change > 0 else 'down'} from {seg_margin_pct[prev_month]:.1f}% to {seg_margin_pct[latest_month]:.1f}%."
    except:
        margin_summary = "Margin movement data unavailable."

    client_margin_prev = ((revenue_m[prev_month] - cost_m[prev_month]) / revenue_m[prev_month].replace(0, 1)) * 100
    client_margin_latest = ((revenue_m[latest_month] - cost_m[latest_month]) / revenue_m[latest_month].replace(0, 1)) * 100
    client_movement = (client_margin_latest < client_margin_prev).sum()
    total_clients = len(client_margin_prev)
    client_summary = f"{client_movement} out of {total_clients} clients ({(client_movement/total_clients)*100:.1f}%) in {segment} saw a drop in margin."

    cost_prev = seg_cost.get(prev_month, 0)
    cost_latest = seg_cost.get(latest_month, 0)
    cost_growth = ((cost_latest - cost_prev) / cost_prev) * 100 if cost_prev else 0
    cost_summary = f"{segment} cost {'increased' if cost_growth > 0 else 'decreased'} by {abs(cost_growth):.1f}% from {prev_month.strftime('%b')} to {latest_month.strftime('%b')}."

    margin_threshold = "a certain"
    if user_question:
        match = re.search(r'less than (\d+)%', user_question)
        if match:
            margin_threshold = f"less than {match.group(1)}%"


    group4_df = cost_df[['Month', 'Client', 'Amount', 'Group4']].dropna(subset=['Group4'])
    g4 = group4_df.groupby(['Group4', 'Month'])['Amount'].sum().unstack(fill_value=0)

    if prev_month not in g4.columns or latest_month not in g4.columns:
        st.warning("Missing Group4 cost data for selected months.")
        return

    g4_raw = g4.copy()
    g4['% Change'] = ((g4_raw[latest_month] - g4_raw[prev_month]) / g4_raw[prev_month].replace(0, 0.0001)) * 100
    g4_raw['abs_change'] = (g4_raw[latest_month] - g4_raw[prev_month])

    g4_positive_increase = g4_raw[g4_raw['abs_change'] > 0].copy()
    top8 = g4_positive_increase.sort_values(by='abs_change', ascending=False).head(8)

    table_df = pd.DataFrame({
        f'{prev_month.strftime("%b")} (Mn USD)': top8[prev_month] / 1e6,
        f'{latest_month.strftime("%b")} (Mn USD)': top8[latest_month] / 1e6,
        '% Change': g4.loc[top8.index, '% Change']
    }, index=top8.index)
    table_df.index.name = 'Group4'

    table_df[f'{prev_month.strftime("%b")} (Mn USD)'] = table_df[f'{prev_month.strftime("%b")} (Mn USD)'].map(lambda x: f"{x:,.2f}")
    table_df[f'{latest_month.strftime("%b")} (Mn USD)'] = table_df[f'{latest_month.strftime("%b")} (Mn USD)'].map(lambda x: f"{x:,.2f}")
    table_df['% Change'] = table_df['% Change'].map(lambda x: f"{x:.2f}%")

    st.markdown(f"### 📊 Top 8 Group4 Cost Increases (actual cost in Mn USD, % change from {prev_month.strftime('%b')} to {latest_month.strftime('%b')})")
    st.dataframe(table_df)
