import streamlit as st
import pandas as pd
from src.database import fetch_all_products, create_sale_record, void_transaction, fetch_shop_settings
from src.utils import generate_invoice_pdf, get_whatsapp_link

# Must be the first command
st.set_page_config(page_title="Haveli Billing", layout="wide")

# Sophisticated "Haveli Red" UI CSS
st.markdown("""
    <style>
    /* Main Background */
    .main { 
        background-color: #0f0f0f; 
    }
    
    /* Text Readability */
    html, body, [class*="css"] {
        color: #e0e0e0 !important;
        font-family: 'Inter', sans-serif;
    }

    /* Target ONLY the main container for the border, NOT empty columns */
    div[data-testid="stVerticalBlockBorderWrapper"] > div > div > div[data-testid="stVerticalBlock"] {
        padding: 0px !important;
    }

    /* Clean Card Style - Single Border Logic */
    [data-testid="stForm"], div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #2d2d2d !important;
        border-radius: 12px;
        background-color: #161616 !important;
        padding: 20px !important;
    }

    /* Red Accent for Section Headers */
    h4 {
        color: #ff5252 !important;
        margin-bottom: 15px !important;
        border-bottom: 1px solid #4a0e0e;
        padding-bottom: 8px;
    }

    /* Primary Button - Deep Red */
    .stButton>button {
        border-radius: 6px;
        background-color: #b71c1c !important;
        color: white !important;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #d32f2f !important;
        box-shadow: 0 4px 12px rgba(183, 28, 28, 0.3);
    }

    /* --- FLEXBOX CENTERING FOR MAIN ACTIONS --- */
    /* This centers buttons within their specific containers */
    div.stButton {
        display: flex;
        justify-content: center;
    }

    /* New Bill Button Overwrite */
    [data-testid="column"] .stButton>button:contains("New Bill") {
        background-color: #333 !important;
        border: 1px solid #444 !important;
    }

    /* Total Bill Box - Sleek and integrated */
    .total-box {
        background-color: #1a1a1a;
        color: #ff5252 !important;
        padding: 18px;
        border-radius: 8px;
        text-align: right;
        font-size: 30px;
        font-weight: 800;
        margin-top: 15px;
        border: 2px solid #b71c1c;
    }

    /* Input Styling */
    .stTextInput>div>div>input, .stSelectbox>div>div>select, .stNumberInput>div>div>input {
        background-color: #222 !important;
        color: white !important;
        border: 1px solid #333 !important;
    }
    
    /* Info Box Styling */
    .stAlert {
        background-color: #1a1a1a !important;
        border-left: 4px solid #b71c1c !important;
        color: #e0e0e0 !important;
    }

    /* Divider Color */
    hr {
        border-color: #333 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize Session State
if 'cart' not in st.session_state: st.session_state.cart = []
if 'last_sale' not in st.session_state: st.session_state.last_sale = None

def reset_bill():
    st.session_state.cart = []
    st.session_state.last_sale = None
    st.rerun()

# --- DYNAMIC HEADER ---
try:
    shop_info = fetch_shop_settings()
    shop_name = shop_info.get('shop_name', 'Haveli Electricals')
except:
    shop_name = "Haveli Electricals"

# Clean Header Row
header_col, action_col = st.columns([5, 1])
with header_col:
    st.markdown(f"# 🏮 {shop_name}")
with action_col:
    st.write("") 
    if st.button("🆕 New Bill", use_container_width=True):
        reset_bill()

st.divider()

# --- SECTION 1: DATA ENTRY ---
col_left, col_right = st.columns([1, 1.2], gap="large")

with col_left:
    with st.container(border=True):
        st.markdown("#### 👤 Customer & Payment")
        cust_phone = st.text_input("WhatsApp Number", placeholder="e.g. 9825XXXXXX")
        payment_mode = st.selectbox("Mode of Payment", ["Cash", "UPI", "Card"])

with col_right:
    with st.container(border=True):
        st.markdown("#### 📦 Add Products")
        products = fetch_all_products()
        product_names = [p['name'] for p in products]
        
        selected_item_name = st.selectbox("Search Product", [""] + product_names, label_visibility="collapsed")
        
        q_col, a_col = st.columns([1, 2], gap="medium")
        qty = q_col.number_input("Qty", min_value=1, value=1)
        
        if st.session_state.last_sale is None:
            if a_col.button("➕ Add to Cart", use_container_width=True):
                if selected_item_name:
                    prod_details = next(p for p in products if p['name'] == selected_item_name)
                    existing_item = next((item for item in st.session_state.cart if item['id'] == prod_details['id']), None)
                    if existing_item:
                        existing_item['quantity'] += qty
                    else:
                        st.session_state.cart.append({
                            "id": prod_details['id'], "name": prod_details['name'],
                            "quantity": qty, "price": float(prod_details['selling_price']),
                            "cost_price": float(prod_details['cost_price'])
                        })
                    st.rerun()
        else:
            a_col.info("Bill Finalized")

# --- SECTION 2: THE BILL VIEW ---
if st.session_state.cart:
    st.write("") 
    st.markdown("#### 📋 Current Bill Details")
    
    with st.container(border=True):
        cart_df = pd.DataFrame(st.session_state.cart)
        
        if st.session_state.last_sale:
            st.dataframe(cart_df[['name', 'quantity', 'price']], use_container_width=True, hide_index=True)
            total_bill = st.session_state.last_sale['total']
        else:
            edited_cart = st.data_editor(
                cart_df[['name', 'quantity', 'price']],
                column_config={
                    "name": st.column_config.TextColumn("Product Name", disabled=True),
                    "price": st.column_config.NumberColumn("Rate (Rs.)", format="%.2f"),
                    "quantity": st.column_config.NumberColumn("Qty")
                },
                use_container_width=True,
                num_rows="dynamic",
                hide_index=True,
                key="bill_editor"
            )
            total_bill = (edited_cart['quantity'] * edited_cart['price']).sum()

        st.markdown(f"""<div class="total-box">Grand Total: Rs. {total_bill:,.2f}</div>""", unsafe_allow_html=True)

    # --- SECTION 3: CHECKOUT & ACTIONS ---
    if st.session_state.last_sale is None:
        st.write("") 
        # The CSS rule div.stButton centers this button automatically
        if st.button("🚀 FINALIZE TRANSACTION & PRINT", type="primary", use_container_width=False):
            db_sale_items = []
            pdf_sale_items = []
            for _, row in edited_cart.iterrows():
                original_item = next(item for item in st.session_state.cart if item['name'] == row['name'])
                db_sale_items.append({"product_id": original_item['id'], "quantity": int(row['quantity']), "price_at_sale": float(row['price'])})
                pdf_sale_items.append({"name": row['name'], "quantity": int(row['quantity']), "price": float(row['price'])})
            
            try:
                sale_id = create_sale_record(cust_phone, total_bill, payment_mode, db_sale_items)
                st.session_state.last_sale = {"id": sale_id, "total": total_bill, "phone": cust_phone, "items": pdf_sale_items}
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Transaction failed: {e}")
    
    if st.session_state.last_sale:
        ls = st.session_state.last_sale
        st.success(f"Sale Recorded Successfully. Invoice ID: {ls['id'][:8]}")
        
        pdf_buffer = generate_invoice_pdf(ls['id'], ls['items'], ls['total'], ls['phone'], payment_mode)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button("📥 Download PDF Receipt", data=pdf_buffer, file_name=f"Haveli_{ls['id'][:8]}.pdf", use_container_width=True)
        with c2:
            if ls['phone']:
                st.link_button("💬 Send WhatsApp Receipt", get_whatsapp_link(ls['phone'], ls['total']), use_container_width=True)
        with c3:
            with st.popover("⚠️ Cancel/Void Sale", use_container_width=True):
                st.write("Confirming will delete this sale and restore stock.")
                if st.button("Confirm Void", type="primary", use_container_width=True):
                    void_transaction(ls['id'])
                    reset_bill()
else:
    st.write("")
    st.info("No items in cart. Start by searching for a product above.")