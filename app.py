import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- SETUP & AUTHENTICATION ---
st.set_page_config(page_title="Retail POS & Inventory", layout="wide")

@st.cache_resource
def init_connection():
    # Load credentials from Streamlit Secrets
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
    st.header("Add New Item to Inventory")
    
    with st.form("add_item_form"):
        col1, col2 = st.columns(2)
        item_name = col1.text_input("Item Name")
        qty = col1.number_input("Quantity", min_value=1, step=1)
        buy_price = col2.number_input("Purchased Price", min_value=0.0, step=1.0)
        sell_price = col2.number_input("Sell Price", min_value=0.0, step=1.0)
        
        submitted = st.form_submit_button("Add to Inventory")
        
        if submitted:
            if item_name:
                df_inv = get_data(inv_ws)
                new_s_no = int(df_inv['S No.'].max() + 1) if not df_inv.empty else 1
                remarks = "Available" if qty > 0 else "Out of Stock"
                
                inv_ws.append_row([new_s_no, item_name, buy_price, sell_price, qty, remarks])
                st.success(f"Added '{item_name}' to inventory successfully!")
                clear_cache()
            else:
                st.error("Please enter an Item Name.")

# ==========================================
# TAB 2: SELL ITEM (POS)
# ==========================================
with tab2:
    st.header("Point of Sale")
    df_inv = get_data(inv_ws)
    
    if df_inv.empty:
        st.warning("Inventory is empty. Add items first.")
    else:
        # Filter only available items
        available_items = df_inv[df_inv['Quantity'] > 0]['Item Name'].tolist()
        
        with st.form("sell_item_form"):
            selected_item = st.selectbox("Search & Select Item", available_items)
            qty_sold = st.number_input("Quantity Sold", min_value=1, step=1)
            
            sell_submitted = st.form_submit_button("Complete Sale")
            
            if sell_submitted and selected_item:
                item_data = df_inv[df_inv['Item Name'] == selected_item].iloc[0]
                current_qty = int(item_data['Quantity'])
                
                if qty_sold > current_qty:
                    st.error(f"Not enough stock! Only {current_qty} left.")
                else:
                    # Calculations
                    buy_price = float(item_data['Purchased price'])
                    sell_price = float(item_data['Sell price'])
                    profit = (sell_price - buy_price) * qty_sold
                    new_qty = current_qty - qty_sold
                    remarks = "Out of Stock" if new_qty == 0 else "Available"
                    
                    # Update Inventory Sheet
                    # gspread is 1-indexed, and row 1 is headers. So +2 to get correct row
                    row_index = int(item_data.name) + 2 
                    
                    # Update Quantity (Col E) and Remarks (Col F)
                    inv_ws.update(f"E{row_index}:F{row_index}", [[new_qty, remarks]])
                    
                    # Log Sale
                    df_sales = get_data(sales_ws)
                    new_sales_no = int(df_sales['S No.'].max() + 1) if not df_sales.empty else 1
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    
                    sales_ws.append_row([
                        new_sales_no, date_str, selected_item, buy_price, sell_price, qty_sold, profit
                    ])
                    
                    st.success(f"Sale successful! Sold {qty_sold}x {selected_item}. Profit: ${profit:.2f}")
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
            
            # Check if item exists
            if not df_req.empty and req_item.lower() in df_req['Item Name'].str.lower().tolist():
                # Find row index to update count
                idx = df_req.index[df_req['Item Name'].str.lower() == req_item.lower()].tolist()[0]
                current_count = int(df_req.iloc[idx]['Demand Count'])
                
                row_index = idx + 2
                req_ws.update_acell(f"C{row_index}", current_count + 1)
                req_ws.update_acell(f"A{row_index}", date_str) # Update to latest date
                st.success(f"Updated demand count for '{req_item}'.")
            else:
                # Add new row
                req_ws.append_row([date_str, req_item, 1])
                st.success(f"Logged new demand for '{req_item}'.")
            clear_cache()

# ==========================================
# TAB 4: DASHBOARD
# ==========================================
with tab4:
    st.header("Dashboard & Analytics")
    
    # Fetch latest data
    df_sales = get_data(sales_ws)
    df_inv = get_data(inv_ws)
    df_req = get_data(req_ws)
    
    # 1. Today's Metrics
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    today_sales = 0
    today_profit = 0
    if not df_sales.empty:
        df_today = df_sales[df_sales['Date'] == today_str]
        today_sales = (df_today['Sell price'] * df_today['Quantity Sold']).sum()
        today_profit = df_today['Total Profit'].sum()
    
    col1, col2 = st.columns(2)
    col1.metric("Today's Total Sales", f"${today_sales:.2f}")
    col2.metric("Today's Total Profit", f"${today_profit:.2f}")
    
    st.divider()
    
    # 2. To-Buy / Restock List
    st.subheader("🔴 To-Buy / Restock List")
    if not df_inv.empty:
        out_of_stock = df_inv[df_inv['Remarks'] == "Out of Stock"]
        if not out_of_stock.empty:
            st.dataframe(out_of_stock[['Item Name', 'Purchased price', 'Sell price']], use_container_width=True, hide_index=True)
        else:
            st.success("All items are currently in stock!")
    else:
        st.write("No inventory data.")

    st.divider()
    
    # 3. Most Demanded New Items
    st.subheader("🔥 Most Demanded New Items")
    if not df_req.empty:
        top_demands = df_req.sort_values(by="Demand Count", ascending=False)
        st.dataframe(top_demands, use_container_width=True, hide_index=True)
    else:
        st.write("No customer demands logged yet.")
