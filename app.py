# app.py
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, date, timedelta
import calendar
import io
import json

import plotly.express as px
from sklearn.linear_model import LinearRegression

# Try Prophet; fallback if not available
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except Exception:
    PROPHET_AVAILABLE = False

# Try statsmodels SARIMAX as fallback
try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    STATSMODEL_AVAILABLE = True
except Exception:
    STATSMODEL_AVAILABLE = False

# Optional: gspread for Google Sheets sync (only used if credentials provided)
try:
    import gspread
    GSPREAD_AVAILABLE = True
except Exception:
    GSPREAD_AVAILABLE = False

# Custom CSS for personal, fun, and quirky UI
def apply_custom_styling():
    st.markdown("""
    <style>
    /* Main app styling */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Comic Sans MS', cursive, sans-serif;
    }
    
    /* Title styling */
    .main-title {
        background: linear-gradient(45deg, #ff6b6b, #ffd93d, #6bcf7f, #4d9fff);
        background-size: 300% 300%;
        animation: rainbow 3s ease infinite;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    @keyframes rainbow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Container styling */
    .stContainer {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #ff9a9e 0%, #fecfef 100%);
        border-radius: 0 20px 20px 0;
    }
    
    /* Form styling */
    .stForm {
         background: linear-gradient(135deg, #ffe0e6, #fdf2f8);
         border-radius: 15px;
         padding: 1.5rem;
         border: 3px dashed #fd79a8;
    box-shadow: 0 4px 15px rgba(253, 121, 168, 0.3);
    }

    /* Form styling */
    .stForm {
         background: linear-gradient(135deg, #ffe0e6, #fdf2f8);
         border-radius: 15px;
         padding: 1.5rem;
         border: 3px dashed #fd79a8;
         box-shadow: 0 4px 15px rgba(253, 121, 168, 0.3);
    }
    
    # ========== ADD THE NEW CSS HERE ========== #
    
    /* Form labels/descriptors styling - ADD THIS SECTION */
    .stForm label {
        color: #2d3436 !important;
        font-weight: bold !important;
        font-size: 1rem !important;
    }

    /* More specific targeting for different input types */
    .stForm .stTextInput label,
    .stForm .stNumberInput label,
    .stForm .stSelectbox label,
    .stForm .stDateInput label,
    .stForm .stTextArea label,
    .stForm .stCheckbox label {
        color: #2d3436 !important;
        font-weight: bold !important;
    }

    /* Target Streamlit's internal label classes */
    .stForm [data-testid="stWidgetLabel"] {
        color: #2d3436 !important;
    }

    /* Alternative approach - target by element structure */
    .stForm > div > div > label,
    .stForm div[data-testid="element-container"] label {
        color: #2d3436 !important;
        font-weight: bold !important;
    }

    /* For any markdown text within forms that might be acting as labels */
    .stForm .stMarkdown {
        color: #2d3436 !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(45deg, #ff6b6b, #ff8e53);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: bold;
        font-size: 1.1rem;
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
        transition: all 0.3s ease;
        transform: translateY(0px);
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(255, 107, 107, 0.6);
        background: linear-gradient(45deg, #ff8e53, #ff6b6b);
    }
    
    /* Metric styling */
    .css-1xarl3l {
        background: linear-gradient(135deg, #a8edea, #fed6e3);
        border-radius: 15px;
        padding: 1rem;
        border-left: 5px solid #fd79a8;
        margin: 0.5rem 0;
    }
    
    /* Progress bar styling */
    .stProgress .css-1cpxqw2 {
        background: linear-gradient(90deg, #ff6b6b, #ffd93d, #6bcf7f);
        border-radius: 10px;
        height: 20px;
    }
    
    /* Input field styling */
    .stTextInput > div > div > input {
        border-radius: 20px;
        border: 2px solid #fd79a8;
        background: rgba(255, 255, 255, 0.9);
    }
    
    .stNumberInput > div > div > input {
        border-radius: 20px;
        border: 2px solid #fd79a8;
        background: rgba(255, 255, 255, 0.9);
    }
    
    .stSelectbox > div > div > select {
        border-radius: 20px;
        border: 2px solid #fd79a8;
        background: rgba(255, 255, 255, 0.9);
    }
    
    /* Success/Error message styling */
    .stSuccess {
        background: linear-gradient(135deg, #6bcf7f, #a8e6cf);
        border-radius: 15px;
        border-left: 5px solid #00b894;
        animation: bounce 0.5s ease;
    }
    
    .stError {
        background: linear-gradient(135deg, #ff6b6b, #ffa8a8);
        border-radius: 15px;
        border-left: 5px solid #e17055;
        animation: shake 0.5s ease;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #ffd93d, #ffed4e);
        border-radius: 15px;
        border-left: 5px solid #fdcb6e;
    }
    
    .stInfo {
        background: linear-gradient(135deg, #74b9ff, #a8d8ff);
        border-radius: 15px;
        border-left: 5px solid #0984e3;
    }
    
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-10px); }
        60% { transform: translateY(-5px); }
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
    
    /* Dataframe styling */
    .dataframe {
        border-radius: 15px;
        overflow: hidden;
        border: 2px solid #fd79a8;
    }
    
    /* Chart container styling */
    .plotly-graph-div {
        border-radius: 15px;
        background: rgba(255, 255, 255, 0.9);
        padding: 1rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* Header styling for sections */
    h1, h2, h3 {
        color: #2d3436;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    
    /* Fun emoji background pattern */
    .fun-bg::before {
        content: "💸 💰 📊 💳 🎯 💸 💰 📊 💳 🎯";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        opacity: 0.05;
        font-size: 2rem;
        line-height: 3rem;
        pointer-events: none;
        z-index: -1;
    }
    </style>
    
    <div class="fun-bg"></div>
    """, unsafe_allow_html=True)

