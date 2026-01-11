import streamlit as st
import pandas as pd
from src.database import fetch_all_products, create_sale_record, void_transaction, fetch_shop_settings
from src.utils import generate_invoice_pdf, get_whatsapp_link

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Haveli Billing", layout="wide", initial_sidebar_state="collapsed")

# --- 2. GLOBAL STYLING ---
st.markdown("""
    <style>
    .main { background-color: #0f0f0f; }
    html, body, [class*="css"] { color: #e0e0e0 !important; font-family: 'Inter', sans-serif; }
    
    /* STOPS SIDEBAR FROM APPEARING AT LOGIN */
    [data-testid="stSidebarNav"] {display: none !important;}
    div[data-testid="stSidebar"] {display: none;}
    
    /* Highlight the active page button */
    .active-nav-container { border: 2px solid #ff5252; border-radius: 8px; }

    /* Red Button Theme */
    .stButton > button {
        border-radius: 6px;
        background-color: #b71c1c !important; 
        color: white !important;
        border: 1px solid #4a0e0e !important;
        font-weight: 600;
    }
    .stButton > button:hover { background-color: #d32f2f !important; }

    /* UI Containers */
    [data-testid="stForm"], div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #2d2d2d !important;
        border-radius: 12px;
        background-color: #161616 !important;
        padding: 20px !important;
    }
    .login-hero { padding: 40px; border-right: 2px solid #b71c1c; }
    h4 { color: #ff5252 !important; border-bottom: 1px solid #4a0e0e; padding-bottom: 8px; }
    
    .total-box {
        background-color: #1a1a1a; color: #ff5252 !important; padding: 18px;
        border-radius: 8px; text-align: right; font-size: 30px; font-weight: 800;
        border: 2px solid #b71c1c;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN & SECURITY LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login():
    """Centered admin login screen with hero section."""
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col_info, col_login = st.columns([1.2, 1], gap="large")
    with col_info:
        # st.markdown("<div class='login-hero'>", unsafe_allow_html=True)
        st.markdown("# 🏮 Haveli Electricals")
        st.markdown("### Professional Inventory & Billing Management")
        st.write("")
        st.markdown("✅ **Real-time Stock Tracking**")
        st.markdown("✅ **Automated WhatsApp Receipts**")
        st.markdown("✅ **GST-Ready PDF Invoices**")
        st.markdown("✅ **Daily Business Insights**")
        st.write("")
        st.info("⚠️ Restricted Access: Authorized Personnel Only")
        st.markdown("</div>", unsafe_allow_html=True)
    with col_login:
        st.write("<br>", unsafe_allow_html=True)
        with st.form("login_form"):
            st.markdown("#### 🔐 Admin Login")
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            if st.form_submit_button("Access Terminal", use_container_width=True):
                if user == st.secrets["ADMIN_USER"] and pwd == st.secrets["ADMIN_PASSWORD"]:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid Credentials")

if not st.session_state.logged_in:
    login()
    st.stop()

st.markdown("""<style>div[data-testid="stSidebar"] {display: block !important;}</style>""", unsafe_allow_html=True)

# TOP NAVIGATION BAR
nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
with nav_col1:
    st.markdown('<div class="active-nav-container">', unsafe_allow_html=True)
    st.button("⚡ Billing Hub", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
with nav_col2:
    if st.button("📦 Inventory", use_container_width=True):
        st.switch_page("pages/inventory.py") 
with nav_col3:
    if st.button("📊 Insights", use_container_width=True):
        st.switch_page("pages/insights.py")
with nav_col4:
    if st.button("⚙️ Settings", use_container_width=True):
        st.switch_page("pages/settings.py")

st.divider()

with st.sidebar:
    st.markdown("### 🏮 Admin Panel")
    st.write(f"User: **{st.secrets['ADMIN_USER']}**")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
    st.divider()
    st.info("Haveli Electricals v1.2")

# --- 5. BILLING HUB LOGIC WITH STOCK GUARDRAILS ---
if 'cart' not in st.session_state: st.session_state.cart = []
if 'last_sale' not in st.session_state: st.session_state.last_sale = None

def reset_bill():
    st.session_state.cart = []
    st.session_state.last_sale = None
    st.rerun()

try:
    shop_info = fetch_shop_settings()
    shop_name = shop_info.get('shop_name', 'Haveli Electricals')
except:
    shop_name = "Haveli Electricals"

header_col, action_col = st.columns([5, 1])
with header_col:
    st.markdown(f"# ⚡ Billing Terminal")
with action_col:
    if st.button("🆕 New Bill", use_container_width=True):
        reset_bill()

col_left, col_right = st.columns([1, 1.2], gap="large")

with col_left:
    with st.container(border=True):
        st.markdown("#### 👤 Customer & Payment")
        cust_phone = st.text_input("WhatsApp Number", placeholder="e.g. 9825XXXXXX")
        payment_mode = st.selectbox("Mode of Payment", ["Cash", "UPI", "Card"])

with col_right:
    with st.container(border=True):
        st.markdown("#### 📦 Add Products")
        all_products = fetch_all_products()
        
        # GUARDRAIL 1: Filter out products with 0 or negative stock
        available_products = [p for p in all_products if p['current_stock'] > 0]
        product_names = [f"{p['name']} (Stock: {p['current_stock']})" for p in available_products]
        
        selected_display_name = st.selectbox("Search Product", [""] + product_names, label_visibility="collapsed")
        
        q_col, a_col = st.columns([1, 2], gap="medium")
        qty = q_col.number_input("Qty", min_value=1, value=1)
        
        if st.session_state.last_sale is None:
            if selected_display_name:
                # Extract real product name from display string
                real_name = selected_display_name.split(" (Stock:")[0]
                prod_details = next(p for p in available_products if p['name'] == real_name)
                
                # LOW STOCK ALERT: Notify if down to last 3 units
                if 0 < prod_details['current_stock'] <= 3:
                    st.warning(f"⚠️ Low Stock Alert: Only {prod_details['current_stock']} left!")

                # GUARDRAIL 2: Check if requested qty is more than available
                if qty > prod_details['current_stock']:
                    a_col.error(f"Only {prod_details['current_stock']} left!")
                elif a_col.button("➕ Add to Cart", use_container_width=True):
                    existing_item = next((item for item in st.session_state.cart if item['id'] == prod_details['id']), None)
                    if existing_item:
                        if (existing_item['quantity'] + qty) > prod_details['current_stock']:
                            st.error(f"Cannot add more! Total exceeds stock.")
                        else:
                            existing_item['quantity'] += qty
                            st.rerun()
                    else:
                        st.session_state.cart.append({
                            "id": prod_details['id'], "name": prod_details['name'],
                            "quantity": qty, "price": float(prod_details['selling_price']),
                            "cost_price": float(prod_details['cost_price'])
                        })
                        st.rerun()
        else:
            a_col.info("Bill Finalized")

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
                use_container_width=True, num_rows="dynamic", hide_index=True, key="bill_editor"
            )
            total_bill = (edited_cart['quantity'] * edited_cart['price']).sum()
        st.markdown(f"""<div class="total-box">Grand Total: Rs. {total_bill:,.2f}</div>""", unsafe_allow_html=True)

    if st.session_state.last_sale is None:
        if st.button("🚀 FINALIZE TRANSACTION & PRINT", type="primary"):
            db_sale_items, pdf_sale_items = [], []
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
    
    # --- UPDATED CHECKOUT LOGIC WITH DYNAMIC WHATSAPP ---
    if st.session_state.last_sale:
        ls = st.session_state.last_sale
        st.success(f"Sale Recorded Successfully. ID: {ls['id'][:8]}")
        
        pdf_buffer = generate_invoice_pdf(ls['id'], ls['items'], ls['total'], ls['phone'], payment_mode)
        
        c1, c2, c3 = st.columns(3)
        with c1: 
            st.download_button("📥 Download PDF", data=pdf_buffer, file_name=f"Haveli_{ls['id'][:8]}.pdf", use_container_width=True)
        
        with c2: 
            # Allow phone number entry if it was missing or needs changing
            share_phone = st.text_input("WhatsApp No.", value=ls['phone'], placeholder="Enter for WhatsApp", label_visibility="collapsed")
            
            if share_phone:
                st.link_button("💬 WhatsApp Receipt", get_whatsapp_link(share_phone, ls['total']), use_container_width=True)
            else:
                st.button("💬 WhatsApp (Enter No. ⬆️)", disabled=True, use_container_width=True)
                
        with c3:
            with st.popover("⚠️ Cancel Sale", use_container_width=True):
                if st.button("Confirm Void", type="primary", use_container_width=True):
                    void_transaction(ls['id'])
                    reset_bill()
else:
    st.info("No items in cart.")