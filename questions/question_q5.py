import pandas as pd

def analyze_cb_cost_percentage_trend(pnl_df: pd.DataFrame) -> dict:
    """
    Calculates MoM trend of C&B Cost as a % of Total Revenue.

    Args:
        pnl_df (pd.DataFrame): The Profit and Loss dataframe.

    Returns:
        dict: Dictionary containing summary, table, and chart data.
    """

    # Filter C&B Cost rows
    cb_df = pnl_df[pnl_df["Group Description"] == "C&B"]
    revenue_df = pnl_df[pnl_df["Group Description"] == "Total Revenue"]

    # Sum by Month
    cb_monthly = cb_df.groupby("Month")["Amount in USD"].sum()
    rev_monthly = revenue_df.groupby("Month")["Amount in USD"].sum()

    # Join and calculate %
    combined = pd.DataFrame({
        "C&B Cost": cb_monthly,
        "Total Revenue": rev_monthly
    })

    combined["C&B Cost %"] = (combined["C&B Cost"] / combined["Total Revenue"]) * 100
    combined = combined.reset_index()

    # Prepare response
    summary = "Here is the Month-over-Month trend of C&B cost as a percentage of Total Revenue:"
    table = combined[["Month", "C&B Cost %"]].round(2).to_dict(orient="records")
    chart = {
        "x": combined["Month"].tolist(),
        "y": combined["C&B Cost %"].round(2).tolist(),
        "title": "C&B Cost % of Revenue - MoM Trend",
        "x_label": "Month",
        "y_label": "C&B Cost %"
    }

    return {
        "summary": summary,
        "table": table,
        "chart": chart
    }
