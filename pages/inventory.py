import streamlit as st
import pandas as pd
from src.database import fetch_all_products, bulk_upload_products, supabase

# --- 1. PAGE CONFIG & HIDE DEFAULTS ---
st.set_page_config(page_title="Haveli Inventory", layout="wide", initial_sidebar_state="collapsed")

# --- 2. THEME & PERSISTENT NAVIGATION CSS ---
st.markdown("""
    <style>
    .main { background-color: #0f0f0f; }
    html, body, [class*="css"] { color: #e0e0e0 !important; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebarNav"] {display: none !important;}
    
    /* Fixed Button Styling */
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

    /* Target main containers but prevent styling empty spacer columns */
    div[data-testid="stVerticalBlockBorderWrapper"] > div > div > div[data-testid="stVerticalBlock"] {
        padding: 0px !important;
    }

    /* Clean Card Style for Containers */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #2d2d2d !important;
        border-radius: 12px;
        background-color: #161616 !important;
        padding: 20px !important;
    }
    
    .stTextInput>div>div>input, .stFileUploader section {
        background-color: #222 !important;
        color: white !important;
        border: 1px solid #333 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN PROTECTION ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Access Denied. Please login from the Billing page.")
    if st.button("Go to Login Hub"):
        st.switch_page("app.py")
    st.stop()

# --- 4. PERSISTENT TOP NAVIGATION ---
nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
with nav_col1:
    if st.button("⚡ Billing Hub", use_container_width=True):
        st.switch_page("app.py")
with nav_col2:
    st.markdown('<div style="border: 2px solid #ff5252; border-radius: 8px;">', unsafe_allow_html=True)
    st.button("📦 Inventory", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
with nav_col3:
    if st.button("📊 Insights", use_container_width=True):
        st.switch_page("pages/insights.py")
with nav_col4:
    if st.button("⚙️ Settings", use_container_width=True):
        st.switch_page("pages/settings.py")

st.divider()

# --- 5. CLEAN SIDEBAR ---
with st.sidebar:
    st.markdown("### 🏮 Admin Panel")
    st.write(f"User: **{st.secrets['ADMIN_USER']}**")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.switch_page("app.py")
    st.divider()
    st.info("Haveli Electricals v1.2")

# --- 6. INVENTORY LOGIC ---
st.title("📦 Inventory Control Center")
tab_manage, tab_import = st.tabs(["📋 Manage Stock", "📥 Bulk Import"])

# --- TAB 1: MANAGE STOCK ---
with tab_manage:
    with st.container():
        st.subheader("Live Inventory View")
        products = fetch_all_products()
        
        if products:
            # We fetch products fresh but keep the editor state persistent
            df = pd.DataFrame(products)
            search_query = st.text_input("🔍 Search by Product Name", placeholder="e.g. Anchor, Wire, Fan")
            
            # Apply search filter
            filtered_df = df.copy()
            if search_query:
                filtered_df = df[df['name'].str.contains(search_query, case=False)]

            display_cols = ['name', 'category', 'current_stock', 'selling_price', 'min_stock_level', 'id']
            
            # --- THE GRID EDITOR ---
            # Removing the form wrapper allows the key="inventory_editor" to update instantly
            edited_data = st.data_editor(
                filtered_df[display_cols],
                column_config={
                    "name": st.column_config.TextColumn("Product Name", disabled=True),
                    "category": st.column_config.TextColumn("Category", disabled=True),
                    "current_stock": st.column_config.NumberColumn("In Stock (Qty)"),
                    "selling_price": st.column_config.NumberColumn("Price (Rs.)"),
                    "min_stock_level": st.column_config.NumberColumn("Alert Level"),
                    "id": None # Hide ID but keep it available for processing
                },
                use_container_width=True,
                hide_index=True,
                key="inventory_editor"
            )

            # --- DYNAMIC NOTIFICATION LOGIC ---
            edits = st.session_state.inventory_editor.get("edited_rows", {})
            
            # Use columns to align warning and button without creating empty boxes
            col_warn, col_save = st.columns([2, 1])
            
            with col_warn:
                if edits:
                    st.markdown(f"<p style='color: #FF5252; font-weight: bold; font-size: 16px;'>⚠️ Warning: You have {len(edits)} unsaved row(s). Click Save to sync!</p>", unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color: #00FF00; font-size: 16px;'>✅ All data synced.</p>", unsafe_allow_html=True)

            with col_save:
                if st.button("💾 Save All Changes", use_container_width=True):
                    if edits:
                        with st.spinner("Saving..."):
                            try:
                                for index_str, changes in edits.items():
                                    index = int(index_str)
                                    # We use the filtered_df to find the correct database ID
                                    product_id = filtered_df.iloc[index]['id']
                                    supabase.table("products").update(changes).eq("id", product_id).execute()
                                
                                st.toast("🚀✅ All changes saved to database!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to update: {e}")
                    else:
                        st.warning("No changes detected.")
        else:
            st.warning("Inventory is empty.")

# --- TAB 2: BULK IMPORT ---
with tab_import:
    with st.container():
        st.subheader("Import Stock from CSV or Excel")
        uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx"], label_visibility="collapsed")

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    try:
                        df_upload = pd.read_csv(uploaded_file)
                    except UnicodeDecodeError:
                        uploaded_file.seek(0)
                        df_upload = pd.read_csv(uploaded_file, encoding='latin1')
                else:
                    df_upload = pd.read_excel(uploaded_file)

                df_upload.columns = df_upload.columns.str.strip().str.lower()
                st.write("### Preview of Upload:")
                st.dataframe(df_upload.head(), use_container_width=True)
                
                required_cols = ['name', 'cost_price', 'selling_price', 'current_stock']
                missing = [col for col in required_cols if col not in df_upload.columns]
                
                if missing:
                    st.error(f"Missing required columns: {', '.join(missing)}")
                else:
                    col_spacer, col_action = st.columns([2, 1])
                    with col_action:
                        if st.button("🚀 Confirm and Push", use_container_width=True):
                            with st.spinner("Uploading..."):
                                data_to_insert = df_upload.to_dict(orient='records')
                                bulk_upload_products(data_to_insert)
                                st.success(f"Successfully uploaded {len(data_to_insert)} items!")
                                st.rerun()
                            
            except Exception as e:
                st.error(f"Error reading file: {e}")