# ---------------------
# File paths & helpers
# ---------------------
DATA_DIR = Path("data")
EXPENSES_FILE = DATA_DIR / "expenses.csv"
RECURRING_FILE = DATA_DIR / "recurring.csv"
SETTINGS_FILE = DATA_DIR / "settings.json"

def ensure_files():
    DATA_DIR.mkdir(exist_ok=True)
    if not EXPENSES_FILE.exists():
        df = pd.DataFrame(columns=["Date","Category","Amount","PaymentType","Notes","IsRecurring","CreatedAt"])
        df.to_csv(EXPENSES_FILE, index=False)
    if not RECURRING_FILE.exists():
        df = pd.DataFrame(columns=["Name","Category","Amount","Frequency","StartDate","DayOfMonth","LastApplied"])
        df.to_csv(RECURRING_FILE, index=False)
    if not SETTINGS_FILE.exists():
        default = {
            "monthly_budget": None,
            "monthly_income": None,
            "savings_goal": None
        }
        with open(SETTINGS_FILE, "w") as f:
            json.dump(default, f)

def load_settings():
    with open(SETTINGS_FILE,"r") as f:
        return json.load(f)

def save_settings(settings):
    with open(SETTINGS_FILE,"w") as f:
        json.dump(settings, f)

def load_expenses():
    df = pd.read_csv(EXPENSES_FILE, parse_dates=["Date"], dayfirst=False)
    if df.empty:
        return df
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    return df

def append_expense(row: dict):
    df = load_expenses()
    ndf = pd.DataFrame([row])
    ndf.to_csv(EXPENSES_FILE, mode='a', header=False, index=False)
    return

def load_recurring():
    df = pd.read_csv(RECURRING_FILE)
    if df.empty:
        return df
    df["StartDate"] = pd.to_datetime(df["StartDate"]).dt.date
    return df

def save_recurring(df):
    df.to_csv(RECURRING_FILE, index=False)
    
