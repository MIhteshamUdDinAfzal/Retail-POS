import os
import tempfile
import json
import streamlit as st
import streamlit.components.v1 as components
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta
import time

# --- NEW LIBRARIES FOR AI VOICE ASSISTANT ---
from audio_recorder_streamlit import audio_recorder
from groq import Groq
import google.generativeai as genai

# ==========================================
# 🛑 1. PERMANENT FORCE LIGHT MODE CONFIG
# ==========================================
if not os.path.exists('.streamlit'):
    os.makedirs('.streamlit')
config_path = '.streamlit/config.toml'
if not os.path.exists(config_path):
    with open(config_path, 'w') as f:
        f.write('[theme]\nbase="light"\nprimaryColor="#FF416C"\n')

# --- 2. SETUP & PAGE CONFIG ---
st.set_page_config(page_title="Ihtesham Bartan and Karakari Store", page_icon="🏪", layout="wide", initial_sidebar_state="expanded")

# --- 3. VIBRANT & CRASH-PROOF CSS ---
st.markdown("""
    <style>
    /* =========================================
       📱 EXTREME FORCE LIGHT MODE
       ========================================= */
    :root, html, body { color-scheme: light !important; background-color: #f4f7f6 !important; }
    .stApp, .main, div[data-testid="stAppViewContainer"] { background-color: #f4f7f6 !important; color: #222222 !important; }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}
    
    /* Force General Text to Black */
    p, span, div, h1, h2, h3, h4, h5, h6, label, li { color: #222222 !important; }
    
    /* Exceptions */
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #ffffff !important; }
    .stButton > button * { color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; }
    div[data-testid="stDownloadButton"] > button * { color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; }
    div[data-testid="metric-container"] > div:nth-child(1) { color: #FF416C !important; }
    div[data-testid="metric-container"] > div:nth-child(2) { color: #1A2980 !important; }
    
    /* =========================================
       🍔 CRASH-PROOF MENU BUTTON (Replaces Arrows)
       ========================================= */
    /* 1. Hide all SVG icons in Header and Sidebar close buttons */
    [data-testid="collapsedControl"] svg { display: none !important; }
    [data-testid="stSidebar"] button[aria-label="Close sidebar"] svg { display: none !important; }
    
    /* 2. Add 'Menu' text and style the top-left button */
    [data-testid="collapsedControl"] button {
        background-color: #ffffff !important;
        border-radius: 8px !important;
        padding: 6px 14px !important;
        border: 2px solid #26D0CE !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important;
        width: auto !important;
        height: auto !important;
    }
    [data-testid="collapsedControl"] button::after {
        content: "☰ Menu" !important;
        font-size: 16px !important;
        font-weight: 900 !important;
        color: #1A2980 !important;
        display: block !important;
        visibility: visible !important;
    }
    
    /* 3. Add 'X Close' text to the sidebar close button */
    [data-testid="stSidebar"] button[aria-label="Close sidebar"] {
        background-color: transparent !important;
        width: auto !important;
        height: auto !important;
        padding: 5px !important;
    }
    [data-testid="stSidebar"] button[aria-label="Close sidebar"]::after {
        content: "✖ Close" !important;
        font-size: 16px !important;
        font-weight: bold !important;
        color: #FFD700 !important;
        display: block !important;
        visibility: visible !important;
    }
    
    /* =========================================
       📝 FIX TABLES, FORMS & INPUTS
       ========================================= */
    table, th, td, tr, tbody, thead { background-color: #ffffff !important; color: #000000 !important; border-color: #dddddd !important; }
    [data-testid="stForm"], .streamlit-expanderHeader, div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: #ffffff !important; border-radius: 15px !important; border: 1px solid #ced4da !important; box-shadow: 0 5px 15px rgba(0,0,0,0.04) !important;
    }
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div { background-color: #ffffff !important; border-radius: 8px !important; border: 1px solid #aaa !important; }
    input, select, textarea, div[data-baseweb="select"] span { color: #000000 !important; -webkit-text-fill-color: #000000 !important; font-weight: 600 !important; }
    div[data-baseweb="popover"], ul[role="listbox"], li[role="option"] { background-color: #ffffff !important; color: #000000 !important; }
    li[role="option"]:hover { background-color: #e2e6ea !important; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background: linear-gradient(135deg, #1A2980 0%, #26D0CE 100%); box-shadow: 5px 0 15px rgba(0,0,0,0.1); }
    
    /* Metric Cards */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #ffffff 0%, #f9fbfd 100%); border-radius: 15px; padding: 20px; box-shadow: 0px 8px 20px rgba(0, 0, 0, 0.08); border-top: 6px solid #FF416C; width: 100% !important; box-sizing: border-box !important; overflow-wrap: break-word !important; 
    }
    div[data-testid="metric-container"] > div:nth-child(2) { font-size: 28px !important; font-weight: 900 !important; white-space: normal !important; }
    @media (max-width: 768px) { div[data-testid="metric-container"] { padding: 15px; margin-bottom: 10px; } div[data-testid="metric-container"] > div:nth-child(2) { font-size: 24px !important; } }
    
    /* Buttons */
    .stButton>button { background: linear-gradient(to right, #FF416C, #FF4B2B) !important; border-radius: 30px !important; padding: 12px 25px !important; font-weight: 700 !important; box-shadow: 0 4px 15px rgba(255, 75, 43, 0.4) !important; }
    div[data-testid="stDownloadButton"] > button { background: linear-gradient(to right, #1A2980, #26D0CE) !important; border-radius: 30px !important; box-shadow: 0 4px 15px rgba(38, 208, 206, 0.4) !important; width: 100% !important; }
    
    /* Sidebar Menu Buttons */
    [data-testid="stSidebar"] .stButton>button { background: rgba(255, 255, 255, 0.05) !important; border-radius: 12px !important; margin-bottom: 5px !important; }
    [data-testid="stSidebar"] .stButton>button[kind="primary"] { background: rgba(255, 255, 255, 0.25) !important; border-left: 5px solid #FFD700 !important; font-weight: 800 !important; }
    h1, h2, h3 { font-weight: 800 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 4. GOOGLE SHEETS CONNECTION & CACHING ---
@st.cache_resource
def init_connection():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_url(st.secrets["gsheets"]["spreadsheet_url"])

try:
    sheet = init_connection()
except Exception as e:
    st.error(f"Google Sheets Connection Error: {e}")
    st.stop()

@st.cache_data(ttl=120) 
def get_data_cached(ws_name):
    try:
        ws = sheet.worksheet(ws_name)
        df = pd.DataFrame(ws.get_all_records())
        if not df.empty: df.columns = df.columns.astype(str).str.strip()
        return df
    except:
        return pd.DataFrame()

def clear_cache(): st.cache_data.clear()
def get_pkt_date(): return (datetime.utcnow() + timedelta(hours=5)).strftime("%Y-%m-%d")

try:
    inv_ws = sheet.worksheet("Inventory")
    sales_ws = sheet.worksheet("Sales")
    req_ws = sheet.worksheet("Requested Items")
except Exception as e:
    st.error(f"Error accessing basic sheets. Details: {e}"); st.stop()

try:
    cust_ws = sheet.worksheet("Customers")
    if not cust_ws.get_all_values(): cust_ws.append_row(["Customer Name", "Phone", "Balance (RS)", "Last Updated"])
except: cust_ws = None

try:
    outflow_ws = sheet.worksheet("Cash Outflow")
    if not outflow_ws.get_all_values(): outflow_ws.append_row(["Date", "Description", "Amount (RS)"])
except: outflow_ws = None


# --- AI VOICE ASSISTANT FUNCTION ---
GROQ_API_KEY = st.secrets.get("ai_keys", {}).get("GROQ_API_KEY", "")
GEMINI_API_KEY = st.secrets.get("ai_keys", {}).get("GEMINI_API_KEY", "")

def process_voice_command(audio_bytes, valid_items, task_type="sell"):
    if not GROQ_API_KEY or not GEMINI_API_KEY:
        st.error("⚠️ API Keys Missing in Secrets!")
        return None
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
            
        with open(tmp_path, "rb") as f:
            transcription = groq_client.audio.transcriptions.create(
                file=(tmp_path, f.read()),
                model="whisper-large-v3",
                language="ur"
            )
        user_text = transcription.text
        st.info(f"🗣️ آپ نے کہا: {user_text}")
        
        prompt = f"""
        You are an Urdu Retail Assistant. Extract data for a '{task_type}' operation.
        Available Items in shop: {valid_items}
        User said: "{user_text}"
        
        Return ONLY a raw JSON object (no markdown, no backticks). Format:
        {{
            "item_name": "Closest exact matching name from Available Items (or 'Unknown')",
            "quantity": float or int (default to 1 if not mentioned),
            "price": float or int (if explicitly mentioned, else null)
        }}
        """
        response = model.generate_content(prompt)
        raw_json = response.text.replace('```json', '').replace('
