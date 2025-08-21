# app.py

import streamlit as st
st.set_page_config(page_title="LTTS BI Assistant", layout="wide")

from utils.semantic_matcher import find_best_matching_qid  # returns (qid, prompt, score)
import importlib
from kpi_engine import margin
import os
import pandas as pd
import inspect
from PIL import Image
from io import BytesIO
import base64
import re
from datetime import datetime
from dotenv import load_dotenv
from google.cloud import storage
import json


load_dotenv('.env.template')
# ---------- tiny helper (fixes NameError) ----------
def _safe_has_cols(frame: pd.DataFrame, cols) -> bool:
    """Return True if all required columns exist in the DataFrame."""
    return isinstance(frame, pd.DataFrame) and all(c in frame.columns for c in cols)

# -----------------------------
# Prompt bank (preserving UX)
# -----------------------------
PROMPT_BANK = [
    "List accounts with margin % less than 30% in the last quarter",
    "Which cost caused margin drop last month in Transportation?",
    "How much C&B varied from last quarter to this quarter?",
    "C&B cost as percentage of revenue trend",
    "What is FTE trend over months?",
    "How is utilization % trending?",
    "realized rate",
    "revenue per person",
    "fresher ut trend"
]

# -----------------------------
# Session state (preserved)
# -----------------------------
if "autofill_text" not in st.session_state:
    st.session_state.autofill_text = ""
if "clear_chat" not in st.session_state:
    st.session_state.clear_chat = False

def handle_click(prompt):
    st.session_state.autofill_text = prompt
    st.session_state.clear_chat = False

def clear_input():
    st.session_state.autofill_text = ""
    st.session_state.clear_chat = True

# -----------------------------
# Data loaders (P&L preserved) + OPTIONAL UT loader
# -----------------------------
load_dotenv('.env.template')
@st.cache_data

def load_pnl():
      # Explicitly load from .env.template
    
    # 2. Get configuration
    filepath = "LnTPnL.xlsx"
    
    df = margin.load_pnl_data(filepath)
    df = margin.preprocess_pnl_data(df)
    # Ensure Month is datetime for filtering
    if "Month" in df.columns:
        try:
            df["Month"] = pd.to_datetime(df["Month"], errors="coerce")
        except Exception:
            pass
    if df.empty:
        raise ValueError("Loaded P&L data is empty after preprocessing.")
    return df