def delete_expense_by_index(df, index_to_delete):
    """Delete expense by DataFrame index and save"""
    df_updated = df.drop(index_to_delete).reset_index(drop=True)
    df_updated.to_csv(EXPENSES_FILE, index=False)
    return df_updated

def delete_recurring_by_index(df, index_to_delete):
    """Delete recurring payment by DataFrame index and save"""
    df_updated = df.drop(index_to_delete).reset_index(drop=True)
    df_updated.to_csv(RECURRING_FILE, index=False)
    return df_updated

def check_duplicate_expense(expenses_df, date_val, amount_val, category_val):
    """Check if similar expense exists"""
    if expenses_df.empty:
        return False
    similar = expenses_df[
        (expenses_df['Date'] == date_val) & 
        (expenses_df['Amount'] == amount_val) & 
        (expenses_df['Category'] == category_val)
    ]
    return len(similar) > 0

# ---------------------
# Recurring handling
# ---------------------
def generate_virtual_recurring_for_month(rec_df, year, month):
    """Return list of generated recurring rows for the given month (DOES NOT persist unless persist=True)."""
    generated = []
    for _, row in rec_df.iterrows():
        day = int(row.get("DayOfMonth", pd.to_datetime(row["StartDate"]).day))
        # clamp day to days in month
        last_day = calendar.monthrange(year, month)[1]
        day = min(day, last_day)
        dt = date(year, month, day)
        generated.append({
            "Date": dt,
            "Category": row["Category"],
            "Amount": float(row["Amount"]),
            "PaymentType": "Recurring",
            "Notes": f"Recurring: {row['Name']}",
            "IsRecurring": True,
            "CreatedAt": datetime.now()
        })
    if generated:
        return pd.DataFrame(generated)
    else:
        return pd.DataFrame(columns=["Date","Category","Amount","PaymentType","Notes","IsRecurring","CreatedAt"])

def persist_recurring_for_month(rec_df, year, month):
    """Persist recurring entries for this month (mark LastApplied) to avoid duplicates."""
    today_key = f"{year}-{month:02d}"
    # load expenses and persist only those that have not been applied this month
    ex = load_expenses()
    to_add = []
    for i, row in rec_df.iterrows():
        last = row.get("LastApplied", "")
        if last == today_key:
            continue
        day = int(row.get("DayOfMonth", pd.to_datetime(row["StartDate"]).day))
        last_day = calendar.monthrange(year, month)[1]
        day = min(day, last_day)
        dt = date(year, month, day)
        to_add.append({
            "Date": dt,
            "Category": row["Category"],
            "Amount": float(row["Amount"]),
            "PaymentType": "Recurring",
            "Notes": f"Recurring: {row['Name']}",
            "IsRecurring": True,
            "CreatedAt": datetime.now()
        })
        # update last applied
        rec_df.at[i,"LastApplied"] = today_key
    if to_add:
        pd.DataFrame(to_add).to_csv(EXPENSES_FILE, mode='a', header=False, index=False)
        save_recurring(rec_df)
    return len(to_add)

# ---------------------
# Forecasting utilities
# ---------------------
def daily_totals(expenses_df, year, month):
    """Return a Series indexed by date for every day from 1..today (or full month if needed)."""
    if expenses_df is None or expenses_df.empty:
        return pd.Series(dtype=float)
    # Filter to this month
    df = expenses_df.copy()
    df = df[df["Date"].apply(lambda d: d.year==year and d.month==month)]
    if df.empty:
        return pd.Series(dtype=float)
    df2 = df.groupby("Date")["Amount"].sum().sort_index()
    # full index
    start = date(year, month, 1)
    end = date(year, month, calendar.monthrange(year, month)[1])
    idx = pd.date_range(start, end).date
    s = pd.Series(0.0, index=idx)
    for d,v in df2.items():
        s[d] = v
    return s

