import streamlit as st
import pandas as pd
from src.database import supabase
import datetime

st.set_page_config(page_title="Haveli Insights", layout="wide")

# --- PRO UI FACELIFT (Custom CSS) ---
st.markdown("""
    <style>
    div[data-testid="stMetricValue"] {
        font-size: 32px;
        color: #00D1FF;
        font-weight: bold;
    }
    .stDataFrame {
        border: 1px solid #333;
        border-radius: 10px;
    }
    .main {
        padding: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Business Analytics")
st.write("Track your sales performance and inventory health at a glance.")

# Fetch Data from Supabase
with st.spinner("Analyzing shop data..."):
    try:
        # 1. Fetch sales headers
        sales_res = supabase.table("sales").select("*").order("created_at", desc=True).execute()
        
        # 2. FIXED QUERY: Fetch items AND join with sales to get 'created_at'
        items_res = supabase.table("sale_items").select(
            "*, sales(created_at), products(name, cost_price)"
        ).execute()
        
        # 3. Fetch product status
        products_res = supabase.table("products").select("name, current_stock, min_stock_level").execute()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        sales_res, items_res, products_res = None, None, None

if sales_res and sales_res.data:
    df_sales = pd.DataFrame(sales_res.data)
    df_items = pd.DataFrame(items_res.data)
    
    # --- FIXED DATA PROCESSING ---
    if not df_items.empty:
        # Flattening nested JSON from joins
        df_items['product_name'] = df_items['products'].apply(lambda x: x['name'] if x else "Unknown")
        df_items['cost_price'] = df_items['products'].apply(lambda x: float(x['cost_price']) if x else 0.0)
        
        # EXTRACTING created_at from the joined 'sales' dictionary
        df_items['created_at'] = df_items['sales'].apply(lambda x: x['created_at'] if x else None)
        df_items['date'] = pd.to_datetime(df_items['created_at']).dt.date
        
        # Calculations
        df_items['total_cost'] = df_items['cost_price'] * df_items['quantity']
        df_items['total_revenue'] = df_items['price_at_sale'] * df_items['quantity']
        df_items['profit'] = df_items['total_revenue'] - df_items['total_cost']

    # --- TOP ROW: Comparison Metrics (Today vs Yesterday) ---
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    today_sales = df_items[df_items['date'] == today]['total_revenue'].sum() if not df_items.empty else 0
    yesterday_sales = df_items[df_items['date'] == yesterday]['total_revenue'].sum() if not df_items.empty else 0
    
    total_rev = df_items['total_revenue'].sum() if not df_items.empty else 0
    total_prof = df_items['profit'].sum() if not df_items.empty else 0

    # Layout for KPIs
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        
        # Delta shows how much more/less was earned compared to yesterday
        col1.metric("Today's Revenue", f"₹{today_sales:,.2f}", 
                    delta=f"₹{today_sales - yesterday_sales:,.2f} vs yesterday")
        col2.metric("Total Net Profit", f"₹{total_prof:,.2f}")
        col3.metric("Lifetime Revenue", f"₹{total_rev:,.2f}")

    st.divider()

    # --- MIDDLE ROW: Visuals ---
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("🔥 Popular Products")
        if not df_items.empty:
            top_prods = df_items.groupby('product_name')['quantity'].sum().sort_values(ascending=False).head(8)
            st.bar_chart(top_prods, color="#00D1FF")
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
                    use_container_width=True, 
                    hide_index=True
                )
            else:
                st.success("All stock levels are healthy!")

    # --- BOTTOM SECTION: Full Transaction History ---
    st.divider()
    st.subheader("📜 Detailed Sales Log")
    
    # Search functionality
    search_term = st.text_input("🔍 Filter by Customer Phone Number", placeholder="Start typing a number...")
    
    display_history = df_sales.copy()
    if search_term:
        display_history = display_history[display_history['customer_phone'].str.contains(search_term, na=False)]

    if not display_history.empty:
        display_history['Date & Time'] = pd.to_datetime(display_history['created_at']).dt.strftime('%d %b, %I:%M %p')
        display_history['Amount'] = display_history['total_amount'].apply(lambda x: f"₹{x:,.2f}")
        
        history_view = display_history.rename(columns={
            'customer_phone': 'Customer Number',
            'payment_mode': 'Method'
        })[['Date & Time', 'Customer Number', 'Amount', 'Method']]
        
        st.dataframe(history_view, use_container_width=True, hide_index=True)
    else:
        st.info("No matching transactions found.")

else:
    st.info("Welcome to Haveli Electricals! No sales records found yet. Visit the Billing Terminal to get started.")