@st.cache_data
def load_ut_optional():
    ut_path = "LNTData.xlsx"  # Matches os.path.join("sample_data", "LNTData.xlsx")

    try:
        # 2. Initialize GCS client (using same .env.template as load_pnl())
        client = storage.Client.from_service_account_info(
            json.loads(os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")))
        bucket = client.bucket(os.getenv("GCS_BUCKET_NAME"))
        blob = bucket.blob(ut_path)
        
        # 3. Same "return None if not found" behavior
        if not blob.exists():
            return None
        
        # 4. IDENTICAL processing logic ▼
        with BytesIO() as file_obj:
            blob.download_to_file(file_obj)
            file_obj.seek(0)
            df = pd.read_excel(file_obj)
        
        df.columns = [str(c).strip() for c in df.columns]

        if "Date_a" in df.columns:
            df["Date_a_dt"] = pd.to_datetime(df["Date_a"], errors="coerce")
            df["Year"] = df["Date_a_dt"].dt.year
            df["MonthNum"] = df["Date_a_dt"].dt.month
            df["MonthName"] = df["Date_a_dt"].dt.strftime("%b")
        else:
            if "Month" in df.columns and pd.api.types.is_numeric_dtype(df["Month"]):
                month_map = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                            7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
                df["MonthName"] = df["Month"].map(month_map)
                df["MonthNum"] = df["Month"]
        # ▲ END OF ORIGINAL LOGIC
        
        return df
        
    except Exception:  # ← Same silent error handling
        return None

try:
    df_pnl = load_pnl()
except Exception as e:
    st.error(f"❌ Failed to load data: {e}")
    st.stop()

df_ut = load_ut_optional()  # may be None (non-breaking)

# -----------------------------
# Header (preserved)
# -----------------------------
def display_header():
    client = storage.Client.from_service_account_info(
    json.loads(os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")))
    bucket = client.bucket(os.getenv("GCS_BUCKET_NAME"))
    logo_path = "Logo.png"  # Same path structure
    
    # Check if logo exists in GCS
    blob = bucket.blob(logo_path)
    if blob.exists():
        # Load and process image (same as original)
        with BytesIO() as file_obj:
            blob.download_to_file(file_obj)
            file_obj.seek(0)
            logo = Image.open(file_obj)
            buffered = BytesIO()
            logo.save(buffered, format="PNG")
            encoded_image = base64.b64encode(buffered.getvalue()).decode()

        # IDENTICAL HTML STRUCTURE AS ORIGINAL
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: -20px; margin-bottom: 10px;">
                <div style="flex: 1;"></div>
                <div style="flex: 2; text-align: center;">
                    <h1 style='font-family: "Segoe UI", sans-serif; font-size: 40px; color: #002D62; margin: 0;'>
                        Conversational Analytics Assistant
                    </h1>
                </div>
                <div style="flex: 1; text-align: right;">
                    <img src="data:image/png;base64,{encoded_image}" width="140" />
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# Call the function exactly as before
display_header()

# -----------------------------
# Welcome text (preserved)
# -----------------------------
st.markdown(
    """
    <div style='text-align:center; font-size:18px; margin-bottom: 10px;'>
    Welcome to <b>AIde</b> — an AI-powered tool for analyzing business trends using your P&L and utilization data.
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Chat input + clear (preserved)
# -----------------------------
chat_col, clear_col = st.columns([4, 1])
with chat_col:
    user_question = st.text_input(
        label="👉 Start by typing your business question:",
        placeholder="e.g. List accounts with margin % less than 30% in the last quarter",
        value=st.session_state.autofill_text,
    )
with clear_col:
    if st.button("🧹 Clear Response"):
        clear_input()

# =========================================================
# Helper: Dynamic Amount field selector + unit helpers (financials)
# =========================================================
REVCOST_MARGIN_KEYWORDS = (
    "revenue", "cost", "margin", "c&b", "c & b", "c and b", "profit", "loss",
    "cogs", "gross margin", "gm%", "gm %", "cm%", "cm %"
)

def choose_amount_column(user_q: str, df: pd.DataFrame) -> str:
    """
    If the question is about revenue/cost/margin, prefer 'Amount in USD'.
    If it's missing, fall back to 'Amount in INR' with a notice.
    Non-financial questions: prefer INR if present else USD.
    """
    ql = (user_q or "").lower()
    wants_usd = any(k in ql for k in REVCOST_MARGIN_KEYWORDS)
    has_usd = "Amount in USD" in df.columns
    has_inr = "Amount in INR" in df.columns

    if wants_usd:
        if has_usd:
            return "Amount in USD"
        elif has_inr:
            st.caption("Note: 'Amount in USD' not found — using 'Amount in INR' for this financial question.")
            return "Amount in INR"
        else:
            return "Amount in USD"
    else:
        if has_inr:
            return "Amount in INR"
        elif has_usd:
            return "Amount in USD"
        else:
            return "Amount in INR"

def is_usd_col(amount_col: str) -> bool:
    return amount_col.strip().lower() == "amount in usd"

def unit_label(amount_col: str) -> str:
    return "USD mn" if is_usd_col(amount_col) else "INR mn (USD unavailable)"

def to_million(value) -> float:
    try:
        return round(float(value) / 1_000_000.0, 1)
    except Exception:
        return value

def series_to_million(s: pd.Series) -> pd.Series:
    try:
        return (s.astype(float) / 1_000_000.0).round(1)
    except Exception:
        return s

# =========================================================
# Parsing helpers shared by UT & P&L
# =========================================================
SIM_THRESHOLD = 0.72
FREEFORM_TRIGGERS = ("ai:", "freeform:", "ad-hoc:")

MONTH_ALIASES = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12
}

def parse_month_year_from_text(q: str):
    """Returns (month_num, year) if found; otherwise (None, None)."""
    ql = (q or "").lower()
    m = re.search(
        r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|january|february|march|april|june|july|august|september|october|november|december)\s+(\d{4})\b",
        ql,
    )
    if m:
        month_token, year = m.group(1), int(m.group(2))
        month_num = MONTH_ALIASES.get(month_token, None)
        return month_num, year
    for token, mnum in MONTH_ALIASES.items():
        if re.search(rf"\b{token}\b", ql):
            return mnum, None
    return None, None

def parse_account_token(q: str):
    """Light account parser: tokens like 'A1', 'A-1'."""
    m = re.search(r"\b([A-Za-z]\-?\d{1,3})\b", q or "")
    return m.group(1) if m else None

def _unique_nontrivial_values(series: pd.Series):
    vals = (
        series.dropna()
        .astype(str)
        .map(lambda x: x.strip())
        .replace("", pd.NA)
        .dropna()
        .unique()
        .tolist()
    )
    return [v for v in vals if isinstance(v, str) and len(v.strip()) >= 3]

# =========================================================
# (NEW) Lightweight rule override for Q1 — "margin % below <N>"
# =========================================================
_Q1_PATTERNS = [
    r"\b(?:margin|gm|cm)\s*%?\s*<\s*\d+\s*%?",
    r"\b(?:margin|gm|cm)\s*(?:%|percent|percentage)?\s*(?:less than|below|under)\s*\d+\s*%?",
    r"\b(?:less than|below|under)\s*\d+\s*%?\s*(?:margin|gm|cm)\b",
]
def _is_q1_margin_below_intent(q: str | None) -> bool:
    if not q:
        return False
    ql = q.lower()
    return any(re.search(p, ql) for p in _Q1_PATTERNS)

# =========================================================
# (NEW) Lightweight rule override for Q3 — "C&B quarter-over-quarter change"
# =========================================================
_Q3_PATTERNS = [
    r"\bc\s*&\s*b\b.*\b(var(?:y|ied)|change|delta|diff(?:erence)?)\b.*\bquarter\b",
    r"\bc\s*and\s*b\b.*\b(var(?:y|ied)|change|delta|diff(?:erence)?)\b.*\bquarter\b",
    r"\bc&b\b.*\bqoq\b",
    r"\bqoq\b.*\bc&b\b",
    r"\bcompare\b.*\bc&b\b.*\bquarter\b",
]
def _is_q3_cb_variance_intent(q: str | None) -> bool:
    if not q:
        return False
    ql = q.lower()
    return any(re.search(p, ql) for p in _Q3_PATTERNS)

# =========================================================
# UT headcount fallback (multi-dimension + Date_a) — working
# =========================================================
DIMENSION_CANDIDATES_UT = {
    "account_like": ["FinalCustomerName", "Account", "Customer", "Company_code"],
    "segment_like": ["Segment", "Vertical"],
    "org_like": ["BU", "DU"]
}

def extract_dimension_filters_ut(user_q: str, df_ut: pd.DataFrame):
    if df_ut is None or df_ut.empty:
        return {}
    ql = (user_q or "").lower()
    filters = {}
    acct_token = parse_account_token(user_q)
    if acct_token:
        for col in DIMENSION_CANDIDATES_UT["account_like"]:
            if col in df_ut.columns:
                filters.setdefault(col, []).append(acct_token)
                break
    for group, cols in DIMENSION_CANDIDATES_UT.items():
        for col in cols:
            if col not in df_ut.columns:
                continue
            matches = []
            for val in _unique_nontrivial_values(df_ut[col]):
                if val.lower() in ql:
                    matches.append(val)
            if matches:
                filters.setdefault(col, []).extend(matches)
    return filters

def apply_ut_filters(df_ut: pd.DataFrame, filters: dict, month_num: int | None, year: int | None):
    if df_ut is None or df_ut.empty:
        return pd.DataFrame(), year
    work = df_ut.copy()
    if "Date_a_dt" in work.columns and pd.api.types.is_datetime64_any_dtype(work["Date_a_dt"]):
        if month_num:
            if year is None:
                yrs = work[work["Date_a_dt"].dt.month == month_num]["Date_a_dt"].dt.year
                if len(yrs):
                    year = int(yrs.max())
        if month_num and year:
            work = work[(work["Date_a_dt"].dt.month == month_num) & (work["Date_a_dt"].dt.year == year)]
        elif month_num:
            work = work[work["Date_a_dt"].dt.month == month_num]
    else:
        if month_num and "MonthNum" in work.columns:
            work = work[work["MonthNum"] == month_num]
        if year and "Year" in work.columns:
            work = work[work["Year"] == year]
    for col, values in (filters or {}).items():
        if col not in work.columns or not values:
            continue
        mask = pd.Series(False, index=work.index)
        for v in values:
            mask = mask | work[col].astype(str).str.contains(str(v), case=False, na=False)
        work = work[mask]
    return work, year

def headcount_view(user_q: str, df_ut: pd.DataFrame):
    if df_ut is None or df_ut.empty:
        st.subheader("AI Fallback — Additional KPI")
        st.info("This analysis needs UT/HR datasets (e.g., NetAvailableHours, Utilization%). Please load/connect UT data to enable.")
        return True
    month_num, year = parse_month_year_from_text(user_q)
    dim_filters = extract_dimension_filters_ut(user_q, df_ut)
    person_cols = [c for c in ["PSNo", "Agent", "EmployeeID", "EmpID"] if c in df_ut.columns]
    if not person_cols:
        st.subheader("AI Fallback — Headcount")
        st.info("UT dataset found, but no person identifier column (e.g., PSNo/Agent) was detected.")
        return True
    person_col = person_cols[0]
    filt, resolved_year = apply_ut_filters(df_ut, dim_filters, month_num, year)
    if filt.empty:
        st.subheader("AI Fallback — Headcount")
        month_label = "month not specified" if month_num is None else datetime(2000, month_num, 1).strftime("%b")
        year_label = "" if (resolved_year is None and year is None) else f" {resolved_year or year}"
        st.info(f"No UT records found for the requested filters in {month_label}{year_label}.")
        return True
    ql = (user_question or "").lower()
    dfw = filt.copy()
    if "Status" in dfw.columns and ("billable" in ql or "non-billable" in ql):
        if "billable" in ql:
            dfw = dfw[dfw["Status"].astype(str).str.contains("billable", case=False, na=False)]
        elif "non-billable" in ql:
            dfw = dfw[dfw["Status"].astype(str).str.contains("non", case=False, na=False)]
    hc = dfw[person_col].nunique()
    st.subheader("AI Fallback — Headcount")
    pieces = []
    if month_num:
        mdisp = datetime(2000, month_num, 1).strftime("%b")
        if resolved_year or year:
            mdisp = f"{mdisp} {resolved_year or year}"
        pieces.append(f"**Month:** {mdisp}")
    else:
        pieces.append("**Month:** (not specified)")
    if dim_filters:
        applied = []
        for col, vals in dim_filters.items():
            applied.append(f"{col} contains [{', '.join(map(str, vals))}]")
        pieces.append("**Filters:** " + "; ".join(applied))
    else:
        pieces.append("**Filters:** (none)")
    st.markdown(" &nbsp;&nbsp; ".join(pieces))
    st.dataframe(pd.DataFrame([{"Headcount": hc}]))
    for grp_col in ["BU", "DU", "Segment", "Vertical"]:
        if grp_col in dfw.columns:
            br = dfw.groupby(grp_col, dropna=False)[person_col].nunique().reset_index().rename(columns={person_col:"Headcount"})
            st.markdown(f"**Headcount by {grp_col}**")
            st.dataframe(br.sort_values("Headcount", ascending=False))
    return True

# =========================================================
# Financial multi-dimension filtering for P&L (Segment/Account + Month)
# =========================================================
DIMENSION_CANDIDATES_PNL = {
    "account_like": ["FinalCustomerName", "Account", "Customer", "Company_code"],
    "segment_like": ["Segment", "Vertical", "BU", "DU"]
}

def extract_dimension_filters_pnl(user_q: str, df_pnl: pd.DataFrame):
    if df_pnl is None or df_pnl.empty:
        return {}
    ql = (user_q or "").lower()
    filters = {}

    # explicit account token (A1)
    acct_token = parse_account_token(user_q)
    if acct_token:
        for col in DIMENSION_CANDIDATES_PNL["account_like"]:
            if col in df_pnl.columns:
                filters.setdefault(col, []).append(acct_token)
                break

    # substring matches for known values
    for group, cols in DIMENSION_CANDIDATES_PNL.items():
        for col in cols:
            if col not in df_pnl.columns:
                continue
            matches = []
            for val in _unique_nontrivial_values(df_pnl[col]):
                if val.lower() in ql:
                    matches.append(val)
            if matches:
                filters.setdefault(col, []).extend(matches)

    return filters

def apply_pnl_filters(df: pd.DataFrame, filters: dict, month_num: int | None, year: int | None):
    if df is None or df.empty:
        return pd.DataFrame(), year
    work = df.copy()

    # Month/year via 'Month' datetime column
    if "Month" in work.columns and pd.api.types.is_datetime64_any_dtype(work["Month"]):
        if month_num:
            if year is None:
                yrs = work[work["Month"].dt.month == month_num]["Month"].dt.year
                if len(yrs):
                    year = int(yrs.max())
        if month_num and year:
            work = work[(work["Month"].dt.month == month_num) & (work["Month"].dt.year == year)]
        elif month_num:
            work = work[work["Month"].dt.month == month_num]

    # Dimension filters: AND across columns, OR within the same column
    for col, values in (filters or {}).items():
        if col not in work.columns or not values:
            continue
        mask = pd.Series(False, index=work.index)
        for v in values:
            mask = mask | work[col].astype(str).str.contains(str(v), case=False, na=False)
        work = work[mask]

    return work, year

# ------------------ Financial fallbacks (with filtering) ------------------
def _generic_margin_summary(df: pd.DataFrame, user_q: str):
    st.subheader("AI Fallback — General Summary")

    amount_col = choose_amount_column(user_q, df)
    if not _safe_has_cols(df, ["Type", amount_col]):
        st.warning(f"The dataset is missing required columns ('Type', '{amount_col}') for a safe fallback summary.")
        return

    month_num, year = parse_month_year_from_text(user_q)
    dim_filters = extract_dimension_filters_pnl(user_q, df)
    dff, resolved_year = apply_pnl_filters(df, dim_filters, month_num, year)

    if dff.empty:
        st.info("No P&L rows found for the requested filters/time. Showing overall totals instead.")
        dff = df

    unit = unit_label(amount_col)

    if "Month" in dff.columns:
        g = dff.groupby(["Month", "Type"], dropna=False)[amount_col].sum().reset_index()
        g[amount_col] = series_to_million(g[amount_col])
        st.markdown(f"**Monthly Revenue/Cost** (values in {unit})")
        st.dataframe(g)

    pivot = dff.pivot_table(values=amount_col, index=None, columns="Type", aggfunc="sum", fill_value=0)
    if isinstance(pivot, pd.DataFrame):
        rev = float(pivot["Revenue"].iloc[0]) if "Revenue" in pivot.columns else 0.0
        cost = float(pivot["Cost"].iloc[0]) if "Cost" in pivot.columns else 0.0
    else:
        rev = float(pivot.get("Revenue", 0.0))
        cost = float(pivot.get("Cost", 0.0))

    margin_amt = rev - cost
    margin_pct = (margin_amt / cost * 100) if cost else None

    pieces = []
    if month_num:
        mdisp = datetime(2000, month_num, 1).strftime("%b")
        if resolved_year or year:
            mdisp = f"{mdisp} {resolved_year or year}"
        pieces.append(f"**Month filter:** {mdisp}")
    if dim_filters:
        applied = []
        for col, vals in dim_filters.items():
            applied.append(f"{col} contains [{', '.join(map(str, vals))}]")
        pieces.append("**Filters:** " + "; ".join(applied))
    if pieces:
        st.caption(" | ".join(pieces))

    st.markdown("**Quick Totals**")
    st.write(
        {
            f"Revenue (total, {unit})": to_million(rev),
            f"Cost (total, {unit})": to_million(cost),
            "Margin (Amount, same unit)": to_million(margin_amt),
            "Margin % ( (Rev - Cost)/Cost )": round(margin_pct, 1) if margin_pct is not None else "N/A",
        }
    )

    for key in ["Company_code", "FinalCustomerName", "Account", "Customer"]:
        if key in dff.columns:
            by_acct = dff.groupby([key, "Type"], dropna=False)[amount_col].sum().reset_index()
            by_acct[amount_col] = series_to_million(by_acct[amount_col])
            st.markdown(f"**By {key}** (values in {unit})")
            st.dataframe(by_acct.head(50))
            break

def _use_kpi_tools_if_available(user_q: str, df: pd.DataFrame):
    """
    Best-effort use of pandas-only views.
    Includes headcount intent via UT (using Date_a) if loaded.
    Adds multi-dimension + Month filtering for P&L-based financial metrics.
    """
    ql = (user_q or "").lower()

    # ---- Headcount intent (Date_a + multi-dimension filters) ----
    if any(w in ql for w in ["headcount", "fte", "resources"]) or re.search(r"\bhc\b", ql):
        return headcount_view(user_question, df_ut)

    # ---- Financial fallbacks (USD mn where available) ----
    amount_col = choose_amount_column(user_q, df)
    unit = unit_label(amount_col)

    # Extract P&L filters once
    month_num, year = parse_month_year_from_text(user_q)
    dim_filters = extract_dimension_filters_pnl(user_q, df)
    dff, resolved_year = apply_pnl_filters(df, dim_filters, month_num, year)
    if dff.empty:
        dff = df
        tried_filter_note = True
    else:
        tried_filter_note = False

    # Margin-style view
    if "margin" in ql:
        st.subheader("AI Fallback — Margin Analysis")
        try:
            if _safe_has_cols(dff, ["Type", amount_col]) and "Month" in dff.columns:
                monthly = dff.pivot_table(
                    values=amount_col, index="Month", columns="Type", aggfunc="sum", fill_value=0
                ).reset_index()
                for col in ["Revenue", "Cost"]:
                    if col in monthly.columns:
                        monthly[col] = series_to_million(monthly[col])
                if "Revenue" in monthly.columns and "Cost" in monthly.columns:
                    monthly["Margin Amount"] = (monthly["Revenue"] - monthly["Cost"]).round(1)
                    monthly["Margin %"] = monthly.apply(
                        lambda r: round((r["Margin Amount"] / r["Cost"] * 100), 1) if r["Cost"] else None, axis=1
                    )
                parts = [f"Values shown in {unit}."]
                if month_num:
                    mdisp = datetime(2000, month_num, 1).strftime("%b")
                    if resolved_year or year:
                        mdisp = f"{mdisp} {resolved_year or year}"
                    parts.append(f"Month filter: {mdisp}")
                if dim_filters:
                    applied = []
                    for col, vals in dim_filters.items():
                        applied.append(f"{col} contains [{', '.join(map(str, vals))}]")
                    parts.append("Filters: " + "; ".join(applied))
                if tried_filter_note:
                    parts.append("(No rows matched filters — showing overall results.)")
                st.caption(" | ".join(parts))
                st.dataframe(monthly)
                return True
        except Exception as e:
            st.warning(f"Margin view failed: {e}")

    # Revenue / Cost breakdown
    if ("revenue" in ql) or ("cost" in ql):
        st.subheader("AI Fallback — Revenue/Cost Breakdown")
        try:
            if _safe_has_cols(dff, ["Type", amount_col]) and "Month" in dff.columns:
                g = dff.groupby(["Month", "Type"], dropna=False)[amount_col].sum().reset_index()
                g[amount_col] = series_to_million(g[amount_col])
                parts = [f"Values shown in {unit}."]
                if month_num:
                    mdisp = datetime(2000, month_num, 1).strftime("%b")
                    if resolved_year or year:
                        mdisp = f"{mdisp} {resolved_year or year}"
                    parts.append(f"Month filter: {mdisp}")
                if dim_filters:
                    applied = []
                    for col, vals in dim_filters.items():
                        applied.append(f"{col} contains [{', '.join(map(str, vals))}]")
                    parts.append("Filters: " + "; ".join(applied))
                if tried_filter_note:
                    parts.append("(No rows matched filters — showing overall results.)")
                st.caption(" | ".join(parts))
                st.dataframe(g)
                return True
        except Exception as e:
            st.warning(f"Rev/Cost view failed: {e}")

    # Offshore / Onsite splits
    if ("offshore" in ql or "onsite" in ql) and "Month" in df.columns:
        loc_col = None
        for c in ["Location", "WorkLocation", "Onsite_Offshore", "Onshore_Offshore"]:
            if c in df.columns:
                loc_col = c
                break
        if loc_col and _safe_has_cols(dff, ["Type", amount_col, loc_col]):
            st.subheader(f"AI Fallback — {loc_col} Split")
            split = dff.groupby([loc_col, "Type"], dropna=False)[amount_col].sum().reset_index()
            split[amount_col] = series_to_million(split[amount_col])
            parts = [f"Values shown in {unit}."]
            if month_num:
                mdisp = datetime(2000, month_num, 1).strftime("%b")
                if resolved_year or year:
                    mdisp = f"{mdisp} {resolved_year or year}"
                parts.append(f"Month filter: {mdisp}")
            if dim_filters:
                applied = []
                for col, vals in dim_filters.items():
                    applied.append(f"{col} contains [{', '.join(map(str, vals))}]")
                parts.append("Filters: " + "; ".join(applied))
            if tried_filter_note:
                parts.append("(No rows matched filters — showing overall results.)")
            st.caption(" | ".join(parts))
            st.dataframe(split)
            return True

    # Realized Rate / Utilization — require UT/HR data (kept informative)
    if any(k in ql for k in ["realized rate", "utilization", "ut"]):
        st.subheader("AI Fallback — Additional KPI")
        st.info("This analysis needs UT/HR datasets (e.g., NetAvailableHours, Utilization%). Please load/connect UT data to enable.")
        return True

    return False

def ai_fallback(user_q: str, df: pd.DataFrame):
    """Main fallback entry."""
    used = _use_kpi_tools_if_available(user_q, df)
    if not used:
        _generic_margin_summary(df, user_q)
    st.success("✅ AI-generated fallback completed.")

# =========================================================
# MAIN ROUTER (prebuilt path preserved + AI fallback)
# =========================================================
if user_question and not st.session_state.clear_chat:
    try:
        res = find_best_matching_qid(user_question)
        best_qid, matched_prompt, score = None, None, None
        if isinstance(res, tuple):
            if len(res) == 3:
                best_qid, matched_prompt, score = res
            elif len(res) == 2:
                best_qid, matched_prompt = res
            elif len(res) == 1:
                best_qid = res[0]
        elif isinstance(res, dict):
            best_qid = res.get("qid") or res.get("best_qid")
            matched_prompt = res.get("prompt") or res.get("matched_prompt")
            score = res.get("score")

        # --- Rule-based overrides BEFORE threshold check ---
        if _is_q1_margin_below_intent(user_question):
            best_qid, matched_prompt, score = "Q1", "Margin % below threshold", 1.0
            st.caption("Q1 override: explicit 'margin% below N' intent detected.")
        elif _is_q3_cb_variance_intent(user_question):
            best_qid, matched_prompt, score = "Q3", "C&B QoQ variation", 1.0
            st.caption("Q3 override: explicit 'C&B quarter-over-quarter change' intent detected.")

        force_ai = user_question.lower().strip().startswith(FREEFORM_TRIGGERS)
        low_score = (score is not None and score < SIM_THRESHOLD)

        if force_ai or low_score or not best_qid:
            if force_ai:
                st.caption("AI mode: freeform override detected.")
            elif low_score:
                st.caption(f"AI mode: matcher score {score:.2f} < {SIM_THRESHOLD}.")
            else:
                st.caption("AI mode: no suitable prebuilt match found.")
            ai_fallback(user_question, df_pnl)
            st.stop()

        # Pre-configured Q1–Q10 path
        try:
            question_module = importlib.import_module(f"questions.question_{best_qid.lower()}")
            run_func = getattr(question_module, "run", None)
            if run_func is None:
                raise AttributeError(f"'run' function not found in module for {best_qid}")

            run_params = inspect.signature(run_func).parameters
            if len(run_params) >= 2:
                result = run_func(df_pnl, user_question)
            else:
                result = run_func(df_pnl)

            st.success("✅ Analysis complete.")
            if isinstance(result, pd.DataFrame):
                st.dataframe(result)
            elif isinstance(result, str):
                st.markdown(result)
            elif isinstance(result, None.__class__):
                pass
            else:
                st.write(result)

        except (ModuleNotFoundError, AttributeError) as e:
            st.info(f"Switching to AI fallback for your question (reason: {e})")
            ai_fallback(user_question, df_pnl)

    except Exception as e:
        st.info("Switching to AI fallback due to an error in routing.")
        st.caption(f"Router error: {e}")
        ai_fallback(user_question, df_pnl)

# -----------------------------
# Prompt bank (preserved)
# -----------------------------
st.markdown("---")
st.markdown("💡 **Try asking:**")
col1, col2 = st.columns(2)
for i, prompt in enumerate(PROMPT_BANK):
    with (col1 if i % 2 == 0 else col2):
        st.button(prompt, on_click=handle_click, args=(prompt,))