def forecast_month(expenses_df, year, month, threshold_days=10):
    """
    Forecast total spend for the month.
    - returns dict: {'status': 'not_enough_data'/'linear'/'prophet'/'sarimax', 'predicted_total': x, 'model': name}
    """
    s = daily_totals(expenses_df, year, month)
    if len(s.dropna()) == 0:
        return {"status":"no_data"}
    days_in_month = calendar.monthrange(year,month)[1]
    today = date.today()
    # We'll use days up to today for fitting
    # count meaningful days (non-zero or at least presence)
    # Use actual days passed to avoid overfitting if month early
    days_passed = min(today.day, days_in_month) if today.year==year and today.month==month else days_in_month
    used_series = s[:date(year,month,days_passed)]
    # require effective data count threshold
    non_zero_count = (used_series != 0).sum()
    # but allow forecasting if we have at least threshold_days days with any recorded pattern
    if days_passed < threshold_days and non_zero_count < max(3, threshold_days//2):
        return {"status":"not_enough_data", "days_collected": days_passed, "non_zero_days": int(non_zero_count)}
    total_so_far = used_series.sum()
    # Linear regression fallback (fast)
    try:
        # Prepare X as day index
        X = np.arange(1, days_passed+1).reshape(-1,1)
        y = used_series.values.reshape(-1,1)
        lr = LinearRegression()
        lr.fit(X, y)
        # predict remaining days:
        future_days = np.arange(days_passed+1, days_in_month+1).reshape(-1,1)
        if len(future_days)>0:
            preds = lr.predict(future_days).clip(min=0).flatten()
            future_sum = preds.sum()
        else:
            future_sum = 0.0
        predicted_total = float(total_so_far + future_sum)
        model_name = "linear_regression"
        # If enough history and prophet available, try prophet for better seasonality
        if (days_passed >= 30) and PROPHET_AVAILABLE:
            # prepare prophet dataframe
            dfp = used_series.reset_index()
            dfp.columns = ["ds","y"]
            dfp["ds"] = pd.to_datetime(dfp["ds"])
            m = Prophet(daily_seasonality=True, weekly_seasonality=True)
            m.fit(dfp)
            future = m.make_future_dataframe(periods=(days_in_month-days_passed), freq='D')
            forecast = m.predict(future)
            # sum predicted month total
            forecasted = forecast[forecast['ds'].dt.month==month]['yhat'].sum()
            predicted_total = float(forecasted)
            model_name = "prophet"
        elif (days_passed >= 30) and (not PROPHET_AVAILABLE) and STATSMODEL_AVAILABLE:
            # fall back to SARIMAX with simple order (p,d,q) = (1,1,1)
            y_train = used_series.astype(float).values
            try:
                model = SARIMAX(y_train, order=(1,1,1), enforce_stationarity=False, enforce_invertibility=False)
                res = model.fit(disp=False)
                steps = days_in_month - days_passed
                if steps>0:
                    preds = res.get_forecast(steps=steps).predicted_mean
                    future_sum = max(0.0, float(preds.sum()))
                else:
                    future_sum = 0.0
                predicted_total = float(total_so_far + future_sum)
                model_name = "sarimax"
            except Exception:
                pass
        return {"status":"ok", "predicted_total": round(predicted_total,2), "model": model_name, "total_so_far": float(total_so_far)}
    except Exception as e:
        return {"status":"error", "error": str(e)}

# ---------------------
# Google Sheets sync (optional)
# ---------------------
def gsheets_append_row(sheet_name, row_dict):
    """
    append a single row dict to sheet with title sheet_name.
    Uses creds provided in st.secrets['gcp_service_account'] as JSON string (recommended)
    """
    if not GSPREAD_AVAILABLE:
        st.warning("gspread not installed; cannot sync to Google Sheets")
        return False
    if "gcp_service_account" not in st.secrets:
        st.warning("No Google service account credentials found in Streamlit secrets.")
        return False
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    gc = gspread.service_account_from_dict(creds_dict)
    # sheet_name here is the spreadsheet key or title; for simplicity look up by title
    try:
        sh = gc.open(sheet_name)
    except Exception:
        sh = gc.create(sheet_name)  # create if not exists
    ws = sh.sheet1
    # ensure header
    header = ws.row_values(1)
    if not header:
        headers = list(row_dict.keys())
        ws.append_row(headers)
    # append values in header order
    vals = [row_dict.get(h, "") for h in ws.row_values(1)]
    ws.append_row(vals)
    return True

# ---------------------
# UI / App
# ---------------------
st.set_page_config(page_title="Babo's Smart Expense Predictor", page_icon="💸", layout="wide")

# Apply custom styling
apply_custom_styling()

ensure_files()
settings = load_settings()

# Fun animated title
st.markdown('<h1 class="main-title">💸✨ Babo\'s Magical Money Tracker ✨💸</h1>', unsafe_allow_html=True)

APP_PASSWORD = "anniversary17"   # <- set your password here

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if not st.session_state["authenticated"]:
    pwd = st.text_input("Enter app password", type="password")
    if st.button("Login"):
        if pwd == APP_PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()   # ✅ new function in latest Streamlit
        else:
            st.error("Wrong password.")
    st.stop()


# Sidebar: settings
with st.sidebar:
    st.markdown("#### ⚙️ Magic Settings ✨")
    monthly_budget = st.number_input("Set monthly budget (₹)", min_value=0.0, value=settings.get("monthly_budget") or 0.0, step=100.0)
    monthly_income = st.number_input("Set monthly income (₹)", min_value=0.0, value=settings.get("monthly_income") or 0.0, step=500.0)
    savings_goal = st.number_input("Set monthly savings goal (₹)", min_value=0.0, value=settings.get("savings_goal") or 0.0, step=500.0)
    if st.button("Save settings"):
        settings["monthly_budget"] = float(monthly_budget) if monthly_budget>0 else None
        settings["monthly_income"] = float(monthly_income) if monthly_income>0 else None
        settings["savings_goal"] = float(savings_goal) if savings_goal>0 else None
        save_settings(settings)
        st.success("⚙️ Settings locked and loaded! 🚀")

    st.markdown("---")
    st.markdown("#### 🔁 Monthly Money Vampires 🧛‍♂️")
    if st.checkbox("Apply recurring payments for this month (persist to expenses)"):
        rec_df = load_recurring()
        applied = persist_recurring_for_month(rec_df, date.today().year, date.today().month)
        st.info(f"🔄 {applied} recurring payments have been unleashed for this month!")
    if st.button("Open recurring manager"):
        st.write("Manage recurring in the main page below")

    st.markdown("---")
    st.markdown("#### 💾 Save My Soul (Data) 😇")
    if st.button("Export expenses CSV"):
        df = load_expenses()
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, file_name="expenses_export.csv", mime="text/csv")
    st.caption("Enable Google Sheets sync in the app (main page) for cloud persistence.")

