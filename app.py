"""
The OPAM Dashboard
================================
Operational & Pedagogical Audit of Mathematics Teaching
Tracks how much of the scheduled maths teaching time is actually spent
on instruction vs. assessments vs. lost to non-maths disruptions.

Connects to a private Google Sheet via a Service Account.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="The OPAM Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Security Layer ───────────────────────────────────────────
audit_pwd = st.secrets.get("audit_password")
user_pwd = st.text_input("Audit Credentials", type="password")

if user_pwd != audit_pwd or not user_pwd:
    st.warning("Please enter the audit credentials to view the instructional data.")
    st.stop()

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ── Global ─────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    }

    /* ── Header ─────────────────────────────────── */
    .dashboard-header {
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
    }

    .dashboard-header h1 {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 50%, #fda085 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
        letter-spacing: -0.5px;
    }

    .dashboard-header p {
        color: #8892b0;
        font-size: 0.95rem;
        font-weight: 400;
        margin: 0;
    }

    /* ── KPI Cards ──────────────────────────────── */
    .kpi-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 1.5rem 1.25rem;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.3);
    }

    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        border-radius: 16px 16px 0 0;
    }

    .kpi-card.green::before  { background: linear-gradient(90deg, #00d68f, #38ef7d); }
    .kpi-card.yellow::before { background: linear-gradient(90deg, #f7b731, #ffd32a); }
    .kpi-card.red::before    { background: linear-gradient(90deg, #ff4757, #ff6b81); }

    .kpi-label {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 0.5rem;
    }

    .kpi-card.green .kpi-label  { color: #38ef7d; }
    .kpi-card.yellow .kpi-label { color: #ffd32a; }
    .kpi-card.red .kpi-label    { color: #ff6b81; }

    .kpi-value {
        font-size: 2.8rem;
        font-weight: 900;
        color: #ffffff;
        line-height: 1;
        margin-bottom: 0.35rem;
    }

    .kpi-sub {
        font-size: 0.75rem;
        color: #64748b;
        font-weight: 400;
    }

    /* ── Chart section ──────────────────────────── */
    .chart-container {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 1.5rem;
        margin-top: 1rem;
    }

    .chart-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #e2e8f0;
        margin-bottom: 0.25rem;
    }

    .chart-subtitle {
        font-size: 0.8rem;
        color: #64748b;
        margin-bottom: 1rem;
    }

    /* ── Sidebar ────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
        border-right: 1px solid rgba(255,255,255,0.06);
    }

    section[data-testid="stSidebar"] .stSelectbox label {
        color: #a0aec0;
        font-weight: 600;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .sidebar-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #f093fb;
        margin-bottom: 0.5rem;
    }

    /* Prevent sidebar from being collapsed */
    [data-testid="collapsedControl"] {
        display: none !important;
    }

    /* ── Tabs Full Width ────────────────────────── */
    [data-testid="stTabs"] button[data-baseweb="tab"] {
        flex: 1;
        font-weight: 700;
        font-size: 1.05rem;
        padding-top: 1rem;
        padding-bottom: 1rem;
        color: #a0aec0;
    }

    [data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
        color: #e2e8f0;
        background: rgba(255,255,255,0.03);
    }

    /* ── Table styling ──────────────────────────── */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }

    /* ── Divider ────────────────────────────────── */
    .section-divider {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
        margin: 1.5rem 0;
    }

    /* ── Hide default streamlit elements ────────── */
    #MainMenu { visibility: hidden; }
    header { visibility: hidden; }
    footer { visibility: hidden; }

    /* ── Metric override ────────────────────────── */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 800 !important;
    }

    div[data-testid="stVerticalBlock"] > div {
        gap: 0.5rem;
    }

    /* ── Pill Buttons ───────────────────────────── */
    .pill-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 0.5rem 0 0.75rem 0;
    }

    .pill-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.4rem 0.85rem;
        border-radius: 50px;
        font-size: 0.78rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        cursor: pointer;
        transition: all 0.25s ease;
        border: 1.5px solid;
        letter-spacing: 0.2px;
    }

    .pill-btn .pill-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        flex-shrink: 0;
    }

    /* Inactive states */
    .pill-btn.pill-all       { border-color: #64748b; color: #94a3b8; background: rgba(255,255,255,0.03); }
    .pill-btn.pill-green     { border-color: rgba(0,214,143,0.35); color: #94a3b8; background: rgba(0,214,143,0.05); }
    .pill-btn.pill-yellow    { border-color: rgba(255,211,42,0.35); color: #94a3b8; background: rgba(255,211,42,0.05); }
    .pill-btn.pill-red       { border-color: rgba(255,71,87,0.35); color: #94a3b8; background: rgba(255,71,87,0.05); }

    .pill-btn.pill-green  .pill-dot { background: #00d68f; }
    .pill-btn.pill-yellow .pill-dot { background: #ffd32a; }
    .pill-btn.pill-red    .pill-dot { background: #ff4757; }

    /* Active states */
    .pill-btn.pill-all.active       { background: rgba(148,163,184,0.18); color: #e2e8f0; border-color: #94a3b8; }
    .pill-btn.pill-green.active     { background: rgba(0,214,143,0.18); color: #00d68f; border-color: #00d68f; }
    .pill-btn.pill-yellow.active    { background: rgba(255,211,42,0.18); color: #ffd32a; border-color: #ffd32a; }
    .pill-btn.pill-red.active       { background: rgba(255,71,87,0.18); color: #ff4757; border-color: #ff4757; }

    .pill-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }

    .pill-label {
        font-size: 0.72rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.15rem;
    }

    /* Style Streamlit buttons as pills */
    [data-testid="stButton"] button {
        border-radius: 50px !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        padding: 0.35rem 0.5rem !important;
        transition: all 0.25s ease !important;
        border: 1.5px solid rgba(255,255,255,0.12) !important;
        min-height: 0 !important;
        line-height: 1.3 !important;
    }

    [data-testid="stButton"] button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    }

    [data-testid="stButton"] button[kind="secondary"] {
        background: rgba(255,255,255,0.03) !important;
        color: #94a3b8 !important;
    }

    [data-testid="stButton"] button[kind="primary"] {
        background: rgba(148,163,184,0.18) !important;
        color: #e2e8f0 !important;
        border-color: #94a3b8 !important;
    }
</style>
""", unsafe_allow_html=True)


