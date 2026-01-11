import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(url, key)

# --- Inventory Functions ---

def fetch_all_products():
    """Returns all products for the inventory list."""
    response = supabase.table("products").select("*").order("name").execute()
    return response.data

def bulk_upload_products(data_list):
    """Expects a list of dictionaries to insert into Supabase."""
    return supabase.table("products").insert(data_list).execute()

# --- Billing Functions ---

def update_stock_level(product_id, quantity_sold):
    """Reduces the stock count when a sale is made."""
    # First, get current stock
    product = supabase.table("products").select("current_stock").eq("id", product_id).single().execute()
    new_stock = product.data['current_stock'] - quantity_sold
    
    # Update it
    supabase.table("products").update({"current_stock": new_stock}).eq("id", product_id).execute()

def create_sale_record(customer_phone, total_amount, payment_mode, items):
    """
    1. Creates a record in the 'sales' table.
    2. Uses the resulting Sale ID to create records in 'sale_items'.
    """
    sale_data = {
        "customer_phone": customer_phone,
        "total_amount": total_amount,
        "payment_mode": payment_mode
    }
    # Insert sale and get the ID
    sale_response = supabase.table("sales").insert(sale_data).execute()
    sale_id = sale_response.data[0]['id']
    
    # Insert items into sale_items
    for item in items:
        item['sale_id'] = sale_id
        supabase.table("sale_items").insert(item).execute()
        # Update inventory too
        update_stock_level(item['product_id'], item['quantity'])
    
    return sale_id

def fetch_analytics_data():
    """Fetches a joined view of sales and items to calculate profit."""
    # We join sale_items with products to get the cost_price
    query = """
    SELECT 
        s.created_at,
        si.quantity,
        si.price_at_sale,
        p.cost_price,
        p.name as product_name
    FROM sale_items si
    JOIN sales s ON si.sale_id = s.id
    JOIN products p ON si.product_id = p.id
    """
    response = supabase.rpc('get_analytics').execute() # Or a standard select if no RPC
    # For simplicity, let's fetch the raw sale_items and handle joins in Pandas
    sales = supabase.table("sales").select("*").execute()
    items = supabase.table("sale_items").select("*, products(name, cost_price)").execute()
    return sales.data, items.data

def void_transaction(sale_id):
    """Reverses a sale: Restores stock and deletes the sale record."""
    # 1. Get the items from the sale to know what to put back
    items_res = supabase.table("sale_items").select("product_id, quantity").eq("sale_id", sale_id).execute()
    
    for item in items_res.data:
        # Get current stock
        prod = supabase.table("products").select("current_stock").eq("id", item['product_id']).single().execute()
        new_stock = prod.data['current_stock'] + item['quantity']
        
        # Restore stock
        supabase.table("products").update({"current_stock": new_stock}).eq("id", item['product_id']).execute()
    
    # 2. Delete the sale (Cascade will delete sale_items automatically)
    supabase.table("sales").delete().eq("id", sale_id).execute()

def fetch_shop_settings():
    """Fetches the single row of shop configuration."""
    res = supabase.table("shop_settings").select("*").eq("id", 1).single().execute()
    return res.data

def update_shop_settings(data):
    """Updates the shop profile details."""
    return supabase.table("shop_settings").update(data).eq("id", 1).execute()