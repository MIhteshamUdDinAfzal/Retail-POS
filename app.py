import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- SETUP & AUTHENTICATION ---
st.set_page_config(page_title="Retail POS & Inventory", layout="wide")

@st.cache_resource
def init_connection():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(st.secrets["gsheets"]["spreadsheet_url"])
    return sheet

sheet = init_connection()

# Worksheets
inv_ws = sheet.worksheet("Inventory")
sales_ws = sheet.worksheet("Sales")
req_ws = sheet.worksheet("Requested Items")

# Helper Functions
def get_data(worksheet):
    records = worksheet.get_all_records()
    return pd.DataFrame(records)

def clear_cache():
    st.cache_data.clear()

# --- UI LAYOUT ---
st.title("🏪 Retail Shop POS & Inventory")

tab1, tab2, tab3, tab4 = st.tabs([
    "📦 Add Item", 
    "🛒 Sell Item", 
    "📝 Customer Demands", 
    "📊 Dashboard"
])

# ==========================================
# TAB 1: ADD ITEM (INVENTORY)
# ==========================================
with tab1:
    st.header("Add or Restock Item in Inventory")
    df_inv = get_data(inv_ws)
    
    # Get existing items for the dropdown
    existing_items = df_inv['Item Name'].tolist() if not df_inv.empty else []
    options = ["➕ Create New Item"] + existing_items
    
    with st.form("add_item_form"):
        # Select existing item or choose to create a new one
        selected_option = st.selectbox("Select Existing Item or Add New", options)
        new_item_name = st.text_input("New Item Name (Only if creating new)")
        
        col1, col2 = st.columns(2)
        qty = col1.number_input("Quantity to Add", min_value=1, step=1)
        buy_price = col2.number_input("Purchased Price", min_value=0.0, step=1.0)
        
        submitted = st.form_submit_button("Update Inventory")
        
        if submitted:
            # Determine the final item name based on user selection
            final_item_name = new_item_name if selected_option == "➕ Create New Item" else selected_option
            
            if final_item_name:
                # Check if item already exists in inventory (case-insensitive)
                if not df_inv.empty and final_item_name.lower() in df_inv['Item Name'].str.lower().tolist():
                    # --- UPDATE EXISTING ITEM (RESTOCK) ---
                    idx = df_inv.index[df_inv['Item Name'].str.lower() == final_item_name.lower()].tolist()[0]
                    current_qty = int(df_inv.iloc[idx]['Quantity'])
                    new_qty = current_qty + qty
                    
                    # +2 because DataFrame index starts at 0, and Sheet row 1 is header
                    row_index = idx + 2 
                    
                    # Update Price (Col C), Quantity (Col D), and Remarks (Col E)
                    inv_ws.update(range_name=f"C{row_index}:E{row_index}", values=[[buy_price, new_qty, "Available"]])
                    st.success(f"Restocked '{final_item_name}'! New Total Quantity: {new_qty}")
                else:
                    # --- ADD COMPLETELY NEW ITEM ---
                    new_s_no = int(df_inv['S No.'].max() + 1) if not df_inv.empty else 1
                    inv_ws.append_row([new_s_no, final_item_name, buy_price, qty, "Available"])
                    st.success(f"Added new item '{final_item_name}' to inventory!")
                
                clear_cache()
            else:
                st.error("Please provide an Item Name.")

# ==========================================
# TAB 2: SELL ITEM (POS)
# ==========================================
with tab2:
    st.header("Point of Sale")
    df_inv = get_data(inv_ws)
    
    if df_inv.empty:
        st.warning("Inventory is empty. Add items first.")
    else:
        available_items = df_inv[df_inv['Quantity'] > 0]['Item Name'].tolist()
        
        with st.form("sell_item_form"):
            selected_item = st.selectbox("Search & Select Item", available_items)
            
            col1, col2 = st.columns(2)
            qty_sold = col1.number_input("Quantity Sold", min_value=1, step=1)
            sell_price = col2.number_input("Selling Price (Per Unit)", min_value=0.0, step=1.0)
            
            sell_submitted = st.form_submit_button("Complete Sale")
            
            if sell_submitted and selected_item:
                item_data = df_inv[df_inv['Item Name'] == selected_item].iloc[0]
                current_qty = int(item_data['Quantity'])
                
                if qty_sold > current_qty:
                    st.error(f"Not enough stock! Only {current_qty} left.")
                else:
                    buy_price = float(item_data['Purchased price'])
                    profit = (sell_price - buy_price) * qty_sold
                    new_qty = current_qty - qty_sold
                    remarks = "Out of Stock" if new_qty == 0 else "Available"
                    
                    row_index = int(item_data.name) + 2 
                    inv_ws.update(range_name=f"D{row_index}:E{row_index}", values=[[new_qty, remarks]])
                    
                    df_sales = get_data(sales_ws)
                    new_sales_no = int(df_sales['S No.'].max() + 1) if not df_sales.empty else 1
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    
                    sales_ws.append_row([
                        new_sales_no, date_str, selected_item, buy_price, sell_price, qty_sold, profit
                    ])
                    
                    st.success(f"Sale successful! Sold {qty_sold}x {selected_item} for ${sell_price} each. Total Profit: ${profit:.2f}")
                    clear_cache()