# Main: expense entry
col1, col2 = st.columns([2,1])
with col1:
    st.markdown("### 🛍️ Oops, I Spent Money Again! 💸")
    with st.form("add_expense"):
        d = st.date_input("Date", value=date.today())
        cat = st.selectbox("Category", ["Food","Shopping","Rent","Travel","Subscriptions","Utilities","Other"])
        amt = st.number_input("Amount (₹)", min_value=0.0, step=10.0, format="%.2f")
        ptype = st.selectbox("Payment Type", ["Card","UPI","Cash","Recurring"])
        notes = st.text_input("Notes (optional)")
        is_rec = st.checkbox("Mark as recurring (ad-hoc)", value=False)
        submitted = st.form_submit_button("Add Expense")
        if submitted:
            if amt <= 0:
                st.error("Amount must be > 0")
            else:
                current_expenses = load_expenses()
                if check_duplicate_expense(current_expenses, d, float(amt), cat):
                    st.warning("⚠️ Similar expense exists for this date/amount/category. Continue anyway?")
                    if st.button("Yes, add anyway", key="confirm_duplicate"):
                        row = {
                            "Date": d,
                            "Category": cat,
                            "Amount": float(amt),
                            "PaymentType": ptype,
                            "Notes": notes,
                            "IsRecurring": bool(is_rec),
                            "CreatedAt": datetime.now()
                        }
                        append_expense(row)
                        st.success("💸 Another one bites the dust! Added successfully! 🎉")
                else:
                    row = {
                        "Date": d,
                        "Category": cat,
                        "Amount": float(amt),
                        "PaymentType": ptype,
                        "Notes": notes,
                        "IsRecurring": bool(is_rec),
                        "CreatedAt": datetime.now()
                    }
                    append_expense(row)
                    st.success("💸 Another one bites the dust! Added successfully! 🎉")
                # optional Google Sheets sync if configured
                try:
                    if "gcp_service_account" in st.secrets and st.button("Sync this entry to Google Sheets (press once)"):
                        try:
                            gsheets_append_row(st.secrets.get("gspread_spreadsheet_name","SmartExpenses"), {
                                "Date": str(row["Date"]),
                                "Category": row["Category"],
                                "Amount": row["Amount"],
                                "PaymentType": row["PaymentType"],
                                "Notes": row["Notes"]
                            })
                            st.success("☁️ Beamed up to the cloud! Google Sheets updated! 🛸")
                        except Exception as e:
                            st.error("Google Sheets sync failed: " + str(e))
                except:
                    pass

