import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta

# --- 1. SETUP & PAGE CONFIG (Must be first) ---
st.set_page_config(page_title="Ihtesham Bartan and Karakari Store", page_icon="🏪", layout="wide", initial_sidebar_state="expanded")

# --- 2. VIBRANT, PROFESSIONAL & RESPONSIVE CUSTOM CSS ---
st.markdown("""
    <style>
    /* Hide Streamlit Branding but KEEP the sidebar toggle button */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}
    
    /* 🌟 Main App Background */
    .stApp {
        background-color: #f4f7f6;
    }
    
    /* =========================================
       📱 MOBILE DARK MODE FIX
       ========================================= */
    .stApp p, .stApp span, .stApp label, .stApp div[data-testid="stMarkdownContainer"] {
        color: #222222 !important;
    }
    table th, table td {
        color: #222222 !important;
    }
    div[data-testid="stMetricLabel"] > div, div[data-testid="stMetricLabel"] > div > p {
        color: #FF416C !important;
    }
    div[data-testid="stMetricValue"] > div {
        color: #1A2980 !important;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    .stButton>button, .stButton>button p, .stButton>button span {
        color: white !important;
    }
    /* ========================================= */
    
    /* 🎨 Colorful Gradient Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #1A2980 0%, #26D0CE 100%);
        box-shadow: 5px 0 15px rgba(0,0,0,0.1);
    }
    
    /* 📊 Beautiful Metric Cards (Dashboard) - MOBILE RESPONSIVE */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #ffffff 0%, #f9fbfd 100%);
        border: none;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0px 8px 20px rgba(0, 0, 0, 0.08);
        border-top: 6px solid #FF416C; 
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        width: 100% !important;
        box-sizing: border-box !important;
        overflow-wrap: break-word !important; 
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0px 12px 25px rgba(0, 0, 0, 0.15);
    }
    div[data-testid="metric-container"] > div:nth-child(1) {
        font-size: 16px !important;
        font-weight: 700 !important;
    }
    div[data-testid="metric-container"] > div:nth-child(2) {
        font-size: 28px !important;
        font-weight: 900 !important;
        white-space: normal !important; 
    }
    @media (max-width: 768px) {
        div[data-testid="metric-container"] {
            padding: 15px;
            margin-bottom: 10px;
        }
        div[data-testid="metric-container"] > div:nth-child(2) {
            font-size: 24px !important;
        }
    }
    
    /* 🖱️ Stunning Main App Buttons (Gradient) */
    .stButton>button {
        background: linear-gradient(to right, #FF416C, #FF4B2B) !important;
        border: none !important;
        border-radius: 30px !important;
        padding: 12px 25px !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        letter-spacing: 1px;
        box-shadow: 0 4px 15px rgba(255, 75, 43, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        transform: scale(1.05) translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(255, 75, 43, 0.6) !important;
    }
    
    /* 📲 Sidebar Menu Buttons */
    [data-testid="stSidebar"] .stButton>button {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 12px 15px !important;
        box-shadow: none !important;
        margin-bottom: 5px !important;
        width: 100% !important;
    }
    [data-testid="stSidebar"] .stButton>button div,
    [data-testid="stSidebar"] .stButton>button div p {
        justify-content: flex-start !important;
        text-align: left !important;
        width: 100%;
        font-weight: 500 !important;
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        background: rgba(255, 255, 255, 0.15) !important;
        transform: translateX(5px) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important;
    }
    /* ACTIVE/SELECTED SIDEBAR BUTTON */
    [data-testid="stSidebar"] .stButton>button[data-testid="baseButton-primary"],
    [data-testid="stSidebar"] .stButton>button[kind="primary"] {
        background: rgba(255, 255, 255, 0.25) !important;
        border-left: 5px solid #FFD700 !important;
        border-right: 1px solid rgba(255,255,255,0.1) !important;
        border-top: 1px solid rgba(255,255,255,0.1) !important;
        border-bottom: 1px solid rgba(255,255,255,0.1) !important;
        backdrop-filter: blur(10px) !important;
        font-weight: 800 !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
        transform: scale(1) !important; 
    }
    
    /* 🗂️ Beautiful Containers and Forms */
    [data-testid="stForm"], .streamlit-expanderHeader, div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: white !important;
        border-radius: 15px !important;
        border: 1px solid #e1e4e8 !important;
        box-shadow: 0 5px 15px rgba(0,0,0,0.04) !important;
    }
    
    /* ✨ Input Fields Glow Effect */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        border-radius: 10px !important;
        border: 1px solid #ced4da !important;
        transition: all 0.3s;
        color: #222222 !important;
    }
    .stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus {
        border-color: #26D0CE !important;
        box-shadow: 0 0 8px rgba(38, 208, 206, 0.5) !important;
    }
    
    /* 📝 Headings Gradient Text */
    h1, h2, h3 {
        color: #1A2980 !important;
        font-weight: 800 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. GOOGLE SHEETS CONNECTION & CACHING ---
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

try:
    sheet = init_connection()
except Exception as e:
    st.error(f"Google Sheets Connection Error: {e}")
    st.stop()

@st.cache_data(ttl=120) 
def get_data_cached(ws_name):
    try:
        ws = sheet.worksheet(ws_name)
        records = ws.get_all_records()
        df = pd.DataFrame(records)
        if not df.empty:
            df.columns = df.columns.astype(str).str.strip()
        return df
    except:
        return pd.DataFrame()

def clear_cache():
    st.cache_data.clear()

def get_pkt_date():
    return (datetime.utcnow() + timedelta(hours=5)).strftime("%Y-%m-%d")

# Safe Sheet Initialization
try:
    inv_ws = sheet.worksheet("Inventory")
    sales_ws = sheet.worksheet("Sales")
    req_ws = sheet.worksheet("Requested Items")
except Exception as e:
    st.error(f"Error accessing basic sheets. Details: {e}")
    st.stop()

try:
    cust_ws = sheet.worksheet("Customers")
    if not cust_ws.get_all_values():
        cust_ws.append_row(["Customer Name", "Phone", "Balance (RS)", "Last Updated"])
except:
    cust_ws = None

try:
    outflow_ws = sheet.worksheet("Cash Outflow")
    if not outflow_ws.get_all_values():
        outflow_ws.append_row(["Date", "Description", "Amount (RS)"])
except:
    outflow_ws = None


# --- 4. LOGIN SYSTEM WITH PERSISTENCE ---
USERS = {
    "admin": "admin123"
}
SHOP_INFO = {
    "admin": "Ihtesham Bartan and Karakari Store"
}

if "logged_in" not in st.session_state:
    if st.query_params.get("logged_in") == "true":
        st.session_state["logged_in"] = True
        st.session_state["username"] = st.query_params.get("user", "admin")
    else:
        st.session_state["logged_in"] = False

if "active_menu" not in st.session_state:
    st.session_state["active_menu"] = "📊 Dashboard"

def change_menu(new_menu):
    st.session_state["active_menu"] = new_menu

def login():
    st.markdown("<h1 style='text-align: center; background: -webkit-linear-gradient(#1A2980, #26D0CE); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>🏪 Ihtesham Bartan and Karakari Store</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #555;'>Secure Login Portal</h3>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("🔑 Login", use_container_width=True)
            
            if submit:
                if username in USERS and USERS[username] == password:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = username
                    st.query_params["logged_in"] = "true"
                    st.query_params["user"] = username
                    st.success("Login Successful! Redirecting...")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")


# --- 5. MAIN APP NAVIGATION & LOGIC ---
if not st.session_state["logged_in"]:
    login()
else:
    with st.sidebar:
        shop_title = SHOP_INFO.get(st.session_state['username'], "Your Store")
        st.markdown(f"### 🏪 Welcome to\n## <span style='color:#FFD700;'>{shop_title}</span>", unsafe_allow_html=True)
        st.divider()
        st.markdown("### 📌 Main Menu")
        
        menu_options = [
            "📊 Dashboard", 
            "🛒 Sell Item (POS)", 
            "📦 Add Item (Inventory)", 
            "📓 Khata (Credit)", 
            "💸 Cash Outflow", 
            "📝 Customer Demands"
        ]
        
        for option in menu_options:
            btn_type = "primary" if st.session_state["active_menu"] == option else "secondary"
            st.button(option, on_click=change_menu, args=(option,), type=btn_type, use_container_width=True)
        
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["logged_in"] = False
            st.query_params.clear()
            st.rerun()

    menu = st.session_state["active_menu"]

    st.title(f"✨ {menu}")
    st.markdown("---")

    # ==========================================
    # 📊 DASHBOARD
    # ==========================================
    if menu == "📊 Dashboard":
        df_sales = get_data_cached("Sales")
        df_inv = get_data_cached("Inventory")
        df_req = get_data_cached("Requested Items")
        df_outflow = get_data_cached("Cash Outflow")
        
        today_str = get_pkt_date()
        
        if not df_sales.empty:
            for col in ['Purchased price', 'Sell price', 'Quantity Sold', 'Total Profit']:
                if col in df_sales.columns:
                    df_sales[col] = pd.to_numeric(df_sales[col], errors='coerce').fillna(0)
                    
            if 'Purchased price' in df_sales.columns and 'Quantity Sold' in df_sales.columns:
                df_sales['Total Purchase Cost'] = df_sales['Purchased price'] * df_sales['Quantity Sold']
            if 'Sell price' in df_sales.columns and 'Quantity Sold' in df_sales.columns:
                df_sales['Total Revenue'] = df_sales['Sell price'] * df_sales['Quantity Sold']
                
        today_sales, today_profit, today_outflow = 0, 0, 0
        if not df_sales.empty and 'Date' in df_sales.columns:
            df_today = df_sales[df_sales['Date'] == today_str]
            if 'Total Revenue' in df_today.columns:
                today_sales = df_today['Total Revenue'].sum()
            if 'Total Profit' in df_today.columns:
                today_profit = df_today['Total Profit'].sum()
                
        if not df_outflow.empty and 'Date' in df_outflow.columns and 'Amount (RS)' in df_outflow.columns:
            df_outflow['Amount (RS)'] = pd.to_numeric(df_outflow['Amount (RS)'], errors='coerce').fillna(0)
            today_outflow = df_outflow[df_outflow['Date'] == today_str]['Amount (RS)'].sum()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Today's Total Revenue", f"RS {today_sales:,.2f}")
        col2.metric("📈 Today's Total Profit", f"RS {today_profit:,.2f}")
        col3.metric("💸 Today's Cash Outflow", f"RS {today_outflow:,.2f}")
        
        st.write("")
        st.subheader("📥 Download Financial Reports")
        dl_col1, dl_col2 = st.columns(2)
        
        with dl_col1:
            if not df_sales.empty:
                df_download_sales = df_sales.copy()
                total_qty = df_download_sales['Quantity Sold'].sum() if 'Quantity Sold' in df_download_sales.columns else 0
                total_profit = df_download_sales['Total Profit'].sum() if 'Total Profit' in df_download_sales.columns else 0
                total_purchase = df_download_sales['Total Purchase Cost'].sum() if 'Total Purchase Cost' in df_download_sales.columns else 0
                total_revenue = df_download_sales['Total Revenue'].sum() if 'Total Revenue' in df_download_sales.columns else 0
                
                total_row_sales = {col: "" for col in df_download_sales.columns}
                if 'Item Name' in total_row_sales: total_row_sales['Item Name'] = "TOTAL"
                if 'Quantity Sold' in total_row_sales: total_row_sales['Quantity Sold'] = total_qty
                if 'Total Profit' in total_row_sales: total_row_sales['Total Profit'] = total_profit
                if 'Total Purchase Cost' in total_row_sales: total_row_sales['Total Purchase Cost'] = total_purchase
                if 'Total Revenue' in total_row_sales: total_row_sales['Total Revenue'] = total_revenue
                    
                df_download_sales = pd.concat([df_download_sales, pd.DataFrame([total_row_sales])], ignore_index=True)
                csv_sales = df_download_sales.to_csv(index=False).encode('utf-8')
                
                st.download_button(label="📄 Download Sales Report (CSV)", data=csv_sales, file_name=f"sales_report_{today_str}.csv", mime="text/csv", use_container_width=True)
                
        with dl_col2:
            if not df_outflow.empty:
                df_download_outflow = df_outflow.copy()
                total_outflow_amount = df_download_outflow['Amount (RS)'].sum() if 'Amount (RS)' in df_download_outflow.columns else 0
                
                total_row_outflow = {col: "" for col in df_download_outflow.columns}
                if 'Description' in total_row_outflow: total_row_outflow['Description'] = "TOTAL"
                if 'Amount (RS)' in total_row_outflow: total_row_outflow['Amount (RS)'] = total_outflow_amount
                    
                df_download_outflow = pd.concat([df_download_outflow, pd.DataFrame([total_row_outflow])], ignore_index=True)
                csv_outflow = df_download_outflow.to_csv(index=False).encode('utf-8')
                
                st.download_button(label="💸 Download Cash Outflow Report (CSV)", data=csv_outflow, file_name=f"cash_outflow_report_{today_str}.csv", mime="text/csv", use_container_width=True)

        st.write("")
        st.subheader("📅 Daily Sales Report (Ledger)")
        if not df_sales.empty and 'Date' in df_sales.columns:
            unique_dates = sorted(df_sales['Date'].unique(), reverse=True)
            
            for date in unique_dates:
                df_day = df_sales[df_sales['Date'] == date]
                with st.expander(f"🗓️ Sales Date: {date}", expanded=(date == today_str)):
                    cols_to_show = [col for col in ['Item Name', 'Purchased price', 'Sell price', 'Quantity Sold', 'Unit', 'Total Profit'] if col in df_day.columns]
                    st.dataframe(df_day[cols_to_show], use_container_width=True, hide_index=True)
        else:
            st.info("No sales data available yet.")

        st.write("")
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("⚠️ Low Stock & Out of Stock List")
            if not df_inv.empty and 'Remarks' in df_inv.columns:
                low_or_out = df_inv[df_inv['Remarks'].isin(["Out of Stock", "Low Stock"])]
                if not low_or_out.empty:
                    cols_to_show = [col for col in ['Item Name', 'Quantity', 'Unit', 'Remarks'] if col in low_or_out.columns]
                    st.dataframe(low_or_out[cols_to_show], use_container_width=True, hide_index=True)
                else:
                    st.success("All items have sufficient stock!")

        with col_b:
            st.subheader("🔥 Demanded Items")
            if not df_req.empty and 'Demand Count' in df_req.columns:
                st.dataframe(df_req.sort_values(by="Demand Count", ascending=False), use_container_width=True, hide_index=True)


    # ==========================================
    # 🛒 SELL ITEM (POS)
    # ==========================================
    elif menu == "🛒 Sell Item (POS)":
        df_inv = get_data_cached("Inventory")
        
        if "cart" not in st.session_state:
            st.session_state.cart = []
        
        if df_inv.empty:
            st.warning("Inventory is empty. Add items first.")
        else:
            df_inv['Quantity'] = pd.to_numeric(df_inv['Quantity'], errors='coerce').fillna(0)
            available_items = df_inv[df_inv['Quantity'] > 0]['Item Name'].tolist()
            
            with st.container():
                st.subheader("🛒 1. Add Items to Cart")
                
                # 🔴 LIVE SEARCH BOX (Triggers Keyboard on Mobile!)
                search_term_pos = st.text_input("🔍 Live Search Item (Mobile Friendly)", placeholder="Type item name here to filter list...", key="search_pos")
                filtered_pos = [item for item in available_items if search_term_pos.lower() in item.lower()] if search_term_pos else available_items

                with st.form("add_to_cart_form"):
                    selected_item = st.selectbox("📌 Select Item from List", filtered_pos, index=None, placeholder="Choose an item...")
                    
                    c1, c2 = st.columns(2)
                    qty_sold = c1.number_input("Quantity / Weight Sold", min_value=0.01, value=None, step=1.0, format="%.2f", placeholder="Enter quantity...")
                    sell_price = c2.number_input("Selling Price (Per Unit/KG in RS)", min_value=0.0, value=None, step=1.0, placeholder="Enter selling price...")
                    
                    add_to_cart = st.form_submit_button("➕ Add to Cart")
                    
                    if add_to_cart:
                        if not selected_item:
                            st.error("Please select an item.")
                        elif qty_sold is None:
                            st.error("Please enter Quantity/Weight.")
                        elif sell_price is None:
                            st.error("Please enter the Selling Price.")
                        else:
                            item_data = df_inv[df_inv['Item Name'] == selected_item].iloc[0]
                            current_qty = float(item_data['Quantity'])
                            unit = str(item_data['Unit']) if 'Unit' in item_data else "Pcs"
                            buy_price = float(item_data['Purchased price'])
                            
                            if qty_sold > current_qty:
                                st.error(f"Not enough stock! Only {current_qty} {unit} left.")
                            else:
                                profit = (sell_price - buy_price) * qty_sold
                                st.session_state.cart.append({
                                    "Item Name": selected_item,
                                    "Qty": qty_sold,
                                    "Unit": unit,
                                    "Buy Price": buy_price,
                                    "Sell Price": sell_price,
                                    "Total Profit": profit,
                                    "Total Bill": sell_price * qty_sold
                                })
                                st.success(f"Added {qty_sold} {unit} of {selected_item} to cart!")

            if len(st.session_state.cart) > 0:
                st.write("")
                st.subheader("🧾 2. Current Cart & Checkout")
                cart_df = pd.DataFrame(st.session_state.cart)
                st.dataframe(cart_df[["Item Name", "Qty", "Unit", "Sell Price", "Total Bill"]], use_container_width=True)
                
                total_bill = cart_df['Total Bill'].sum()
                st.markdown(f"<h3 style='color: #FF416C;'>Grand Total: RS {total_bill:,.2f}</h3>", unsafe_allow_html=True)
                
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("🗑️ Clear Cart", use_container_width=True):
                        st.session_state.cart = []
                        st.rerun()
                with col_b2:
                    if st.button("✅ Complete Sale (Checkout)", use_container_width=True):
                        date_str = get_pkt_date()
                        df_sales = get_data_cached("Sales")
                        
                        if not df_sales.empty and 'S No.' in df_sales.columns:
                            new_sales_no = int(pd.to_numeric(df_sales['S No.'], errors='coerce').max() + 1) if pd.notna(pd.to_numeric(df_sales['S No.'], errors='coerce').max()) else 1
                        else:
                            new_sales_no = len(df_sales) + 1
                        
                        sales_rows_to_append = []
                        inv_ws = sheet.worksheet("Inventory")
                        sales_ws = sheet.worksheet("Sales")
                        
                        for item in st.session_state.cart:
                            idx = df_inv.index[df_inv['Item Name'] == item["Item Name"]].tolist()[0]
                            current_qty = float(df_inv.iloc[idx]['Quantity'])
                            new_qty = current_qty - item["Qty"]
                            remarks = "Out of Stock" if new_qty <= 0 else ("Low Stock" if new_qty <= 5 else "Available")
                            row_index_inv = idx + 2
                            
                            inv_ws.update(range_name=f"D{row_index_inv}:F{row_index_inv}", values=[[new_qty, item["Unit"], remarks]])
                            
                            sales_rows_to_append.append([
                                new_sales_no, date_str, item["Item Name"], item["Buy Price"], 
                                item["Sell Price"], item["Qty"], item["Unit"], item["Total Profit"]
                            ])
                            new_sales_no += 1
                            
                        if sales_rows_to_append:
                            sales_ws.append_rows(sales_rows_to_append)
                            
                        st.session_state.cart = []
                        st.success("🎉 Sale Completed Successfully! Inventory and Sales reports updated.")
                        clear_cache()
                        st.rerun()
                        
        st.write("")
        with st.expander("↩️ Undo / Delete a Recent Sale"):
            st.info("Deleting a sale will restore the total quantity of that item back to your inventory.")
            df_sales_current = get_data_cached("Sales")
            
            if not df_sales_current.empty and 'S No.' in df_sales_current.columns:
                recent_sales = df_sales_current.tail(20).copy()
                sale_options = {}
                for index, row in recent_sales.iterrows():
                    s_no = row['S No.']
                    if pd.notna(s_no):
                        unit_val = str(row.get('Unit', 'Pcs'))
                        label = f"Sale #{int(s_no)} | {row.get('Date', 'N/A')} | {row.get('Quantity Sold', 0)} {unit_val} {row.get('Item Name', 'N/A')} | Profit: RS {row.get('Total Profit', 0)}"
                        sale_options[label] = s_no
                    
                if sale_options:
                    with st.form("delete_sale_form"):
                        selected_sale_label = st.selectbox("Select Recent Sale to Delete", list(sale_options.keys())[::-1], index=None, placeholder="Select a sale to delete...")
                        delete_submitted = st.form_submit_button("🗑️ Delete Sale & Restore Inventory")
                        
                        if delete_submitted:
                            if selected_sale_label:
                                s_no_to_delete = sale_options[selected_sale_label]
                                sale_record = df_sales_current[df_sales_current['S No.'] == s_no_to_delete].iloc[0]
                                item_name = sale_record['Item Name']
                                qty_to_restore = float(sale_record['Quantity Sold'])
                                
                                sale_idx = df_sales_current.index[df_sales_current['S No.'] == s_no_to_delete].tolist()[0]
                                sales_ws = sheet.worksheet("Sales")
                                sales_ws.delete_rows(sale_idx + 2) 
                                
                                df_inv_current = get_data_cached("Inventory")
                                if not df_inv_current.empty and item_name.lower() in df_inv_current['Item Name'].str.lower().tolist():
                                    inv_idx = df_inv_current.index[df_inv_current['Item Name'].str.lower() == item_name.lower()].tolist()[0]
                                    current_inv_qty = float(df_inv_current.iloc[inv_idx]['Quantity'])
                                    new_qty = current_inv_qty + qty_to_restore
                                    remarks = "Out of Stock" if new_qty <= 0 else ("Low Stock" if new_qty <= 5 else "Available")
                                    
                                    inv_row = inv_idx + 2
                                    inv_ws = sheet.worksheet("Inventory")
                                    inv_ws.update(range_name=f"D{inv_row}:F{inv_row}", values=[[new_qty, sale_record.get('Unit', 'Pcs'), remarks]])
                                
                                st.success(f"Sale deleted! {qty_to_restore} of '{item_name}' have been restored.")
                                clear_cache()
                                st.rerun()
                            else:
                                st.error("Please select a sale to delete.")


    # ==========================================
    # 📦 ADD ITEM (INVENTORY)
    # ==========================================
    elif menu == "📦 Add Item (Inventory)":
        df_inv = get_data_cached("Inventory")
        
        action_type = st.radio("What do you want to do?", ["🔄 Restock Existing Item", "📦 Add Completely New Item"], horizontal=True)
        st.divider()
        
        if action_type == "🔄 Restock Existing Item":
            existing_items = df_inv['Item Name'].tolist() if not df_inv.empty else []
            if not existing_items:
                st.warning("No items in inventory yet. Please add a new item first.")
            else:
                with st.container():
                    # 🔴 LIVE SEARCH BOX (Triggers Keyboard on Mobile!)
                    search_term_inv = st.text_input("🔍 Live Search Item (Mobile Friendly)", placeholder="Type item name here to filter list...", key="search_inv")
                    filtered_inv = [item for item in existing_items if search_term_inv.lower() in item.lower()] if search_term_inv else existing_items

                    selected_option = st.selectbox("📌 Select Item from List", filtered_inv, index=None, placeholder="Choose an item...")
                    
                    default_price = None 
                    current_unit = "Pcs"
                    if selected_option:
                        idx = df_inv.index[df_inv['Item Name'] == selected_option].tolist()[0]
                        default_price = float(df_inv.iloc[idx]['Purchased price'])
                        if 'Unit' in df_inv.columns:
                            current_unit = str(df_inv.iloc[idx]['Unit'])
                        st.info(f"✔️ Selected: **{selected_option}** | Current Purchase Price: RS {default_price} | Unit: {current_unit}")
                        
                    col1, col2, col3 = st.columns([2, 1, 2])
                    qty = col1.number_input("Quantity to Add", min_value=0.01, value=None, step=1.0, key="exist_qty", format="%.2f", placeholder="Enter quantity...")
                    unit_select = col2.selectbox("Unit", ["Pcs", "KG", "Gram", "Liter", "Set"], index=["Pcs", "KG", "Gram", "Liter", "Set"].index(current_unit) if current_unit in ["Pcs", "KG", "Gram", "Liter", "Set"] else 0, key="exist_unit")
                    buy_price = col3.number_input("Update Purchased Price (RS)", min_value=0.0, value=default_price, step=1.0, key="exist_price", placeholder="Enter price...")
                    
                    submitted = st.button("Update Inventory", use_container_width=True)
                    
                    if submitted:
                        if not selected_option:
                            st.error("Please select an item first.")
                        elif qty is None:
                            st.error("Please enter the Quantity.")
                        elif buy_price is None:
                            st.error("Please enter the Purchased Price.")
                        else:
                            current_qty = float(df_inv.iloc[idx]['Quantity'])
                            new_qty = current_qty + qty
                            remarks = "Out of Stock" if new_qty <= 0 else ("Low Stock" if new_qty <= 5 else "Available")
                            row_index = idx + 2 
                            inv_ws = sheet.worksheet("Inventory")
                            inv_ws.update(range_name=f"C{row_index}:F{row_index}", values=[[buy_price, new_qty, unit_select, remarks]])
                            st.success(f"Restocked '{selected_option}'! New Qty: {new_qty} {unit_select}. Price updated to RS {buy_price}.")
                            clear_cache()
                            st.rerun()

        else:
            with st.container():
                new_item_name = st.text_input("🆕 Enter New Item Name", key="input_item_name")
                
                col1, col2, col3 = st.columns([2, 1, 2])
                qty = col1.number_input("Initial Quantity", min_value=0.01, value=None, step=1.0, key="input_qty", format="%.2f", placeholder="Enter quantity...")
                unit_select = col2.selectbox("Unit", ["Pcs", "KG", "Gram", "Liter", "Set"], key="input_unit")
                buy_price = col3.number_input("Purchased Price (RS)", min_value=0.0, value=None, step=1.0, key="input_price", placeholder="Type price here...")
                
                submitted = st.button("Save New Item", use_container_width=True)
                
                if submitted:
                    if not new_item_name:
                        st.error("Please provide an Item Name.")
                    elif qty is None:
                        st.error("Please enter the Initial Quantity.")
                    elif buy_price is None:
                        st.error("Please enter the Purchased Price.")
                    else:
                        if not df_inv.empty and new_item_name.lower() in df_inv['Item Name'].str.lower().tolist():
                            st.error(f"Item '{new_item_name}' already exists! Go to 'Restock Existing Item'.")
                        else:
                            if not df_inv.empty and 'S No.' in df_inv.columns:
                                new_s_no = int(pd.to_numeric(df_inv['S No.'], errors='coerce').max() + 1) if pd.notna(pd.to_numeric(df_inv['S No.'], errors='coerce').max()) else 1
                            else:
                                new_s_no = len(df_inv) + 1
                            
                            remarks = "Out of Stock" if qty <= 0 else ("Low Stock" if qty <= 5 else "Available")
                            inv_ws = sheet.worksheet("Inventory")
                            inv_ws.insert_row([new_s_no, new_item_name, buy_price, qty, unit_select, remarks], index=2)
                            st.success(f"Added new item '{new_item_name}' ({qty} {unit_select}) to inventory successfully!")
                            clear_cache()
                            st.rerun()


    # ==========================================
    # 📓 KHATA (CUSTOMER CREDIT)
    # ==========================================
    elif menu == "📓 Khata (Credit)":
        if cust_ws is None:
            st.error("⚠️ Please create a new worksheet named 'Customers' in your Google Sheet.")
        else:
            df_cust = get_data_cached("Customers")
            col_c1, col_c2 = st.columns([1, 1.5])
            
            with col_c1:
                with st.container():
                    st.subheader("➕ Add / Update Credit")
                    with st.form("khata_form"):
                        cust_name = st.text_input("Customer Name")
                        cust_phone = st.text_input("Phone Number")
                        amount = st.number_input("Amount (RS)", min_value=0.01, value=None, step=1.0, placeholder="Enter amount...")
                        action = st.radio("Transaction Type", ["Gave Credit (Udhaar Diya)", "Received Payment (Pैसे Mile)"])
                        
                        khata_submitted = st.form_submit_button("Save Transaction")
                        
                        if khata_submitted:
                            if not cust_name or amount is None or amount <= 0:
                                st.error("Please enter valid Name and Amount.")
                            else:
                                date_str = get_pkt_date()
                                cust_ws_live = sheet.worksheet("Customers")
                                if not df_cust.empty and 'Customer Name' in df_cust.columns and cust_name.lower() in df_cust['Customer Name'].str.lower().tolist():
                                    idx = df_cust.index[df_cust['Customer Name'].str.lower() == cust_name.lower()].tolist()[0]
                                    current_balance = float(df_cust.iloc[idx]['Balance (RS)'] if 'Balance (RS)' in df_cust.columns and pd.notna(df_cust.iloc[idx]['Balance (RS)']) else 0)
                                    
                                    new_balance = current_balance + amount if action == "Gave Credit (Udhaar Diya)" else current_balance - amount
                                    row_idx = idx + 2
                                    cust_ws_live.update(range_name=f"C{row_idx}:D{row_idx}", values=[[new_balance, date_str]])
                                    st.success(f"Updated Khata for {cust_name}! New Balance: RS {new_balance:.2f}")
                                else:
                                    initial_balance = amount if action == "Gave Credit (Udhaar Diya)" else -amount
                                    cust_ws_live.append_row([cust_name, cust_phone, initial_balance, date_str])
                                    st.success(f"Added new customer {cust_name} with balance RS {initial_balance:.2f}")
                                clear_cache()
                                st.rerun()

            with col_c2:
                st.subheader("📋 Customers Khata List")
                if not df_cust.empty:
                    cols_to_show = [c for c in ['Customer Name', 'Phone', 'Balance (RS)', 'Last Updated'] if c in df_cust.columns]
                    st.dataframe(df_cust[cols_to_show], use_container_width=True, hide_index=True)
                    if 'Balance (RS)' in df_cust.columns:
                        total_market_udhaar = pd.to_numeric(df_cust['Balance (RS)'], errors='coerce').sum()
                        st.info(f"**Total Market Udhaar (Receivable): RS {total_market_udhaar:,.2f}**")


    # ==========================================
    # 💸 CASH OUTFLOW
    # ==========================================
    elif menu == "💸 Cash Outflow":
        if outflow_ws is None:
            st.error("⚠️ Please create a new worksheet named 'Cash Outflow' in your Google Sheet.")
        else:
            df_outflow = get_data_cached("Cash Outflow")
            col_o1, col_o2 = st.columns([1, 1.5])
            
            with col_o1:
                with st.container():
                    st.subheader("➕ Add Cash Outflow")
                    with st.form("outflow_form"):
                        desc = st.text_input("Description (e.g., Shopping, Bill)")
                        outflow_amount = st.number_input("Total Amount (RS)", min_value=0.01, value=None, step=1.0, placeholder="Enter amount...")
                        outflow_submitted = st.form_submit_button("Save Cash Outflow")
                        
                        if outflow_submitted:
                            if not desc or outflow_amount is None or outflow_amount <= 0:
                                st.error("Please enter valid description and amount.")
                            else:
                                date_str = get_pkt_date()
                                outflow_ws_live = sheet.worksheet("Cash Outflow")
                                outflow_ws_live.insert_row([date_str, desc, outflow_amount], index=2)
                                st.success(f"Logged Cash Outflow of RS {outflow_amount:.2f}")
                                clear_cache()
                                st.rerun()
                            
            with col_o2:
                st.subheader("📋 Recent Cash Outflows")
                if not df_outflow.empty:
                    cols_to_show = [c for c in ['Date', 'Description', 'Amount (RS)'] if c in df_outflow.columns]
                    st.dataframe(df_outflow[cols_to_show], use_container_width=True, hide_index=True)


    # ==========================================
    # 📝 CUSTOMER DEMANDS
    # ==========================================
    elif menu == "📝 Customer Demands":
        with st.container():
            st.info("Log items requested by customers that you don't currently stock.")
            with st.form("demand_form"):
                req_item = st.text_input("Requested Item Name")
                req_submit = st.form_submit_button("Log Demand")
                
                if req_submit and req_item:
                    df_req = get_data_cached("Requested Items")
                    date_str = get_pkt_date()
                    req_ws_live = sheet.worksheet("Requested Items")
                    
                    if not df_req.empty and req_item.lower() in df_req['Item Name'].str.lower().tolist():
                        idx = df_req.index[df_req['Item Name'].str.lower() == req_item.lower()].tolist()[0]
                        current_count = int(df_req.iloc[idx]['Demand Count'])
                        
                        row_index = idx + 2
                        req_ws_live.update_acell(f"C{row_index}", current_count + 1)
                        req_ws_live.update_acell(f"A{row_index}", date_str) 
                    else:
                        req_ws_live.insert_row([date_str, req_item, 1], index=2)
                    
                    st.success("Demand Logged Successfully!")
                    clear_cache()
                    st.rerun()
