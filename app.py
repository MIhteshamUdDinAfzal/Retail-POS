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
    st.header("Inventory Management")
    df_inv = get_data(inv_ws)
    
    # 1. Radio Buttons to separate Logic
    action_type = st.radio("What do you want to do?", ["🔄 Restock Existing Item", "📦 Add Completely New Item"], horizontal=True)
    st.divider()
    
    if action_type == "🔄 Restock Existing Item":
        st.subheader("Restock Existing Item")
        existing_items = df_inv['Item Name'].tolist() if not df_inv.empty else []
        
        if not existing_items:
            st.warning("No items in inventory yet. Please add a new item first.")
        else:
            selected_option = st.selectbox("🔍 Search & Select Item", existing_items)
            
            # Auto-fetch existing price
            default_price = 0.0
            if not df_inv.empty:
                idx = df_inv.index[df_inv['Item Name'] == selected_option].tolist()[0]
                default_price = float(df_inv.iloc[idx]['Purchased price'])
                st.info(f"✔️ Selected: **{selected_option}** (Current Purchase Price: RS {default_price})")
            
            col1, col2 = st.columns(2)
            qty = col1.number_input("Quantity to Add", min_value=1, step=1, key="exist_qty")
            buy_price = col2.number_input("Update Purchased Price (RS)", min_value=0.0, value=float(default_price), step=1.0, key="exist_price")
            
            submitted = st.button("Update Inventory", use_container_width=True, key="btn_exist")
            
            if submitted:
                idx = df_inv.index[df_inv['Item Name'] == selected_option].tolist()[0]
                current_qty = int(df_inv.iloc[idx]['Quantity'])
                new_qty = current_qty + qty
                row_index = idx + 2 
                
                inv_ws.update(range_name=f"C{row_index}:E{row_index}", values=[[buy_price, new_qty, "Available"]])
                st.success(f"Restocked '{selected_option}'! New Qty: {new_qty}. Price updated to RS {buy_price}.")
                clear_cache()
                st.rerun()

    else:
        st.subheader("Add New Item")
        new_item_name = st.text_input("🆕 Enter New Item Name")
        
        col1, col2 = st.columns(2)
        qty = col1.number_input("Initial Quantity", min_value=1, step=1, key="new_qty")
        buy_price = col2.number_input("Purchased Price (RS)", min_value=0.0, step=1.0, key="new_price")
        
        submitted = st.button("Save New Item", use_container_width=True, key="btn_new")
        
        if submitted:
            if new_item_name:
                if not df_inv.empty and new_item_name.lower() in df_inv['Item Name'].str.lower().tolist():
                    st.error(f"Item '{new_item_name}' already exists! Go to 'Restock Existing Item'.")
                else:
                    if not df_inv.empty and 'S No.' in df_inv.columns:
                        new_s_no = int(pd.to_numeric(df_inv['S No.'], errors='coerce').max() + 1) if pd.notna(pd.to_numeric(df_inv['S No.'], errors='coerce').max()) else 1
                    else:
                        new_s_no = len(df_inv) + 1
                    
                    inv_ws.insert_row([new_s_no, new_item_name, buy_price, qty, "Available"], index=2)
                    st.success(f"Added new item '{new_item_name}' to inventory!")
                    clear_cache()
                    st.rerun()
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
            selected_item = st.selectbox("🔍 Search & Select Item", available_items)
            
            col1, col2 = st.columns(2)
            qty_sold = col1.number_input("Quantity Sold", min_value=1, step=1)
            sell_price = col2.number_input("Selling Price Per Unit (RS)", min_value=0.0, step=1.0)
            
            sell_submitted = st.form_submit_button("Complete Sale")
            
            if sell_submitted and selected_item:
                item_data = df_inv[df_inv['Item Name'] == selected_item].iloc[0]
                current_qty = int(item_data['Quantity'])
                
                if qty_sold > current_qty:
                    st.error(f"Not enough stock! Only {current_qty} left.")
                else:
                    # Calculations
                    buy_price = float(item_data['Purchased price'])
                    profit = (sell_price - buy_price) * qty_sold
                    new_qty = current_qty - qty_sold
                    remarks = "Out of Stock" if new_qty == 0 else "Available"
                    
                    # Update Inventory Sheet
                    row_index_inv = int(item_data.name) + 2 
                    inv_ws.update(range_name=f"D{row_index_inv}:E{row_index_inv}", values=[[new_qty, remarks]])
                    
                    # 🔴 NEW LOGIC: Check if same item sold on same day with same price
                    df_sales = get_data(sales_ws)
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    
                    is_merged = False
                    if not df_sales.empty:
                        # Find matching row
                        matches = df_sales[
                            (df_sales['Date'] == date_str) & 
                            (df_sales['Item Name'].str.lower() == selected_item.lower()) &
                            (pd.to_numeric(df_sales['Sell price'], errors='coerce') == sell_price)
                        ]
                        
                        if not matches.empty:
                            # Merge with existing row
                            sale_idx = matches.index[0]
                            old_qty_sold = int(matches.iloc[0]['Quantity Sold'])
                            old_profit = float(matches.iloc[0]['Total Profit'])
                            
                            updated_qty = old_qty_sold + qty_sold
                            updated_profit = old_profit + profit
                            
                            row_index_sales = int(sale_idx) + 2
                            # Update Qty (Col F) and Profit (Col G)
                            sales_ws.update(range_name=f"F{row_index_sales}:G{row_index_sales}", values=[[updated_qty, updated_profit]])
                            is_merged = True
                            st.success(f"Updated today's entry! Total {updated_qty}x {selected_item} sold today.")
                    
                    # If not merged, append new row
                    if not is_merged:
                        if not df_sales.empty and 'S No.' in df_sales.columns:
                            max_val = pd.to_numeric(df_sales['S No.'], errors='coerce').max()
                            new_sales_no = int(max_val + 1) if pd.notna(max_val) else 1
                        else:
                            new_sales_no = len(df_sales) + 1
                        
                        sales_ws.append_row([
                            new_sales_no, date_str, selected_item, buy_price, sell_price, qty_sold, profit
                        ])
                        st.success(f"Sale successful! Sold {qty_sold}x {selected_item} for RS {sell_price} each.")
                    
                    clear_cache()
                    st.rerun()
    
    st.divider()
    
    # Undo / Delete a Sale
    st.subheader("↩️ Undo / Delete a Sale")
    st.info("Deleting a merged sale will restore the total combined quantity of that item for the day.")
    
    df_sales_current = get_data(sales_ws)
    
    if not df_sales_current.empty and 'S No.' in df_sales_current.columns:
        recent_sales = df_sales_current.tail(20).copy()
        sale_options = {}
        for index, row in recent_sales.iterrows():
            s_no = row['S No.']
            if pd.notna(s_no):
                label = f"Sale #{int(s_no)} | {row.get('Date', 'N/A')} | {row.get('Quantity Sold', 0)}x {row.get('Item Name', 'N/A')} | Profit: RS {row.get('Total Profit', 0)}"
                sale_options[label] = s_no
            
        if sale_options:
            with st.form("delete_sale_form"):
                selected_sale_label = st.selectbox("Select Recent Sale to Delete", list(sale_options.keys())[::-1])
                delete_submitted = st.form_submit_button("🗑️ Delete Sale & Restore Inventory")
                
                if delete_submitted and selected_sale_label:
                    s_no_to_delete = sale_options[selected_sale_label]
                    sale_record = df_sales_current[df_sales_current['S No.'] == s_no_to_delete].iloc[0]
                    item_name = sale_record['Item Name']
                    qty_to_restore = int(sale_record['Quantity Sold'])
                    
                    sale_idx = df_sales_current.index[df_sales_current['S No.'] == s_no_to_delete].tolist()[0]
                    sales_ws.delete_rows(sale_idx + 2) 
                    
                    df_inv_current = get_data(inv_ws)
                    if not df_inv_current.empty and item_name.lower() in df_inv_current['Item Name'].str.lower().tolist():
                        inv_idx = df_inv_current.index[df_inv_current['Item Name'].str.lower() == item_name.lower()].tolist()[0]
                        current_inv_qty = int(df_inv_current.iloc[inv_idx]['Quantity'])
                        new_qty = current_inv_qty + qty_to_restore
                        inv_row = inv_idx + 2
                        inv_ws.update(range_name=f"D{inv_row}:E{inv_row}", values=[[new_qty, "Available"]])
                    
                    st.success(f"Sale deleted! {qty_to_restore}x '{item_name}' have been restored.")
                    clear_cache()
                    st.rerun()
        else:
            st.write("No valid sales records available to delete.")
    else:
        st.write("No sales records available to delete.")

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
                req_ws.insert_row([date_str, req_item, 1], index=2)
                st.success(f"Logged new demand for '{req_item}'.")
            
            clear_cache()
            st.rerun()