with col2:
    st.markdown("### 🔄 Set It & Forget It (Bills) 📅")
    with st.form("recurring_form"):
        rname = st.text_input("Name (e.g., Rent)")
        rcat = st.selectbox("Category", ["Rent","Subscriptions","Utilities","Other"])
        ramt = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
        freq = st.selectbox("Frequency", ["Monthly","Weekly"])
        start = st.date_input("Start date", value=date.today())
        dom = st.number_input("Day of month to apply", min_value=1, max_value=28, value=start.day)
        sub2 = st.form_submit_button("Save recurring")
        if sub2:
            if not rname.strip():
                st.error("Name is required!")
            elif ramt <= 0:
                st.error("Amount must be greater than 0!")
            else:
                rec_df = load_recurring()
                new = {
                    "Name": rname,
                    "Category": rcat,
                    "Amount": float(ramt),
                    "Frequency": freq,
                    "StartDate": start,
                    "DayOfMonth": int(dom),
                    "LastApplied": ""
                }
                rec_df = pd.concat([rec_df, pd.DataFrame([new])], ignore_index=True)
                save_recurring(rec_df)
                st.success("🔄 Recurring payment trapped! It's now in the vault! 🏦")

st.markdown("---")
# Dashboard
st.markdown("### 📊 The Damage Report 😅")
expenses = load_expenses()
recurring = load_recurring()

# show month summary
# ---------- Safe metrics block (replace the old block with this) ----------
from datetime import date as _date  # local alias to avoid shadowing if needed

# Ensure expenses DataFrame exists
if expenses is None:
    expenses = pd.DataFrame()

# Coerce Date column to python date objects (safe even if already date)
if not expenses.empty and "Date" in expenses.columns:
    try:
        expenses["Date"] = pd.to_datetime(expenses["Date"]).dt.date
    except Exception:
        # if conversion fails, leave as-is (we'll guard later)
        pass

# Coerce Amount to numeric to avoid string issues
if not expenses.empty and "Amount" in expenses.columns:
    expenses["Amount"] = pd.to_numeric(expenses["Amount"], errors="coerce").fillna(0.0)

# Today's date as a python date object
today_date = _date.today()
year, month = today_date.year, today_date.month

