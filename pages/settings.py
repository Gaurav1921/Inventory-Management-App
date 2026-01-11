import streamlit as st
from src.database import fetch_shop_settings, update_shop_settings

# 1. Page Config
st.set_page_config(page_title="Haveli Settings", layout="wide")

# 2. Sophisticated "Haveli Red" UI CSS
st.markdown("""
    <style>
    /* Main Background */
    .main { 
        background-color: #0f0f0f; 
    }
    
    /* Text Visibility */
    html, body, [class*="css"] {
        color: #e0e0e0 !important;
        font-family: 'Inter', sans-serif;
    }

    /* Target ONLY the main container for the border, NOT empty columns */
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

    /* Primary Button - Deep Red */
    .stButton > button {
        border-radius: 6px;
        background-color: #b71c1c !important;
        color: white !important;
        border: none;
        padding: 0.6rem 2.5rem;
        font-weight: 600;
        width: 100% !important;
    }
    
    .stButton > button:hover {
        background-color: #d32f2f !important;
    }

    /* --- FLEXBOX CENTERING --- */
    /* This centers the specific "Save" button row without using columns */
    div.stFormSubmitButton {
        display: flex;
        justify-content: center;
        margin-top: 20px;
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

# --- HEADER ---
st.markdown("## ⚙️ Shop Configuration")

# Fetch data
try:
    settings = fetch_shop_settings()
    if settings is None: settings = {}
except Exception:
    settings = {"shop_name": "Haveli Electricals", "shop_address": "", "shop_contact": "", "upi_id": "", "tax_percent": 0}

# --- MAIN SETTINGS CARD ---
# We use st.form directly to avoid the "box-in-a-box" issue
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
    # Note: Removed columns here. The CSS class .stFormSubmitButton handles centering.
    if st.form_submit_button("💾 Save All Changes"):
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

st.markdown("<p style='text-align: center; color: #666; font-size: 0.8rem; margin-top: 20px;'>Haveli Electricals Management System v1.0</p>", unsafe_allow_html=True)