# ── Data Loading ─────────────────────────────────────────────
@st.cache_data(ttl=600)
def load_data():
    """Load and merge data from both worksheets using computed values."""
    import gspread
    from google.oauth2.service_account import Credentials

    # Build credentials from Streamlit secrets
    creds_info = {k: v for k, v in st.secrets["connections"]["gsheets"].items()
                  if k != "spreadsheet"}
    creds = Credentials.from_service_account_info(
        creds_info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ],
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])

    # ── Read Tracking
    ws_tracking = sh.worksheet("Tracking")
    raw_tracking = ws_tracking.get_all_values()
    if not (raw_tracking and len(raw_tracking) > 0):
        return pd.DataFrame()
    
    # Robust header deduplication
    tracking_headers = []
    for i, h in enumerate(raw_tracking[0]):
        h = h.strip()
        if not h: h = f"Col_{i+1}"
        orig_h, counter = h, 1
        while h in tracking_headers:
            h = f"{orig_h}_{counter}"
            counter += 1
        tracking_headers.append(h)
    
    tracking = pd.DataFrame(raw_tracking[1:], columns=tracking_headers)

    # ── Read Term 1
    ws_term1 = sh.worksheet("Term 1")
    raw_term1 = ws_term1.get_all_values()
    if not (raw_term1 and len(raw_term1) > 0):
        return pd.DataFrame()

    term1_headers = []
    for i, h in enumerate(raw_term1[0]):
        h = h.strip()
        if not h: h = f"Col_{i+1}"
        orig_h, counter = h, 1
        while h in term1_headers:
            h = f"{orig_h}_{counter}"
            counter += 1
        term1_headers.append(h)
    
    term1 = pd.DataFrame(raw_term1[1:], columns=term1_headers)

    # ── Fetch Hidden URLs (Cmd+K)
    import urllib.parse
    try:
        ws_title = urllib.parse.quote(ws_term1.title)
        fields = "sheets/data/rowData/values(hyperlink,textFormatRuns/format/link/uri)"
        req_url = f"https://sheets.googleapis.com/v4/spreadsheets/{sh.id}?ranges='{ws_title}'&fields={fields}"
        resp = sh.client.request('get', req_url)
        data = resp.json()
        
        resource_idx = term1_headers.index("Resource") if "Resource" in term1_headers else -1
        link_column = []
        
        if 'sheets' in data and data['sheets'] and resource_idx >= 0:
            grid_data = data['sheets'][0]['data'][0].get('rowData', [])
            # Skip header row (index 0) if it exists
            for row in grid_data[1:]:
                vals = row.get('values', [])
                url = ""
                if resource_idx < len(vals):
                    cell = vals[resource_idx]
                    # Direct hyperlink property
                    if 'hyperlink' in cell:
                        url = cell['hyperlink']
                    # Rich text runs (Cmd+K)
                    elif 'textFormatRuns' in cell:
                        for run in cell['textFormatRuns']:
                            u = run.get('format', {}).get('link', {}).get('uri')
                            if u:
                                url = u
                                break
                link_column.append(url)
        
        # Match length of term1 DataFrame exactly
        link_column.extend([""] * max(0, len(term1) - len(link_column)))
        term1["Resource_Link"] = link_column[:len(term1)]
    except Exception:
        term1["Resource_Link"] = ""

    # Drop rows where Week is empty/NaN (summary rows at bottom)
    if "Week" in tracking.columns:
        w_series = tracking["Week"]
        if isinstance(w_series, pd.DataFrame): w_series = w_series.iloc[:, 0]
        tracking = tracking[w_series.map(str).str.strip() != ""]

    if "Week" in term1.columns:
        w_series = term1["Week"]
        if isinstance(w_series, pd.DataFrame): w_series = w_series.iloc[:, 0]
        term1 = term1[w_series.map(str).str.strip() != ""]

    # We use "Week", "Date (DD:MM)", "Type of task" as join keys for accuracy
    term1_subset_cols = ["Week", "Date (DD:MM)", "Type of task", "Resource", "Resource_Link"]
    
    # Filter to existing columns
    term1_subset_cols = [c for c in term1_subset_cols if c in term1.columns]

    term1_subset = term1[term1_subset_cols].copy()
    
    # Deduplicate term1 to avoid row explosion during merge
    if all(c in term1_subset.columns for c in ["Week", "Date (DD:MM)", "Type of task"]):
        term1_subset = term1_subset.drop_duplicates(subset=["Week", "Date (DD:MM)", "Type of task"])

    df = tracking.merge(
        term1_subset,
        on=["Week", "Date (DD:MM)", "Type of task"],
        how="left",
    )

    # Nuclear option: Force column uniqueness after merge
    df = df.loc[:, ~df.columns.duplicated()]
    
    # Final safety: Reset index to ensure it's unique
    df = df.reset_index(drop=True)

    # Rename for clarity
    if "Resource" in df.columns:
        df["Description"] = df["Resource"]
    else:
        df["Description"] = ""
        
    if "Resource_Link" in df.columns:
        df = df.rename(columns={"Resource_Link": "Lesson Link"})
    elif "Resource" in df.columns:
        df["Lesson Link"] = df["Resource"]
    else:
        df["Lesson Link"] = ""

    # Clean string columns
    str_cols = ["Type of task", "Lesson Link", "Description", "Explicit or Inquiry"]
    if "Explicit or Inquiry" in df.columns:
        str_cols.append("Explicit or Inquiry")

    for col in str_cols:
        if col in df.columns:
            # Defensive Series selection
            series = df[col]
            if isinstance(series, pd.DataFrame):
                series = series.iloc[:, 0]
            df[col] = series.map(str).str.strip()

    # Ensure Period Taught is numeric
    if "Period Taught" in df.columns:
        df["Period Taught"] = pd.to_numeric(df["Period Taught"], errors="coerce").fillna(0).astype(int)

    return df


