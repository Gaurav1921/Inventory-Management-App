from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas
import io
import urllib.parse
from src.database import fetch_shop_settings
from datetime import datetime

def generate_invoice_pdf(sale_id, items, total_amount, customer_phone="", payment_mode="Cash"):
    """Generates a detailed PDF invoice with fixed line alignment."""
    try:
        shop = fetch_shop_settings()
        if shop is None: shop = {}
    except Exception:
        shop = {}

    shop_name = shop.get('shop_name') or "HAVELI ELECTRICALS"
    shop_address = shop.get('shop_address') or ""
    shop_contact = shop.get('shop_contact') or ""

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A5)
    width, height = A5

    # --- Header Section ---
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width/2, height - 40, str(shop_name).upper())
    
    p.setFont("Helvetica", 8)
    p.drawCentredString(width/2, height - 55, str(shop_address)[:65])
    p.drawCentredString(width/2, height - 65, f"Contact: {shop_contact}")
    
    p.line(30, height - 75, width - 30, height - 75)

    # --- Invoice Info ---
    p.setFont("Helvetica", 10)
    p.drawString(30, height - 95, f"Invoice ID: {sale_id[:8]}")
    p.drawString(30, height - 110, f"Customer: {customer_phone if customer_phone else 'Walk-in'}")
    p.drawRightString(width - 30, height - 95, f"Payment: {payment_mode}")
    p.drawRightString(width - 30, height - 110, f"Date: {datetime.now().strftime('%d-%m-%Y')}")

    # --- Table Header ---
    p.setFont("Helvetica-Bold", 10)
    p.drawString(30, height - 140, "Item Description")
    p.drawRightString(width - 100, height - 140, "Qty")
    p.drawRightString(width - 30, height - 140, "Price (Rs.)")
    p.line(30, height - 145, width - 30, height - 145)

    # --- Items List ---
    y = height - 165
    p.setFont("Helvetica", 10)
    for item in items:
        # Draw the text
        p.drawString(30, y, item['name'][:35])
        p.drawRightString(width - 100, y, str(item['quantity']))
        p.drawRightString(width - 30, y, f"{float(item['price']):,.2f}")
        
        # Move down for the dotted line
        y -= 6 
        p.setDash(1, 2)
        p.setStrokeColorRGB(0.7, 0.7, 0.7) # Light gray for subtle look
        p.line(30, y, width - 30, y)
        p.setDash() 
        p.setStrokeColorRGB(0, 0, 0) # Reset to black
        
        # Move down for the next item
        y -= 14 

        if y < 80:
            p.showPage()
            y = height - 50

    # --- Footer ---
    y -= 10
    p.line(30, y, width - 30, y)
    p.setFont("Helvetica-Bold", 12)
    p.drawRightString(width - 30, y - 25, f"TOTAL AMOUNT: Rs. {total_amount:,.2f}")
    
    p.setFont("Helvetica-Oblique", 8)
    p.drawCentredString(width/2, 30, "This is a computer-generated invoice. Thank you for your business!")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

def get_whatsapp_link(phone, amount):
    """Generates a WhatsApp magic link with dynamic shop name."""
    try:
        shop = fetch_shop_settings()
        shop_name = (shop.get('shop_name') if shop else "Haveli Electricals") or "Haveli Electricals"
    except Exception:
        shop_name = "Haveli Electricals"

    message = f"Hello! Your invoice from {shop_name} for Rs. {amount:,.2f} has been generated. Thank you!"
    encoded_msg = urllib.parse.quote(message)
    
    phone = str(phone).strip()
    if not phone.startswith('91') and len(phone) == 10:
        phone = '91' + phone
        
    return f"https://wa.me/{phone}?text={encoded_msg}"