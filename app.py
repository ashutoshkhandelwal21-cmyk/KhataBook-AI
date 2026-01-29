import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json
from PIL import Image

# --- 1. PAGE SETUP (Thoda Clean UI) ---
st.set_page_config(page_title="Smart Munim", page_icon="💳", layout="centered")
st.title("💳 Smart Munim Ji")
st.caption("Gallery se photo uthao ya camera se khicho!")

# --- 2. CONNECTION (Bulletproof Wala) ---
try:
    if "google_json" in st.secrets:
        # Secrets se JSON data padh rahe hain
        creds_dict = json.loads(st.secrets["google_json"])
        gemini_key = st.secrets["GEMINI_API_KEY"]
        
        # Google Sheets se connect
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("Expenses").sheet1
        
        # AI setup
        genai.configure(api_key=gemini_key)
    else:
        st.error("Secrets missing! Settings check karo.")
        st.stop()
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

# --- 3. AI BRAIN ---
def analyze_expense(content, input_type):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = """
    Extract expense details into JSON.
    Fields: Date (DD/MM/YYYY), Item, Category (Food/Travel/Bills/Misc), Amount (Number), PaymentMode.
    If date is missing, use today.
    Output ONLY JSON. No markdown.
    """
    try:
        with st.spinner("Munim ji dimaag laga rahe hain... 🧠"):
            if input_type == "image":
                response = model.generate_content([prompt, content])
            else:
                response = model.generate_content([prompt, f"Text: {content}"])
                
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
    except Exception as e:
        return None

# --- 4. APP UI (3 Options) ---
# Tabs banaye hain taaki screen saaf dikhe
tab1, tab2, tab3 = st.tabs(["📂 Gallery Upload", "📸 Camera", "✍️ Type"])

# --- OPTION 1: GALLERY (Sabse Best Mobile ke liye) ---
with tab1:
    st.write("Phone ki Gallery se saaf photo select karo:")
    uploaded_file = st.file_uploader("Choose Image", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Bill Preview", use_column_width=True)
        
        if st.button("Hisaab Save Karo (Upload)", type="primary"):
            data = analyze_expense(image, "image")
            if data:
                sheet.append_row(list(data.values()))
                st.balloons()
                st.success(f"✅ Likh diya: ₹{data.get('Amount')} ({data.get('Item')})")
            else:
                st.error("Photo samajh nahi aayi. Dobara try karo.")

# --- OPTION 2: CAMERA (Direct) ---
with tab2:
    cam_img = st.camera_input("Photo Khicho")
    if cam_img:
        image = Image.open(cam_img)
        if st.button("Hisaab Save Karo (Cam)"):
            data = analyze_expense(image, "image")
            if data:
                sheet.append_row(list(data.values()))
                st.balloons()
                st.success(f"✅ Saved: ₹{data.get('Amount')}")
            else:
                st.error("Blurry Image? Gallery wala tab use karo.")

# --- OPTION 3: TYPE (Backup) ---
with tab3:
    text_val = st.text_input("Likho (e.g. 50rs Chai)")
    if st.button("Add"):
        data = analyze_expense(text_val, "text")
        if data:
            sheet.append_row(list(data.values()))
            st.success(f"✅ Added: {text_val}")

# --- 5. DATA CHECK ---
st.divider()
try:
    df = pd.DataFrame(sheet.get_all_records())
    if not df.empty:
        st.caption("📋 Haal hi ke kharche:")
        st.dataframe(df.tail(3)) # Sirf last 3 dikhayega taaki phone pe bheed na ho
except:
    pass