def categorize(row):
    """
    Assign a category to each row into three Audit Tracks:
      1. Instructional Leakage: Type of task is "no maths" or Description includes "pat".
      2. Curriculum Overhead: Type of task is "maths assessment".
      3. Learning Core: Explicit or Inquiry is "explicit" or "inquiry".
    """
    task_type = str(row.get("Type of task", "")).strip().lower()
    desc = str(row.get("Description", "")).strip().lower()
    explicit_inquiry = str(row.get("Explicit or Inquiry", "")).strip().lower()

    # Special Exception: PAT Mathematics is Curriculum Overhead
    if "pat mathematics" in desc:
        return "Curriculum Overhead"

    # Priority 1: Instructional Leakage (No maths or contains PAT)
    if task_type == "no maths" or "pat" in desc:
        return "Instructional Leakage"

    # Priority 2: Curriculum Overhead
    if task_type == "maths assessment":
        return "Curriculum Overhead"

    # Priority 3: Learning Core
    if explicit_inquiry in ("explicit", "inquiry"):
        return "Learning Core"

    # Default catch-all
    return "Instructional Leakage"


# ── Load & Process ───────────────────────────────────────────
try:
    df = load_data()
    df["Category"] = df.apply(categorize, axis=1)
    data_loaded = True
except Exception as e:
    data_loaded = False
    error_msg = str(e)

