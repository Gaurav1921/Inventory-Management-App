import streamlit as st
import pandas as pd
from src.database import fetch_all_products, bulk_upload_products, supabase

st.set_page_config(page_title="Haveli Inventory", layout="wide")

st.title("📦 Inventory Control Center")

# Create two tabs: one for managing existing stock, one for adding new things
tab_manage, tab_import = st.tabs(["📋 Manage Stock", "📥 Bulk Import"])

# --- TAB 1: MANAGE STOCK ---
with tab_manage:
    st.subheader("Live Inventory View")
    
    # Fetch latest data
    products = fetch_all_products()
    
    if products:
        df = pd.DataFrame(products)
        
        # 1. Search Filter (Ease of Use)
        search_query = st.text_input("🔍 Search by Product Name", placeholder="e.g. Anchor, Wire, Fan")
        
        if search_query:
            df = df[df['name'].str.contains(search_query, case=False)]

        # 2. Editable Data Table
        # We only show columns that make sense for the owner to edit
        display_cols = ['name', 'category', 'current_stock', 'selling_price', 'min_stock_level', 'id']
        
        st.info("💡 You can edit 'In Stock' and 'Selling Price' directly in the table below.")
        
        edited_df = st.data_editor(
            df[display_cols],
            column_config={
                "name": st.column_config.TextColumn("Product Name", disabled=True),
                "category": st.column_config.TextColumn("Category", disabled=True),
                "current_stock": st.column_config.NumberColumn("In Stock (Qty)"),
                "selling_price": st.column_config.NumberColumn("Price (₹)"),
                "min_stock_level": st.column_config.NumberColumn("Alert Level"),
                "id": None # Hide ID from UI
            },
            use_container_width=True,
            hide_index=True,
            key="inventory_editor"
        )

        # 3. Save Changes
        if st.button("💾 Save All Changes", type="primary"):
            with st.spinner("Updating Inventory..."):
                try:
                    for index, row in edited_df.iterrows():
                        supabase.table("products").update({
                            "current_stock": row['current_stock'],
                            "selling_price": row['selling_price'],
                            "min_stock_level": row['min_stock_level']
                        }).eq("id", row['id']).execute()
                    
                    st.success("Changes saved successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update: {e}")
    else:
        st.warning("No products found. Go to the 'Bulk Import' tab to add your first batch of items.")

# --- TAB 2: BULK IMPORT ---
with tab_import:
    st.subheader("Import Stock from CSV or Excel")
    uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx"])

    if uploaded_file is not None:
        try:
            # Handle encoding issues for CSVs
            if uploaded_file.name.endswith('.csv'):
                try:
                    df_upload = pd.read_csv(uploaded_file)
                except UnicodeDecodeError:
                    uploaded_file.seek(0)
                    df_upload = pd.read_csv(uploaded_file, encoding='latin1')
            else:
                df_upload = pd.read_excel(uploaded_file)

            # Clean and Match Columns
            df_upload.columns = df_upload.columns.str.strip().str.lower()
            
            st.write("### Preview of Upload:")
            st.dataframe(df_upload.head())
            
            required_cols = ['name', 'cost_price', 'selling_price', 'current_stock']
            missing = [col for col in required_cols if col not in df_upload.columns]
            
            if missing:
                st.error(f"Missing required columns: {', '.join(missing)}")
            else:
                if st.button("🚀 Confirm and Push to Database"):
                    with st.spinner("Uploading..."):
                        data_to_insert = df_upload.to_dict(orient='records')
                        bulk_upload_products(data_to_insert)
                        st.success(f"Successfully uploaded {len(data_to_insert)} items!")
                        st.rerun()
                        
        except Exception as e:
            st.error(f"Error reading file: {e}")