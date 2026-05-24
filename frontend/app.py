import streamlit as st
import httpx
import requests
import uuid
import asyncio
import base64
from config import API_BASE_URL, APP_TITLE, APP_SUBTITLE, THEME_LIGHT, THEME_DARK, EXAMPLE_QUERIES, INTENT_METADATA

# ══════════════════════════════════════════════════════════════
# 1. PAGE CONFIGURATION & STATE
# ══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "memory_state" not in st.session_state:
    st.session_state.memory_state = {}

if "light_mode" not in st.session_state:
    st.session_state.light_mode = False

# ══════════════════════════════════════════════════════════════
# 2. TOP BAR & CSS
# ══════════════════════════════════════════════════════════════

col1, col2 = st.columns([9, 1])
with col2:
    lm = st.toggle("Light Mode", value=st.session_state.light_mode)
    if lm != st.session_state.light_mode:
        st.session_state.light_mode = lm
        st.rerun()

THEME = THEME_LIGHT if st.session_state.light_mode else THEME_DARK

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

    :root {{
        --primary: {THEME["primary"]};
        --primary-hover: {THEME["primary_hover"]};
        --bg: {THEME["background"]};
        --card-bg: {THEME["card_bg"]};
        --sidebar: {THEME["sidebar"]};
        --ai-bubble: {THEME["ai_bubble"]};
        --text: {THEME["text"]};
        --text-dim: {THEME["text_dim"]};
        --border: {THEME["border"]};
        --shadow: {THEME["shadow"]};
    }}

    .stApp, [data-testid="stAppViewContainer"], header[data-testid="stHeader"] {{
        background-color: var(--bg) !important;
        color: var(--text) !important;
        font-family: 'Inter', sans-serif !important;
    }}

    .glass-card {{
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 14px var(--shadow);
        transition: all 0.2s ease;
    }}

    .chat-bubble {{
        padding: 14px 18px;
        border-radius: 18px;
        margin-bottom: 12px;
        max-width: 85%;
        line-height: 1.6;
        box-shadow: 0 4px 14px var(--shadow);
        font-size: 16px;
    }}

    .user-bubble {{
        background: var(--primary);
        color: white;
        align-self: flex-end;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }}

    .ai-bubble {{
        background: var(--ai-bubble);
        border: 1px solid var(--border);
        color: var(--text);
        align-self: flex-start;
        border-bottom-left-radius: 4px;
    }}

    .memory-item {{
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid var(--border);
        font-size: 14px;
    }}
    .memory-label {{ color: var(--text-dim); font-weight: 600; }}
    .memory-val {{ color: var(--text); }}

    section[data-testid="stSidebar"] {{
        background-color: var(--sidebar) !important;
        border-right: 1px solid var(--border);
    }}
    
    /* Fix the dark block at the bottom for chat input */
    div[data-testid="stBottomBlockContainer"], div[data-testid="stBottom"] {{
        background-color: var(--bg) !important;
    }}

    .stChatInputContainer, div[data-testid="stChatInput"] {{
        border-radius: 24px !important;
        background-color: var(--card-bg) !important;
        border: 1px solid var(--border) !important;
        box-shadow: 0 4px 14px var(--shadow) !important;
    }}
    
    /* Ensure chat input text is visible */
    .stChatInputContainer textarea, div[data-testid="stChatInput"] textarea {{
        color: var(--text) !important;
        background-color: transparent !important;
    }}

    /* Standardize all buttons to fit the theme */
    .stButton > button, 
    div[data-testid="stPopover"] button,
    button[data-testid="baseButton-secondary"], 
    button[data-testid="baseButton-primary"] {{
        background-color: var(--card-bg) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        border-radius: 14px !important;
        transition: all 0.2s ease !important;
    }}
    
    .stButton > button:hover, 
    div[data-testid="stPopover"] button:hover,
    button[data-testid="baseButton-secondary"]:hover, 
    button[data-testid="baseButton-primary"]:hover {{
        border-color: var(--primary) !important;
        color: var(--primary) !important;
        transform: scale(1.02);
    }}

    /* Removed custom toolbar CSS to fix sidebar toggle bug. Will use .streamlit/config.toml instead */
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# 3. API & HELPER LOGIC
# ══════════════════════════════════════════════════════════════