# ── Session State ────────────────────────────────────────────
if "selected_week" not in st.session_state:
    st.session_state.selected_week = "All Weeks"


# ── Header ───────────────────────────────────────────────────
st.markdown("""
<div class="dashboard-header">
    <h1>🔍 The OPAM Dashboard</h1>
    <p>Operational & Pedagogical Audit of Mathematics Teaching</p>
</div>
<hr class="section-divider">
""", unsafe_allow_html=True)


if not data_loaded:
    st.error(f"⚠️ Error loading data. This could be a configuration issue or a problem with the spreadsheet format.")
    
    # Show the actual error message and traceback for easier debugging
    st.warning(f"**Error Details:** {error_msg}")
    with st.expander("🔍 System Traceback (Debug Info)"):
        import traceback
        st.code(traceback.format_exc())
    
    st.info("""
**Setup checklist:**
1. Create a Service Account in Google Cloud Console
2. Enable the Google Sheets API and Google Drive API
3. Download the JSON key file
4. Share your spreadsheet with the service account's `client_email`
5. Paste the key values into `.streamlit/secrets.toml`
    """)
    st.stop()


# ── KPI Calculations ────────────────────────────────────────
total_periods = len(df)
learning_core_count = len(df[df["Category"] == "Learning Core"])
overhead_count = len(df[df["Category"] == "Curriculum Overhead"])
leakage_count = len(df[df["Category"] == "Instructional Leakage"])

actual_periods_taught = learning_core_count + overhead_count

# Percentages
leakage_pct = (leakage_count / total_periods * 100) if total_periods > 0 else 0

# ── Setup Tabs ────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Operational Metrics", "💡 Pedagogical Pulse", "📁 Instructional Assets"])

