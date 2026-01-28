import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json
from PIL import Image
from datetime import datetime

# --- 1. PAGE SETUP (App ka naam aur icon) ---
st.set_page_config(page_title="KhataBook AI", page_icon="💰", layout="centered")

# --- 2. SECRETS SETUP (Tijori ki chabi) ---
# Ye code check karega ki password Streamlit ke secrets mein hai ya nahi
try:
    if "google_creds" in st.secrets:
        # Cloud par chala rahe hain
        creds_dict = dict(st.secrets["google_creds"])
        gemini_key = st.secrets["GEMINI_API_KEY"]
    else:
        # Agar secrets nahi mile
        st.error("⚠️ Secrets nahi mile! Streamlit settings check karo.")
        st.stop()
except Exception as e:
    st.error(f"Setup Error: {e}")
    st.stop()

# --- 3. CONNECTION (Google & AI) ---
# Gemini AI ko start karo
genai.configure(api_key=gemini_key)

# Google Sheets se connect karo
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Sheet kholo (Naam 'Expenses' hi hona chahiye)
SHEET_NAME = "Expenses"
try:
    sheet = client.open(SHEET_NAME).sheet1
except:
    st.error(f"❌ Error: '{SHEET_NAME}' naam ki Google Sheet nahi mili! Sheet ka naam check kar.")
    st.stop()

# --- 4. THE BRAIN (AI Logic) ---
def analyze_expense(input_type, content):
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    # AI ko instruction
    prompt = """
    You are an expert accountant. Extract expense details from this input into JSON format.
    Fields required:
    1. 'Date': DD/MM/YYYY (If not mentioned, use today's date)
    2. 'Item': What was purchased? (Short name)
    3. 'Category': Choose from [Food, Travel, Bills, Shopping, Business, Misc]
    4. 'Amount': Only the number (e.g., 500)
    5. 'PaymentMode': UPI, Cash, or Card (Guess if not clear)

    Output STRICTLY JSON. Do not add any markdown like ```json.
    """
    
    try:
        if input_type == "text":
            response = model.generate_content([prompt, f"User Input: {content}"])
        elif input_type == "image":
            response = model.generate_content([prompt, content])
            
        # Safai (Cleaning JSON)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        return None

# --- 5. THE APP UI (Jo screen pe dikhega) ---
st.title("💰 AI Munim Ji")
st.caption("Powered by Ashu Khandelwal Enterprise")

# Tabs banaye (Likhne ke liye aur Photo ke liye)
tab1, tab2 = st.tabs(["📝 Likho (Chat)", "📸 Bill Scan"])

# --- TAB 1: TEXT ---
with tab1:
    text_val = st.chat_input("Aaj kya kharcha hua? (e.g. 200 ka burger khaya)")
    if text_val:
        # Chat style message
        with st.chat_message("user"):
            st.write(text_val)
            
        with st.spinner("Munim ji likh rahe hain..."):
            data = analyze_expense("text", text_val)
            
            if data:
                # Save to Sheet
                sheet.append_row([data['Date'], data['Item'], data['Category'], data['Amount'], data['PaymentMode']])
                with st.chat_message("assistant"):
                    st.success(f"✅ Likh liya: ₹{data['Amount']} - {data['Item']}")
            else:
                st.error("Samajh nahi aaya, dobara likho.")

# --- TAB 2: CAMERA ---
with tab2:
    cam_img = st.camera_input("Bill ki photo lo")
    if cam_img:
        img = Image.open(cam_img)
        if st.button("Bill Save Karo"):
            with st.spinner("Bill padh raha hu..."):
                data = analyze_expense("image", img)
                if data:
                    sheet.append_row([data['Date'], data['Item'], data['Category'], data['Amount'], data['PaymentMode']])
                    st.balloons() # Thoda celebration
                    st.success(f"✅ Bill Saved: ₹{data['Amount']} ({data['Item']})")
                else:
                    st.error("Bill saaf nahi hai.")

# --- 6. DASHBOARD (Live Hisaab) ---
st.divider()
st.subheader("📊 Live Hisaab")

# Sheet se data layenge
try:
    records = sheet.get_all_records()
    if records:
        df = pd.DataFrame(records)
        
        # Agar data hai to calculation dikhao
        if 'Amount' in df.columns:
            # Total Calculation
            total_kharcha = df['Amount'].sum()
            st.metric(label="Total Kharcha (Till Date)", value=f"₹{total_kharcha}")
            
            # Recent 5 Entries
            st.write("Haal hi ke kharche:")
            st.dataframe(df.tail(5))
        else:
            st.warning("Sheet mein 'Amount' column nahi mila. Header check karo.")
    else:
        st.info("Abhi Register khali hai. Pehli entry karo!")
except Exception as e:
    st.error("Data load nahi ho pa raha.")