# Filter expenses for this month (safe even if some Date values are NaN)
if not expenses.empty and "Date" in expenses.columns:
    this_month_expenses = expenses[
        expenses["Date"].apply(lambda d: (hasattr(d, "year") and d.year == year and d.month == month) if pd.notna(d) else False)
    ]
else:
    this_month_expenses = pd.DataFrame()

# Totals as float (safe for formatting)
total_month = float(this_month_expenses["Amount"].sum()) if not this_month_expenses.empty else 0.0

# Today's total (compare date objects)
if not this_month_expenses.empty and "Date" in this_month_expenses.columns:
    try:
        today_total = float(this_month_expenses[this_month_expenses["Date"] == today_date]["Amount"].sum())
    except Exception:
        # Fallback: try comparing by ISO string if types mismatch
        try:
            today_str = today_date.isoformat()
            today_total = float(
                this_month_expenses[pd.to_datetime(this_month_expenses["Date"]).dt.strftime("%Y-%m-%d") == today_str]["Amount"].sum()
            )
        except Exception:
            today_total = 0.0
else:
    today_total = 0.0

# Display metrics (guaranteed numeric strings)
c1, c2, c3 = st.columns(3)
c1.metric("Today spent (₹)", f"{today_total:.2f}")
c2.metric("This month so far (₹)", f"{total_month:.2f}")

budget_val = float(settings.get("monthly_budget") or 0.0)
c3.metric("Budget (₹)", f"{budget_val:.2f}")
# ------------------------------------------------------------------------

# Category pie
if not this_month_expenses.empty:
    cat_df = this_month_expenses.groupby("Category")["Amount"].sum().reset_index()
    fig1 = px.pie(cat_df, names="Category", values="Amount", title="Category split")
    st.plotly_chart(fig1, use_container_width=True)

# daily trend
s = daily_totals(expenses, year, month)
if not s.empty:
    df_line = s.reset_index()
    df_line.columns = ["Date","Amount"]
    fig2 = px.line(df_line, x="Date", y="Amount", title="Daily spend (this month)")
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("No expenses logged for this month yet. Add some to see trends.")

# Forecasting
st.markdown("### 🔮 Crystal Ball Says... 💫")
fc = forecast_month(expenses, year, month, threshold_days=10)
if fc.get("status") in ("no_data","not_enough_data"):
    st.info("Not enough data for a reliable forecast yet. Keep logging—I'll get smarter! 🧠✨")
else:
    predicted = fc.get("predicted_total", None)
    if predicted is None:
        st.error("Forecast error: " + str(fc.get("error","unknown")))
    else:
        st.write(f"Predicted total spend this month: **₹{predicted:.2f}** (model: {fc.get('model')})")
        # money meter vs budget
        if settings.get("monthly_budget"):
            budget = settings["monthly_budget"]
            left = budget - predicted
            pct = max(0.0, min(1.0, predicted/budget)) if budget>0 else 0.0
            st.progress(min(int(pct*100),100))
            if left >= 0:
                st.success(f"🎯 On track! Predicted to have ₹{left:.2f} left in budget. You're doing great! 🌟")
            else:
                st.warning(f"⚠️ At this pace you will exceed budget by ₹{abs(left):.2f} — time to eat more maggi! 🍜")
        else:
            st.info("Set your monthly budget in sidebar to compare against forecast.")

# Savings monitor
st.markdown("### 🐷 Piggy Bank Status 💰")
income = settings.get("monthly_income") or 0.0
sgoal = settings.get("savings_goal") or 0.0
if income>0:
    predicted_spend = fc.get("predicted_total") if fc.get("predicted_total") else total_month
    predicted_savings = float(income - predicted_spend)
    st.write(f"Monthly income: ₹{income:.2f}")
    st.write(f"Predicted savings (income - predicted spend): **₹{predicted_savings:.2f}**")
    if sgoal>0:
        pct = max(0.0, min(1.0, predicted_savings / sgoal))
        st.write(f"Savings goal: ₹{sgoal:.2f}")
        st.progress(min(int(pct*100),100))
        if pct>=1.0:
            st.balloons()
            st.success("🎉 AMAZING! Predicted to hit or exceed your savings goal! You're a financial wizard! ✨🧙‍♂️")
        else:
            st.info(f"Predicted to reach {int(pct*100)}% of savings goal. Keep going! 💪")
