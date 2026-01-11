import streamlit as st
from src.database import fetch_shop_settings, update_shop_settings

# --- 1. PAGE CONFIG & HIDE DEFAULTS ---
st.set_page_config(page_title="Haveli Settings", layout="wide", initial_sidebar_state="collapsed")

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

    /* Target main containers but prevent styling empty spacer columns */
    div[data-testid="stVerticalBlockBorderWrapper"] > div > div > div[data-testid="stVerticalBlock"] {
        padding: 0px !important;
    }
    
    /* The single clean border for the main card */
    [data-testid="stForm"] {
        border: 1px solid #2d2d2d !important;
        border-radius: 12px;
        background-color: #161616 !important;
        padding: 30px !important;
    }

    /* Red Accent for Section Headers */
    h3 {
        color: #ff5252 !important;
        font-size: 1.3rem;
        margin-bottom: 15px !important;
        font-weight: 700;
        border-bottom: 1px solid #4a0e0e;
        padding-bottom: 8px;
    }

    /* Input Styling */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stNumberInput>div>div>input {
        background-color: #222 !important;
        color: white !important;
        border: 1px solid #333 !important;
    }

    .stAlert {
        background-color: #1a1a1a !important;
        border-left: 4px solid #b71c1c !important;
        color: #e0e0e0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN PROTECTION ---
# Check session state to ensure user is logged in
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
    if st.button("📊 Insights", use_container_width=True):
        st.switch_page("pages/insights.py")
with nav_col4:
    # Settings is active - styled with a highlight border
    st.markdown('<div style="border: 2px solid #ff5252; border-radius: 8px;">', unsafe_allow_html=True)
    st.button("⚙️ Settings", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

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

# --- 6. SETTINGS LOGIC ---
st.markdown("## ⚙️ Shop Configuration")

# Fetch data
try:
    settings = fetch_shop_settings()
    if settings is None: settings = {}
except Exception:
    settings = {"shop_name": "Haveli Electricals", "shop_address": "", "shop_contact": "", "upi_id": "", "tax_percent": 0}

# --- MAIN SETTINGS CARD ---
with st.form("shop_settings_form"):
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("### 🏢 Business Profile")
        new_name = st.text_input("Shop Name", value=settings.get('shop_name', 'Haveli Electricals'))
        new_address = st.text_area("Shop Address", value=settings.get('shop_address', ''), height=120)
        new_contact = st.text_input("Contact Number", value=settings.get('shop_contact', ''), placeholder="+91 XXXXX XXXXX")
    
    with col2:
        st.markdown("### 💳 Payments & Tax")
        new_upi = st.text_input("UPI ID", value=settings.get('upi_id', ''), placeholder="shop@upi")
        new_tax = st.number_input("Tax / GST %", value=float(settings.get('tax_percent', 0)), min_value=0.0, max_value=28.0)
        
        st.write("") # Spacer
        st.info("💡 Changes update your PDF invoices and WhatsApp receipts instantly.")

    # Centered Submit Button
    col_sub_1, col_sub_2, col_sub_3 = st.columns([1, 1, 1])
    with col_sub_2:
        if st.form_submit_button("💾 Save All Changes", use_container_width=True):
            update_data = {
                "shop_name": new_name,
                "shop_address": new_address,
                "shop_contact": new_contact,
                "upi_id": new_upi,
                "tax_percent": new_tax
            }
            try:
                update_shop_settings(update_data)
                st.success("Settings Saved!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

st.markdown("<p style='text-align: center; color: #666; font-size: 0.8rem; margin-top: 20px;'>Haveli Electricals Management System v1.2</p>", unsafe_allow_html=True)