with tab1:
    st.markdown('<div class="chart-title" style="margin-bottom:1rem;">Operational Metrics</div>', unsafe_allow_html=True)
    
    # ── KPI Grid (2x2) and Donut Chart
    left_col, right_col = st.columns([1.6, 1], gap="large")
    
    with left_col:
        kpi_r1_1, kpi_r1_2 = st.columns(2, gap="medium")
        
        with kpi_r1_1:
            st.markdown(f'''
            <div class="kpi-card green">
                <div class="kpi-label">Total Scheduled Periods</div>
                <div class="kpi-value">{total_periods}</div>
                <div class="kpi-sub">All planned math periods this term</div>
            </div>
            ''', unsafe_allow_html=True)
        
        with kpi_r1_2:
            st.markdown(f'''
            <div class="kpi-card yellow">
                <div class="kpi-label">Actual Periods Taught</div>
                <div class="kpi-value">{actual_periods_taught}</div>
                <div class="kpi-sub">Core + Overhead (excluding leakage)</div>
            </div>
            ''', unsafe_allow_html=True)
            
        kpi_r2_1, kpi_r2_2 = st.columns(2, gap="medium")
        
        with kpi_r2_1:
            st.markdown(f'''
            <div class="kpi-card red">
                <div class="kpi-label">Instructional Leakage</div>
                <div class="kpi-value">{leakage_count}</div>
                <div class="kpi-sub">{leakage_pct:.0f}% lost due to disruptions</div>
            </div>
            ''', unsafe_allow_html=True)

        with kpi_r2_2:
            st.markdown(f'''
            <div class="kpi-card" style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,165,0,0.3); border-radius: 16px; padding: 1.5rem 1.25rem; text-align: center;">
                <div class="kpi-label" style="color: #FFA500;">Maths Assessment</div>
                <div class="kpi-value" style="color: #ffffff;">{overhead_count}</div>
                <div class="kpi-sub">Periods scheduled as assessments</div>
            </div>
            ''', unsafe_allow_html=True)

    with right_col:
        donut_labels = ["Learning Core", "Curriculum Overhead", "Instructional Leakage"]
        donut_values = [learning_core_count, overhead_count, leakage_count]
        donut_colors = ["#00d68f", "#ffd32a", "#ff4757"]

        donut_fig = go.Figure(data=[go.Pie(
            labels=donut_labels,
            values=donut_values,
            hole=0.6,
            marker=dict(colors=donut_colors, line=dict(color="#1e293b", width=2)),
            textinfo="label+percent",
            texttemplate="<b>%{label}</b><br>%{percent}",
            textposition="outside",
            textfont=dict(size=11, family="Inter, sans-serif"),
            hovertemplate="<b>%{label}</b><br>%{value} of " + str(total_periods) + " periods<br>%{percent}<extra></extra>",
            pull=[0.02, 0.02, 0.02],
            direction="clockwise",
            sort=False,
        )])

        donut_fig.update_layout(
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color="#cbd5e1"),
            margin=dict(l=10, r=10, t=10, b=10),
            height=300,
            annotations=[
                dict(
                    text=f"<b style='font-size:1.8rem; color:#e2e8f0;'>{total_periods}</b>"
                         f"<br><span style='font-size:0.75rem; color:#94a3b8;'>periods</span>",
                    x=0.5, y=0.5,
                    font=dict(size=14, color="#e2e8f0", family="Inter, sans-serif"),
                    showarrow=False,
                )
            ],
        )

        st.plotly_chart(donut_fig, use_container_width=True, config={"displayModeBar": False})

    # ── Stacked Bar Chart
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('''
    <div class="chart-title">Period Allocation by Week</div>
    <div class="chart-subtitle">Volume of Learning Core vs. Curriculum Overhead vs. Instructional Leakage.</div>
    ''', unsafe_allow_html=True)

    week_order = sorted(df["Week"].unique(), key=lambda w: int(str(w).replace("W", "")) if str(w).startswith("W") else 999)
    chart_df = df.groupby(["Week", "Category"]).size().reset_index(name="Count")
    category_order = ["Learning Core", "Curriculum Overhead", "Instructional Leakage"]
    color_map = {"Learning Core": "#00d68f", "Curriculum Overhead": "#ffd32a", "Instructional Leakage": "#ff4757"}
    
    fig = px.bar(chart_df, x="Week", y="Count", color="Category", 
                 category_orders={"Week": week_order, "Category": category_order},
                 color_discrete_map=color_map, barmode="stack", 
                 labels={"Count": "Periods", "Week": "Week"})
                 
    # Update layout to match existing style
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#a0aec0", size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=12, color="#cbd5e1"), bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(showgrid=False, tickfont=dict(size=12, color="#94a3b8"), linecolor="rgba(255,255,255,0.1)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=12, color="#94a3b8"), linecolor="rgba(255,255,255,0.1)", dtick=1),
        bargap=0.25, height=420,
    )
    fig.update_traces(marker_line_width=0, opacity=0.92)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── Operational Insights Table
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">🔎 Operational Deep Dive</div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-subtitle">Explore Curriculum Overhead and Instructional Leakage periods.</div>', unsafe_allow_html=True)

    op_df = df[df["Category"].isin(["Curriculum Overhead", "Instructional Leakage"])].copy()
    
    op_left, op_right = st.columns([1, 3], gap="large")
    
    with op_left:
        selected_op_week = st.selectbox("Filter Week", options=["All Weeks"] + week_order, index=0, key="op_week")
        selected_op_cat = st.selectbox("Filter Category", options=["All Categories", "Curriculum Overhead", "Instructional Leakage"], index=0, key="op_cat")
        
        if selected_op_week != "All Weeks":
            op_df = op_df[op_df["Week"] == selected_op_week]
        if selected_op_cat != "All Categories":
            op_df = op_df[op_df["Category"] == selected_op_cat]
            
        st.markdown(f'''
        <div style="background: rgba(255,255,255,0.03); border-radius:12px; padding:1rem; margin-top:0.5rem;">
            <div style="font-size:0.75rem; color:#8892b0; text-transform:uppercase; letter-spacing:1px; margin-bottom:0.5rem;">Periods Found</div>
            <div style="font-size:2rem; font-weight:800; color:#e2e8f0;">{len(op_df)}</div>
        </div>
        ''', unsafe_allow_html=True)

    with op_right:
        cols_to_show_op = ["Week", "Date (DD:MM)", "Type of task", "Description", "Category"]
        if "Lesson Link" in op_df.columns and op_df["Lesson Link"].astype(str).str.contains("http").any():
            cols_to_show_op.append("Lesson Link")
            
        display_op_df = op_df[[c for c in cols_to_show_op if c in op_df.columns]].copy()
        display_op_df = display_op_df.rename(columns={"Date (DD:MM)": "Date"})
        display_op_df = display_op_df.loc[:, ~display_op_df.columns.duplicated()]
        display_op_df = display_op_df.reset_index(drop=True)

        def highlight_op_category(val):
            colors = {"Instructional Leakage": "color: #ff4757; font-weight: 600;", "Curriculum Overhead": "color: #ffd32a; font-weight: 600;"}
            return colors.get(val, "")

        if len(display_op_df) > 0:
            column_config_op = {
                "Lesson Link": st.column_config.LinkColumn("Lesson Link", help="Click to open lesson resource", validate=r"^http", display_text="Open Link 🔗")
            }
            st.dataframe(display_op_df.style.map(highlight_op_category, subset=["Category"]), use_container_width=True, height=min(450, 35 * len(display_op_df) + 38), hide_index=True, column_config=column_config_op)
        else:
            st.info("No periods match the selected filters.")