# ==========================================
# TAB 3: CUSTOMER DEMANDS
# ==========================================
with tab3:
    st.header("Track New Item Demands")
    st.info("Log items requested by customers that you don't currently stock.")
    
    with st.form("demand_form"):
        req_item = st.text_input("Requested Item Name")
        req_submit = st.form_submit_button("Log Demand")
        
        if req_submit and req_item:
            df_req = get_data(req_ws)
            date_str = datetime.now().strftime("%Y-%m-%d")
            
            if not df_req.empty and req_item.lower() in df_req['Item Name'].str.lower().tolist():
                idx = df_req.index[df_req['Item Name'].str.lower() == req_item.lower()].tolist()[0]
                current_count = int(df_req.iloc[idx]['Demand Count'])
                
                row_index = idx + 2
                req_ws.update_acell(f"C{row_index}", current_count + 1)
                req_ws.update_acell(f"A{row_index}", date_str) 
                st.success(f"Updated demand count for '{req_item}'.")
            else:
                req_ws.append_row([date_str, req_item, 1])
                st.success(f"Logged new demand for '{req_item}'.")
            clear_cache()

# ==========================================
# TAB 4: DASHBOARD
# ==========================================
with tab4:
    st.header("Dashboard & Analytics")
    
    df_sales = get_data(sales_ws)
    df_inv = get_data(inv_ws)
    df_req = get_data(req_ws)
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    today_sales = 0
    today_profit = 0
    
    # Error Handling: Check if data exists and columns are correct
    if not df_sales.empty and 'Date' in df_sales.columns:
        df_today = df_sales[df_sales['Date'] == today_str].copy()
        
        # Check if 'Sell price' and 'Quantity Sold' columns actually exist before calculating
        if 'Sell price' in df_today.columns and 'Quantity Sold' in df_today.columns:
            # Convert to numeric just in case there is text
            df_today['Sell price'] = pd.to_numeric(df_today['Sell price'], errors='coerce').fillna(0)
            df_today['Quantity Sold'] = pd.to_numeric(df_today['Quantity Sold'], errors='coerce').fillna(0)
            today_sales = (df_today['Sell price'] * df_today['Quantity Sold']).sum()
            
        if 'Total Profit' in df_today.columns:
            df_today['Total Profit'] = pd.to_numeric(df_today['Total Profit'], errors='coerce').fillna(0)
            today_profit = df_today['Total Profit'].sum()
    
    col1, col2 = st.columns(2)
    col1.metric("Today's Total Revenue", f"${today_sales:.2f}")
    col2.metric("Today's Total Profit", f"${today_profit:.2f}")
    
    st.divider()
    
    st.subheader("🔴 To-Buy / Restock List")
    if not df_inv.empty and 'Remarks' in df_inv.columns:
        out_of_stock = df_inv[df_inv['Remarks'] == "Out of Stock"]
        if not out_of_stock.empty:
            # Safe display of columns
            cols_to_show = [col for col in ['Item Name', 'Purchased price', 'Quantity'] if col in out_of_stock.columns]
            st.dataframe(out_of_stock[cols_to_show], use_container_width=True, hide_index=True)
        else:
            st.success("All items are currently in stock!")
    else:
        st.write("No inventory data.")

    st.divider()
    
    st.subheader("🔥 Most Demanded New Items")
    if not df_req.empty and 'Demand Count' in df_req.columns:
        top_demands = df_req.sort_values(by="Demand Count", ascending=False)
        st.dataframe(top_demands, use_container_width=True, hide_index=True)
    else:
        st.write("No customer demands logged yet.")    
    st.divider()
    
    st.subheader("🔴 To-Buy / Restock List")
    if not df_inv.empty:
        out_of_stock = df_inv[df_inv['Remarks'] == "Out of Stock"]
        if not out_of_stock.empty:
            st.dataframe(out_of_stock[['Item Name', 'Purchased price', 'Quantity']], use_container_width=True, hide_index=True)
        else:
            st.success("All items are currently in stock!")
    else:
        st.write("No inventory data.")

    st.divider()
    
    st.subheader("🔥 Most Demanded New Items")
    if not df_req.empty:
        top_demands = df_req.sort_values(by="Demand Count", ascending=False)
        st.dataframe(top_demands, use_container_width=True, hide_index=True)
    else:
        st.write("No customer demands logged yet.")
