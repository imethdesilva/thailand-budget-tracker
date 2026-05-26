import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import google.generativeai as genai

# --- 1. CONFIGURATION & PLACEHOLDERS ---
# Change these URLs to the actual photos of your friends
USER_CONFIG = {
    "Imeth": {"image": "https://lh3.googleusercontent.com/d/1Ro1gD6yriIEY5XwGdHvmKngI7cLdCQ1I", "color": "#FF4B4B"},
    "Kavindu": {"image": "https://lh3.googleusercontent.com/d/1r848IZj4NzR5bZB7EIhWW8G7I7sgWXPb", "color": "#1F77B4"},
    "Ramith": {"image": "https://lh3.googleusercontent.com/d/1OFdMcqdGpIYXylLHd7B5knV_6fNLCcph", "color": "#2CA02C"},
    "Sandali": {"image": "https://lh3.googleusercontent.com/d/1uz8OKtLcKcFaFlmWjA0fNW_Sv4P6RPV8", "color": "#FF7F0E"},
}

# Mock Exchange Rates (In a real app, you'd fetch from an API)
THB_TO_LKR = 9.95
USD_TO_LKR = 323.99

# --- 2. APP SESSION STATE (Database) ---
if 'data' not in st.session_state:
    st.session_state.data = {
        name: {
            "total_budget": 50000.0,
            "expenses": [
                {"category": "Initial", "amount": 0.0, "note": "Starter"}
            ]
        } for name in USER_CONFIG.keys()
    }

if 'messages' not in st.session_state:
    st.session_state.messages = []

# --- 3. STYLING ---
st.set_page_config(page_title="ThaiBudget Tracker", page_icon="🇹🇭", layout="centered")

st.markdown("""
    <style>
    .main { background: #f0f2f6; }
    .stApp { max-width: 500px; margin: 0 auto; } /* Mobile optimization */
    .leaderboard-card {
        background: white;
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 10px;
        border-left: 5px solid #FFD700;
    }
    .stat-box {
        background: #1E1E1E;
        color: gold;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        font-size: 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. HEADER SECTION ---
def get_thai_time():
    thai_tz = pytz.timezone('Asia/Bangkok')
    return datetime.now(thai_tz).strftime("%I:%M %p")

col1, col2 = st.columns([1, 1])
with col1:
    st.markdown(f"### 🇹🇭 {get_thai_time()}")
    st.caption("Bangkok, Thailand")

with col2:
    st.markdown(f"**฿1 = {THB_TO_LKR} LKR**")
    st.markdown(f"**$1 = {USD_TO_LKR} LKR**")

st.title("Causeway Budget 2026")

# --- 5. LEADERBOARD LOGIC ---
leaderboard_data = []
for name, info in st.session_state.data.items():
    spent = sum(item['amount'] for item in info['expenses'])
    remaining = info['total_budget'] - spent
    percent = (remaining / info['total_budget']) * 100 if info['total_budget'] > 0 else 0
    leaderboard_data.append({
        "name": name,
        "remaining": remaining,
        "percent": max(0, percent),
        "spent": spent
    })

# Sort by most money left
leaderboard_data = sorted(leaderboard_data, key=lambda x: x['remaining'], reverse=True)

st.subheader("Don't go broke in Thailand")

for person in leaderboard_data:
    with st.container():
        cols = st.columns([1, 3])
        with cols[0]:
            st.image(USER_CONFIG[person['name']]['image'], width=70)
        with cols[1]:
            st.markdown(f"**{person['name']}**")
            st.progress(person['percent'] / 100)
            st.caption(f"Remaining: ฿{person['remaining']:.2f} / Spent: ฿{person['spent']:.2f}")
            
            # --- POPUP / EXPANDER FOR CRUD ---
            with st.expander(f"Update {person['name']}'s Wallet"):
                # Update Total Budget
                new_total = st.number_input(f"Total Budget (฿)", value=st.session_state.data[person['name']]['total_budget'], key=f"tot_{person['name']}")
                st.session_state.data[person['name']]['total_budget'] = new_total
                
                st.divider()
                
                # Add Expense
                st.write("Add New Expense")
                cat = st.selectbox("Category", ["Food 🍜", "Transport 🚕", "Alcohol 🍺", "Shopping 🛍️", "Misc 🎟️"], key=f"cat_{person['name']}")
                amt = st.number_input("Amount (฿)", min_value=0.0, key=f"amt_{person['name']}")
                note = st.text_input("Note", key=f"note_{person['name']}")
                
                if st.button(f"Add Expense for {person['name']}", use_container_width=True):
                    st.session_state.data[person['name']]['expenses'].append({"category": cat, "amount": amt, "note": note})
                    st.rerun()

                # View/Delete History
                st.write("History")
                df = pd.DataFrame(st.session_state.data[person['name']]['expenses'])
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                    if st.button("Clear Last Entry", key=f"del_{person['name']}"):
                        st.session_state.data[person['name']]['expenses'].pop()
                        st.rerun()

# --- 6. AI CHATBOT (CHUTIPAN) ---
st.divider()
st.subheader("🤖 Ask Chutipan")
st.caption("Your Thai Itinerary Guide")

# --- AI CONFIGURATION ---
# --- AI CONFIGURATION (Updated to Gemini 1.5 Flash) ---
if "GEMINI_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # Using 'gemini-1.5-flash' for speed and better performance
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction="You are Chutipan, a helpful and fun Thai travel guide. You are helping Imeth, Kavindu, Ramith, and Sandali on their trip. Always start with 'Sawadee ka! 🙏'. Keep answers concise, use emojis, and give local Thai advice."
        )
    except Exception as e:
        st.error(f"Configuration Error: {e}")
else:
    st.error("API Key missing! Add GEMINI_API_KEY to Streamlit Secrets.")

# --- CHATBOT UI ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask Chutipan..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # With 1.5 Flash, we don't need to repeat instructions in the prompt
            # because we used 'system_instruction' above.
            response = model.generate_content(prompt)
            
            full_res = response.text
            st.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
        except Exception as e:
            st.error("Chutipan is currently stuck in Bangkok traffic. Try again in a second!")
            st.info(f"Error details: {e}")

# --- 7. EXTRA FEATURES ---
with st.sidebar:
    st.header("Settings & Tools")
    st.info("💡 Tip: Street food in Bangkok costs roughly 50-100 Baht per meal.")
    
    if st.button("Reset All Data"):
        st.session_state.data = {name: {"total_budget": 50000.0, "expenses": []} for name in USER_CONFIG.keys()}
        st.rerun()