with tab2:
    st.markdown('<div class="chart-title" style="margin-bottom:1rem;">Pedagogical Pulse</div>', unsafe_allow_html=True)
    
    # Needs sidebar filter for week
    week_options = ["All Weeks"] + week_order
    st.sidebar.markdown('<div class="sidebar-title">Pedagogical Filter</div>', unsafe_allow_html=True)
    selected_pulse_week = st.sidebar.selectbox("Select Week", options=week_options, index=0, key="pulse_week")
    
    pulse_df = df[df["Category"] == "Learning Core"].copy()
    if selected_pulse_week != "All Weeks":
        pulse_df = pulse_df[pulse_df["Week"] == selected_pulse_week]
        
    explicit_count = len(pulse_df[pulse_df["Explicit or Inquiry"].str.lower() == "explicit"])
    inquiry_count = len(pulse_df[pulse_df["Explicit or Inquiry"].str.lower() == "inquiry"])
    total_pulse = explicit_count + inquiry_count
    
    inquiry_pct = (inquiry_count / total_pulse * 100) if total_pulse > 0 else 0
    explicit_pct = (explicit_count / total_pulse * 100) if total_pulse > 0 else 0
    
    # Pulse Metric KPI
    pulse_kpi1, pulse_kpi2 = st.columns(2, gap="medium")
    with pulse_kpi1:
        st.markdown(f'''
        <div class="kpi-card green" style="background: linear-gradient(135deg, rgba(0,214,143,0.1), rgba(0,0,0,0));">
            <div class="kpi-label">Pedagogical Pulse (Inquiry-Led)</div>
            <div class="kpi-value">{inquiry_pct:.0f}%</div>
            <div class="kpi-sub">{inquiry_count} Inquiry periods (Learning Core)</div>
        </div>
        ''', unsafe_allow_html=True)
        
    with pulse_kpi2:
        st.markdown(f'''
        <div class="kpi-card yellow" style="background: linear-gradient(135deg, rgba(255,211,42,0.1), rgba(0,0,0,0));">
            <div class="kpi-label">Explicit Instruction</div>
            <div class="kpi-value">{explicit_pct:.0f}%</div>
            <div class="kpi-sub">{explicit_count} Explicit periods (Learning Core)</div>
        </div>
        ''', unsafe_allow_html=True)
        
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('''
    <div class="chart-title">Inquiry vs. Explicit Instruction</div>
    <div class="chart-subtitle">Direct comparison within the Learning Core.</div>
    ''', unsafe_allow_html=True)

    pulse_fig = go.Figure(data=[
        go.Bar(name='Explicit', x=['Pedagogy'], y=[explicit_count], marker_color='#94a3b8'),
        go.Bar(name='Inquiry', x=['Pedagogy'], y=[inquiry_count], marker_color='#00d68f')
    ])
    pulse_fig.update_layout(
        barmode='group',
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#a0aec0", size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)", dtick=1),
        height=350,
        margin=dict(l=40, r=20, t=40, b=40)
    )
    st.plotly_chart(pulse_fig, use_container_width=True, config={"displayModeBar": False})