else:
    st.info("Set monthly income in settings to enable savings predictions.")

# Delete/Edit functionality
st.markdown("### 🗑️ Fix My Oops Moments")

tab1, tab2 = st.tabs(["Delete Expenses", "Delete Recurring"])

with tab1:
    st.markdown("#### Recent Expenses")
    current_expenses = load_expenses()
    if not current_expenses.empty:
        # Show last 15 expenses
        recent_expenses = current_expenses.tail(15).iloc[::-1]  # Reverse to show newest first
        
        for idx, row in recent_expenses.iterrows():
            col1, col2 = st.columns([5, 1])
            with col1:
                st.write(f"**{row['Date']}** | {row['Category']} | ₹{row['Amount']:.2f} | {row['PaymentType']} | {row['Notes']}")
            with col2:
                if st.button("🗑️", key=f"del_exp_{idx}", help="Delete this expense"):
                    delete_expense_by_index(current_expenses, idx)
                    st.success("Deleted!")
                    st.rerun()
    else:
        st.info("No expenses to delete")

with tab2:
    st.markdown("#### Recurring Payments")
    current_recurring = load_recurring()
    if not current_recurring.empty:
        for idx, row in current_recurring.iterrows():
            col1, col2 = st.columns([5, 1])
            with col1:
                st.write(f"**{row['Name']}** | {row['Category']} | ₹{row['Amount']:.2f} | {row['Frequency']} | Day {row['DayOfMonth']}")
            with col2:
                if st.button("🗑️", key=f"del_rec_{idx}", help="Delete this recurring payment"):
                    delete_recurring_by_index(current_recurring, idx)
                    st.success("Deleted!")
                    st.rerun()
    else:
        st.info("No recurring payments to delete")

# Recurring list
st.markdown("### 🔄 Your Money Subscriptions 📋")
if recurring is None or recurring.empty:
    st.info("No recurring payments saved. Living life one expense at a time! 🎭")
else:
    st.dataframe(recurring)

# Allow exporting filtered data
st.markdown("### 📤📥 Data Magic Tricks ✨")
if st.button("Download full expense CSV"):
    csv = load_expenses().to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, file_name="expenses_full.csv", mime="text/csv")

uploaded = st.file_uploader("Upload CSV to append (must have same columns)", type=["csv"])
if uploaded is not None:
    try:
        newdf = pd.read_csv(uploaded, parse_dates=["Date"])
        # sanitize & append
        newdf["CreatedAt"] = datetime.now()
        newdf.to_csv(EXPENSES_FILE, mode='a', header=False, index=False)
        st.success("📂 File absorbed into the matrix! Data updated! 🤖")
    except Exception as e:
        st.error("Upload failed: " + str(e))

# Anniversary Easter egg
if today.day == 17:
    st.balloons()
    st.success("🎉 HAPPY ANNIVERSARY MY LOVE! 💕 This app was crafted with extra love just for you! ✨💖✨")

# End of app with personal footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; margin-top: 3rem; padding: 2rem; 
            background: linear-gradient(135deg, #667eea, #764ba2); 
            border-radius: 20px; color: white;">
    <h3>💖 Crafted with infinite love 💖</h3>
    <p style="font-size: 1.2rem;">From your coding Mathukuttan 👨‍💻💕</p>
    <p>Made special just for my favorite person in the universe 🌟</p>
</div>
""", unsafe_allow_html=True)