# ==========================================
# TAB 4: DASHBOARD
# ==========================================
with tab4:
    st.header("Dashboard & Analytics")
    
    df_sales = get_data(sales_ws)
    df_inv = get_data(inv_ws)
    df_req = get_data(req_ws)
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    if not df_sales.empty:
        for col in ['Purchased price', 'Sell price', 'Quantity Sold', 'Total Profit']:
            if col in df_sales.columns:
                df_sales[col] = pd.to_numeric(df_sales[col], errors='coerce').fillna(0)
                
        if 'Purchased price' in df_sales.columns and 'Quantity Sold' in df_sales.columns:
            df_sales['Total Purchase Cost'] = df_sales['Purchased price'] * df_sales['Quantity Sold']
        if 'Sell price' in df_sales.columns and 'Quantity Sold' in df_sales.columns:
            df_sales['Total Revenue'] = df_sales['Sell price'] * df_sales['Quantity Sold']
            
    today_sales = 0
    today_profit = 0
    if not df_sales.empty and 'Date' in df_sales.columns:
        df_today = df_sales[df_sales['Date'] == today_str]
        if 'Total Revenue' in df_today.columns:
            today_sales = df_today['Total Revenue'].sum()
        if 'Total Profit' in df_today.columns:
            today_profit = df_today['Total Profit'].sum()
    
    col1, col2 = st.columns(2)
    col1.metric("Today's Total Revenue", f"RS {today_sales:.2f}")
    col2.metric("Today's Total Profit", f"RS {today_profit:.2f}")
    
    st.divider()
    
    st.subheader("📅 Daily Sales Report (Ledger)")
    if not df_sales.empty and 'Date' in df_sales.columns:
        unique_dates = sorted(df_sales['Date'].unique(), reverse=True)
        
        for date in unique_dates:
            df_day = df_sales[df_sales['Date'] == date]
            with st.expander(f"🗓️ Sales Date: {date}", expanded=(date == today_str)):
                cols_to_show = [col for col in ['Item Name', 'Purchased price', 'Sell price', 'Quantity Sold', 'Total Profit'] if col in df_day.columns]
                st.dataframe(df_day[cols_to_show], use_container_width=True, hide_index=True)
                
                net_purchased = df_day['Total Purchase Cost'].sum() if 'Total Purchase Cost' in df_day.columns else 0
                net_revenue = df_day['Total Revenue'].sum() if 'Total Revenue' in df_day.columns else 0
                net_profit = df_day['Total Profit'].sum() if 'Total Profit' in df_day.columns else 0
                
                st.markdown(f"**🛒 Net Purchase Cost:** RS {net_purchased:.2f} &nbsp;&nbsp;|&nbsp;&nbsp; **💰 Net Sales (Gross):** RS {net_revenue:.2f} &nbsp;&nbsp;|&nbsp;&nbsp; **📈 Net Profit:** RS {net_profit:.2f}")
    else:
        st.info("No sales data available yet.")

    st.divider()
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🔴 To-Buy / Restock List")
        if not df_inv.empty and 'Remarks' in df_inv.columns:
            out_of_stock = df_inv[df_inv['Remarks'] == "Out of Stock"]
            if not out_of_stock.empty:
                cols_to_show = [col for col in ['Item Name', 'Purchased price', 'Quantity'] if col in out_of_stock.columns]
                st.dataframe(out_of_stock[cols_to_show], use_container_width=True, hide_index=True)
            else:
                st.success("All items are in stock!")
        else:
            st.write("No inventory data.")

    with col_b:
        st.subheader("🔥 Demanded Items")
        if not df_req.empty and 'Demand Count' in df_req.columns:
            top_demands = df_req.sort_values(by="Demand Count", ascending=False)
            st.dataframe(top_demands, use_container_width=True, hide_index=True)
        else:
            st.write("No customer demands yet.")