with tab3:
    st.markdown('<div class="chart-title" style="margin-bottom:1rem;">🔎 Instructional Assets (Deep Dive)</div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-subtitle">Explore individual periods (excludes Instructional Leakage)</div>', unsafe_allow_html=True)

    asset_df = df[df["Category"].isin(["Learning Core", "Curriculum Overhead"])].copy()
    
    dive_left, dive_right = st.columns([1, 3], gap="large")
    
    with dive_left:
        selected_asset_week = st.selectbox("Filter by Week", options=["All Weeks"] + week_order, index=0, key="asset_week")
        selected_asset_cat = st.selectbox("Filter by Category", options=["All Categories", "Learning Core", "Curriculum Overhead"], index=0, key="asset_cat")
        
        if selected_asset_week != "All Weeks":
            asset_df = asset_df[asset_df["Week"] == selected_asset_week]
        if selected_asset_cat != "All Categories":
            asset_df = asset_df[asset_df["Category"] == selected_asset_cat]
            
        st.markdown(f'''
        <div style="background: rgba(255,255,255,0.03); border-radius:12px; padding:1rem; margin-top:0.5rem;">
            <div style="font-size:0.75rem; color:#8892b0; text-transform:uppercase; letter-spacing:1px; margin-bottom:0.5rem;">Assets Found</div>
            <div style="font-size:2rem; font-weight:800; color:#e2e8f0;">{len(asset_df)}</div>
            <div style="color:#94a3b8; font-size:0.8rem;">periods matching criteria</div>
        </div>
        ''', unsafe_allow_html=True)

    with dive_right:
        cols_to_show = ["Week", "Date (DD:MM)", "Type of task", "Explicit or Inquiry", "Description", "Category"]
        if "Lesson Link" in asset_df.columns and asset_df["Lesson Link"].astype(str).str.contains("http").any():
            cols_to_show.append("Lesson Link")
            
        display_df = asset_df[[c for c in cols_to_show if c in asset_df.columns]].copy()
        display_df = display_df.rename(columns={"Date (DD:MM)": "Date", "Explicit or Inquiry": "Pedagogy"})
        display_df = display_df.loc[:, ~display_df.columns.duplicated()]
        display_df = display_df.reset_index(drop=True)

        def highlight_category(val):
            colors = {"Learning Core": "color: #00d68f; font-weight: 600;", "Curriculum Overhead": "color: #ffd32a; font-weight: 600;"}
            return colors.get(val, "")

        if len(display_df) > 0:
            column_config = {
                "Lesson Link": st.column_config.LinkColumn("Lesson Link", help="Click to open lesson resource", validate=r"^http", display_text="Open Link 🔗")
            }
            st.dataframe(display_df.style.map(highlight_category, subset=["Category"]), use_container_width=True, height=min(450, 35 * len(display_df) + 38), hide_index=True, column_config=column_config)
        else:
            st.info("No periods match the selected filters.")

# ── Footer ───────────────────────────────────────────────────
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#475569; font-size:0.7rem;'>The OPAM Dashboard · Data sourced from 2026 6D Maths Learning Tracker</p>", unsafe_allow_html=True)
