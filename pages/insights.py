import streamlit as st
import pandas as pd
from src.database import supabase
import datetime

# --- 1. PAGE CONFIG & HIDE SIDEBAR ---
st.set_page_config(page_title="Haveli Insights", layout="wide", initial_sidebar_state="collapsed")

# --- 2. THEME & PERSISTENT NAVIGATION CSS ---
st.markdown("""
    <style>
    .main { background-color: #0f0f0f; }
    html, body, [class*="css"] { color: #e0e0e0 !important; font-family: 'Inter', sans-serif; }
    
    /* HIDE DEFAULT SIDEBAR NAVIGATION */
    [data-testid="stSidebarNav"] {display: none !important;}

    /* FORCE RED BUTTONS - Prevents default Streamlit Blue */
    .stButton > button {
        border-radius: 6px;
        background-color: #b71c1c !important; 
        color: white !important;
        border: 1px solid #4a0e0e !important;
        font-weight: 600;
    }
    
    .stButton > button:hover {
        background-color: #d32f2f !important;
        border-color: #ff5252 !important;
    }

    /* Analytics Specific UI */
    div[data-testid="stMetricValue"] {
        font-size: 32px;
        color: #ff5252 !important;
        font-weight: bold;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #2d2d2d !important;
        border-radius: 12px;
        background-color: #161616 !important;
    }
    .stDataFrame {
        border: 1px solid #333;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN PROTECTION ---
# Check session state before rendering data
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Access Denied. Please login from the Billing page.")
    if st.button("Go to Login Hub"):
        st.switch_page("app.py")
    st.stop()

# --- 4. PERSISTENT TOP NAVIGATION ---
# Using buttons + st.switch_page ensures state is preserved across pages
nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
with nav_col1:
    if st.button("⚡ Billing Hub", use_container_width=True):
        st.switch_page("app.py")
with nav_col2:
    if st.button("📦 Inventory", use_container_width=True):
        st.switch_page("pages/inventory.py")
with nav_col3:
    # Insights is active - styled with a highlight border
    st.markdown('<div style="border: 2px solid #ff5252; border-radius: 8px;">', unsafe_allow_html=True)
    st.button("📊 Insights", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
with nav_col4:
    if st.button("⚙️ Settings", use_container_width=True):
        st.switch_page("pages/settings.py")

st.divider()

# --- 5. CLEAN SIDEBAR (Admin Info) ---
with st.sidebar:
    st.markdown("### 🏮 Admin Panel")
    st.write(f"User: **{st.secrets['ADMIN_USER']}**")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.switch_page("app.py")
    st.divider()
    st.info("Haveli Electricals v1.2")

# --- 6. ANALYTICS LOGIC ---
st.title("📊 Business Analytics")
st.write("Track your sales performance and inventory health at a glance.")

with st.spinner("Analyzing shop data..."):
    try:
        sales_res = supabase.table("sales").select("*").order("created_at", desc=True).execute()
        items_res = supabase.table("sale_items").select(
            "*, sales(created_at), products(name, cost_price)"
        ).execute()
        products_res = supabase.table("products").select("name, current_stock, min_stock_level").execute()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        sales_res, items_res, products_res = None, None, None

if sales_res and sales_res.data:
    df_sales = pd.DataFrame(sales_res.data)
    df_items = pd.DataFrame(items_res.data)
    
    if not df_items.empty:
        df_items['product_name'] = df_items['products'].apply(lambda x: x['name'] if x else "Unknown")
        df_items['cost_price'] = df_items['products'].apply(lambda x: float(x['cost_price']) if x else 0.0)
        df_items['created_at'] = df_items['sales'].apply(lambda x: x['created_at'] if x else None)
        df_items['date'] = pd.to_datetime(df_items['created_at']).dt.date
        
        df_items['total_cost'] = df_items['cost_price'] * df_items['quantity']
        df_items['total_revenue'] = df_items['price_at_sale'] * df_items['quantity']
        df_items['profit'] = df_items['total_revenue'] - df_items['total_cost']

    # --- TOP ROW: KPI Metrics ---
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    today_sales = df_items[df_items['date'] == today]['total_revenue'].sum() if not df_items.empty else 0
    yesterday_sales = df_items[df_items['date'] == yesterday]['total_revenue'].sum() if not df_items.empty else 0
    total_rev = df_items['total_revenue'].sum() if not df_items.empty else 0
    total_prof = df_items['profit'].sum() if not df_items.empty else 0

    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        col1.metric("Today's Revenue", f"₹{today_sales:,.2f}", 
                    delta=f"₹{today_sales - yesterday_sales:,.2f}")
        col2.metric("Total Net Profit", f"₹{total_prof:,.2f}")
        col3.metric("Lifetime Revenue", f"₹{total_rev:,.2f}")

    st.divider()

    # --- MIDDLE ROW: Visuals ---
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("🔥 Popular Products")
        if not df_items.empty:
            top_prods = df_items.groupby('product_name')['quantity'].sum().sort_values(ascending=False).head(8)
            st.bar_chart(top_prods, color="#ff5252") 
        else:
            st.info("No sales recorded yet.")

    with col_right:
        st.subheader("⚠️ Stock Alerts")
        if products_res and products_res.data:
            df_p = pd.DataFrame(products_res.data)
            low_stock_df = df_p[df_p['current_stock'] <= df_p['min_stock_level']]
            
            if not low_stock_df.empty:
                st.warning(f"{len(low_stock_df)} items need reordering!")
                st.dataframe(
                    low_stock_df[['name', 'current_stock']].sort_values('current_stock'), 
                    use_container_width=True, hide_index=True
                )
            else:
                st.success("All stock levels are healthy!")

    # --- BOTTOM SECTION: Detailed Log ---
    st.divider()
    st.subheader("📜 Detailed Sales Log")
    search_term = st.text_input("🔍 Filter by Customer Number", placeholder="Type phone number...")
    
    display_history = df_sales.copy()
    if search_term:
        display_history = display_history[display_history['customer_phone'].str.contains(search_term, na=False)]

    if not display_history.empty:
        display_history['Date & Time'] = pd.to_datetime(display_history['created_at']).dt.strftime('%d %b, %I:%M %p')
        display_history['Amount'] = display_history['total_amount'].apply(lambda x: f"₹{x:,.2f}")
        history_view = display_history.rename(columns={'customer_phone': 'Customer', 'payment_mode': 'Method'})[['Date & Time', 'Customer', 'Amount', 'Method']]
        st.dataframe(history_view, use_container_width=True, hide_index=True)

else:
    st.info("No records found yet.")