async def call_chat_api(query: str, image_base64: str = None):
    async with httpx.AsyncClient(timeout=60.0) as client:
        payload = {"session_id": st.session_state.session_id, "query": query}
        if image_base64:
            payload["image_base64"] = image_base64
        try:
            response = await client.post(f"{API_BASE_URL}/chat", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Error connecting to backend: {str(e)}")
            return None

def fetch_sessions():
    try:
        res = requests.get(f"{API_BASE_URL}/sessions", timeout=2)
        if res.status_code == 200:
            return res.json().get("sessions", [])
    except:
        pass
    return []

def load_session(sid):
    try:
        res = requests.get(f"{API_BASE_URL}/session/{sid}/history", timeout=2)
        if res.status_code == 200:
            data = res.json()
            st.session_state.messages = [{"role": m["role"], "content": m["content"]} for m in data.get("history", [])]
            st.session_state.memory_state = data.get("memory", {})
            st.session_state.session_id = sid
    except:
        pass

def delete_session(sid):
    try:
        requests.delete(f"{API_BASE_URL}/session/{sid}", timeout=2)
        if st.session_state.session_id == sid:
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.session_state.memory_state = {}
    except:
        pass

# ══════════════════════════════════════════════════════════════
# 4. SIDEBAR
# ══════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown(f"<h1 style='color: var(--text); margin-bottom: 0;'>🛡️ {APP_TITLE}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: var(--text-dim); font-size: 0.9rem;'>{APP_SUBTITLE}</p>", unsafe_allow_html=True)
    
    st.markdown("### 🧠 Current Memory State")
    st.markdown("<div style='background: rgba(128,128,128,0.1); padding: 15px; border-radius: 12px; border: 1px solid rgba(128,128,128,0.2); margin-bottom: 20px;'>", unsafe_allow_html=True)
    
    mem = st.session_state.memory_state
    keys_to_show = ["property_type", "damage_type", "postcode", "policy_tier", "claim_id"]
    for k in keys_to_show:
        val = mem.get(k)
        disp_val = val if val else "—"
        st.markdown(f"""
        <div class='memory-item'>
            <span class='memory-label'>{k.replace('_', ' ').title()}</span>
            <span class='memory-val'>{disp_val}</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("🆕 New Session", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.memory_state = {}
        st.rerun()

    # Saved Sessions Logic
    sessions = fetch_sessions()
    if sessions:
        st.markdown("### 💾 Saved Sessions")
        for s in sessions[:5]: # show top 5
            sid = s["session_id"]
            preview = s.get("preview", "Session")
            c1, c2 = st.columns([8, 2])
            with c1:
                if st.button(f"{preview}", key=f"load_{sid}", use_container_width=True):
                    load_session(sid)
                    st.rerun()
            with c2:
                if st.button("🗑️", key=f"del_{sid}"):
                    delete_session(sid)
                    st.rerun()



    st.markdown("---")
    st.markdown(f"""
        <a href="{API_BASE_URL}/dev-console" target="_blank" style="text-decoration: none;">
            <button style="width: 100%; background: linear-gradient(135deg, {THEME['primary']}, #BE123C); color: white; padding: 10px; border-radius: 8px; border: none; cursor: pointer; font-weight: 600; box-shadow: 0 4px 14px 0 rgba(225, 29, 72, 0.39);">
                🚀 Developer Console
            </button>
        </a>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# 5. MAIN CONTENT
# ══════════════════════════════════════════════════════════════

st.markdown(f"""
<div class='glass-card'>
    <h2 style='margin-top: 0; color: var(--text);'>Welcome to {APP_TITLE}</h2>
    <p style='color: var(--text-dim);'>I can help you understand your coverage, estimate repair costs, find approved contractors, and track claims. I'll remember the details you share with me.</p>
</div>
""", unsafe_allow_html=True)

with st.popover("💡 Frequent Questions"):
    for q in EXAMPLE_QUERIES:
        if st.button(q, key=f"fq_{q}", use_container_width=True):
            st.session_state.pending_query = q
            st.rerun()

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='chat-bubble user-bubble'>{msg['content']}</div>", unsafe_allow_html=True)
        if "image" in msg:
            st.image(msg["image"], width=300)
    else:
        intent = msg.get("intent", "POLICY_Q_A")
        meta = INTENT_METADATA.get(intent, {"color": "gray", "icon": "⚡"})
        st.markdown(f"""
        <div class='chat-bubble ai-bubble'>
            <div style='font-size: 0.75rem; font-weight: 600; padding: 4px 10px; border-radius: 12px; margin-bottom: 10px; display: inline-block; background: {meta["color"]}; color: white;'>
                {meta["icon"]} {intent.replace("_", " ")}
            </div>
            <div style='margin-bottom: 10px;'>{msg["content"]}</div>
        </div>
        """, unsafe_allow_html=True)

prompt = st.chat_input("Ask about your coverage or claim...", accept_file=True, file_type=["jpg", "jpeg", "png"])

query = None
uploaded_file = None

if "pending_query" in st.session_state:
    query = st.session_state.pending_query
    del st.session_state.pending_query

if prompt:
    if isinstance(prompt, str):
        query = prompt
    else:
        query = prompt.text
        if getattr(prompt, "files", None):
            uploaded_file = prompt.files[0]
            if not query:
                query = "Analyze this image for damage."

if query:
    image_b64 = None
    msg_dict = {"role": "user", "content": query}
    
    if uploaded_file:
        bytes_data = uploaded_file.getvalue()
        image_b64 = base64.b64encode(bytes_data).decode()
        msg_dict["image"] = bytes_data
        
    st.session_state.messages.append(msg_dict)
    
    with st.status("🧠 Processing...", expanded=True) as status:
        result = asyncio.run(call_chat_api(query, image_base64=image_b64))
        if result:
            status.update(label="✅ Answer found!", state="complete", expanded=False)
            ai_message = {
                "role": "ai", "content": result["answer"],
                "intent": result["intent"], "steps_log": result["steps_log"]
            }
            st.session_state.messages.append(ai_message)
            st.session_state.memory_state = result.get("memory", {})
            st.rerun()
        else:
            status.update(label="❌ Error generating answer", state="error")
