import streamlit as st
import requests
import time
import base64
import datetime
import textwrap
import json

# Define Indian Standard Time (UTC+5:30)
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
# =========================
# CONFIGURATION
# =========================
BACKEND_URL = "https://sales-chatbot-7wsa.onrender.com"   # Your FastAPI URL
EMPLOYEE_ID = "EMP001"                   # Replace with real login later

# ── helpers ──────────────────────────────────────────────────────────────────

def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""

def init_backend():
    """Warm up backend by hitting the root endpoint."""
    try:
        requests.get(f"{BACKEND_URL}/", timeout=5)
    except Exception:
        pass

def send_message(query: str) -> dict:
    """
    POST /chat to FastAPI.
    Automatically sends session_id on follow-up messages.
    Returns full response dict.
    """
    payload = {
        "employee_id": EMPLOYEE_ID,
        "query"      : query,
        "session_id" : st.session_state.get("session_id")  # None on first message
    }
    try:
        response = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=None)
        response.raise_for_status()
        data = response.json()

        # Save session_id after first message — reused for all follow-ups
        if not st.session_state.get("session_id"):
            st.session_state.session_id = data.get("session_id")

        return data

    except Exception as e:
        return {"answer": f"Error connecting to server: {e}", "db_sources": [], "internet_sources": [], "message_id": None}

def rate_message(message_id: str, rating: str):
    """PATCH /chat/{message_id}/rate"""
    if not message_id or message_id == "None":
        return
    try:
        requests.patch(
            f"{BACKEND_URL}/chat/{message_id}/rate",
            json={"rating": rating},
            timeout=10
        )
    except Exception:
        pass

# ── Google Fonts + global CSS ─────────────────────────────────────────────────

GLOBAL_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

/* ── reset Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
.stApp { background: transparent !important; }

/* ── CSS variables ── */
:root {
    --navy:   #0A0F1E;
    --navy2:  #111827;
    --accent: #63B3ED;
    --accent2:#3B82F6;
    --text:   #E8F4FF;
    --muted:  #94A3B8;
    --green:  #4CAF7D;
    --red:    #EF5350;
    --bubble-bot: #FFFFFF;
    --bubble-user:#111827;
    --bg-page:#F0F2F8;
    --border: rgba(0,0,0,0.08);
    --font-serif: 'Cormorant Garamond', Georgia, serif;
    --font-sans:  'DM Sans', system-ui, sans-serif;
}

body { font-family: var(--font-sans); }
"""

SCRIPTS = """
<script>
function copyMsg(text) {
    navigator.clipboard.writeText(text).then(function(){ 
        var t = document.createElement('div');
        t.style = "position:fixed;bottom:90px;left:50%;transform:translateX(-50%);background:#111827;color:white;padding:8px 18px;border-radius:20px;z-index:999;font-size:.75rem;";
        t.textContent = 'Copied ✓';
        document.body.appendChild(t);
        setTimeout(function(){ t.remove(); }, 2000);
    });
}
function sendChip(text) {
    var inp = parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]') || document.querySelector('textarea');
    if (!inp) return;
    var setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
    setter.call(inp, text);
    inp.dispatchEvent(new Event('input', { bubbles: true }));
    setTimeout(function(){
        var form = inp.closest('form');
        var btn = form ? form.querySelector('button[type="submit"]') : inp.parentElement.querySelector('button');
        if (btn) btn.click();
    }, 80);
}
</script>
"""

# ── Loading Screen CSS ────────────────────────────────────────────────────────

LOADING_CSS = """
<style>
""" + GLOBAL_CSS + """

.stApp { background: var(--navy) !important; }

.bg-grid {
    position: fixed; inset: 0;
    background-image:
        linear-gradient(rgba(99,179,237,0.045) 1px, transparent 1px),
        linear-gradient(90deg, rgba(99,179,237,0.045) 1px, transparent 1px);
    background-size: 30px 30px;
    pointer-events: none; z-index: 0;
}
.bg-glow {
    position: fixed; width: 560px; height: 560px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(56,182,255,0.11) 0%, transparent 68%);
    top: 50%; left: 50%; transform: translate(-50%, -54%);
    pointer-events: none; z-index: 0;
    animation: pulse-glow 3.5s ease-in-out infinite;
}
@keyframes pulse-glow {
    0%,100% { opacity:.6; transform:translate(-50%,-54%) scale(1);   }
    50%      { opacity:1;  transform:translate(-50%,-54%) scale(1.12);}
}
.loading-wrapper {
    position: fixed; inset: 0;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center; z-index: 10;
}
.logo-ring {
    width: 88px; height: 88px; border-radius: 50%;
    border: 1.5px solid rgba(99,179,237,0.35);
    display: flex; align-items: center; justify-content: center;
    position: relative; margin-bottom: 34px;
    animation: spin-cw 9s linear infinite;
}
.logo-ring::before {
    content: ''; position: absolute;
    width: 10px; height: 10px; border-radius: 50%;
    background: var(--accent); top: -5px; left: 50%;
    transform: translateX(-50%); box-shadow: 0 0 12px var(--accent);
}
.logo-inner {
    width: 58px; height: 58px; border-radius: 50%;
    background: rgba(99,179,237,0.08);
    border: 1px solid rgba(99,179,237,0.22);
    display: flex; align-items: center; justify-content: center;
    font-size: 24px; animation: spin-cw 9s linear infinite reverse;
}
@keyframes spin-cw { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.loading-name {
    font-family: var(--font-serif); font-size: 3.4rem; font-weight: 600;
    color: var(--text); letter-spacing: .06em; text-align: center;
    opacity: 0; transform: translateY(18px);
    animation: fade-up 1s ease .2s forwards;
}
.loading-tag {
    font-family: var(--font-sans); font-size: .72rem; font-weight: 300;
    letter-spacing: .22em; text-transform: uppercase; color: var(--accent);
    margin-top: 10px; text-align: center;
    opacity: 0; animation: fade-up 1s ease .55s forwards;
}
.dot-row { display: flex; gap: 7px; margin-top: 28px; justify-content: center; }
.dot-row span {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--accent); opacity: .3;
    animation: dot-p 1.4s ease-in-out infinite;
}
.dot-row span:nth-child(2) { animation-delay:.2s; }
.dot-row span:nth-child(3) { animation-delay:.4s; }
@keyframes dot-p {
    0%,100% { opacity:.3; transform:scale(1);   }
    50%      { opacity:1;  transform:scale(1.45);}
}
@keyframes fade-up { to { opacity:1; transform:translateY(0); } }
</style>
"""

# ── Chat Screen CSS ───────────────────────────────────────────────────────────

CHAT_CSS = """
<style>
""" + GLOBAL_CSS + """

.stApp { 
    background: linear-gradient(135deg, #F0F2F8 0%, #E2E8F0 100%) !important; 
}

.sa-header {
    background: var(--navy); padding: 14px 28px;
    display: flex; align-items: center; justify-content: space-between;
    position: sticky; top: 0; z-index: 100;
}
.sa-header-left { display:flex;align-items:center;gap:14px; }
.sa-header-actions { display:flex;gap:8px; }
.sa-pill {
    font-family: var(--font-sans); font-size: .68rem; padding: 5px 12px;
    border-radius: 20px; background: rgba(99,179,237,0.1);
    border: .5px solid rgba(99,179,237,0.22); color: var(--accent);
    cursor: pointer; transition: background .18s, transform .12s; user-select: none;
}
.sa-pill:hover { background: rgba(99,179,237,0.18); transform: translateY(-1px); }
.sa-avatar {
    width: 40px; height: 40px; border-radius: 50%;
    background: rgba(99,179,237,0.12);
    border: 1px solid rgba(99,179,237,0.28);
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; flex-shrink: 0;
}
.sa-header-name {
    font-family: var(--font-serif); font-size: 1.35rem;
    font-weight: 600; color: var(--text); letter-spacing: .04em;
}
.sa-status {
    font-family: var(--font-sans); font-size: .7rem;
    font-weight: 300; color: var(--green);
    display: flex; align-items: center; gap: 5px; margin-top: 2px;
}
.sa-status-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--green); animation: dot-p 2s ease-in-out infinite;
}
.chat-area { 
    max-width: 780px; 
    margin: 0 auto; 
    padding: 28px 20px 100px;
    backdrop-filter: blur(10px);
}

.msg-row-bot {
    display: flex; gap: 10px; align-items: flex-end;
    margin-bottom: 6px; animation: slide-left .3s ease;
}
.msg-row-user {
    display: flex; justify-content: flex-end;
    margin-bottom: 6px; animation: slide-right .3s ease;
}
@keyframes slide-left  { from { opacity:0; transform:translateX(-12px);} to {opacity:1;transform:translateX(0);}}
@keyframes slide-right { from { opacity:0; transform:translateX(12px); } to {opacity:1;transform:translateX(0);}}

/* TYPING INDICATOR */
.typing-bubble { display:flex;gap:10px;align-items:flex-end;margin-bottom:6px;animation:slide-left .3s ease; }
.typing-dots { background:var(--bubble-bot);border:.5px solid var(--border);border-radius:18px 18px 18px 4px;padding:14px 18px;display:flex;align-items:center;gap:5px; }
.typing-dots span { width:7px;height:7px;border-radius:50%;background:var(--muted);display:inline-block;animation:typing-bounce 1.2s ease-in-out infinite; }
.typing-dots span:nth-child(2){animation-delay:.18s;}.typing-dots span:nth-child(3){animation-delay:.36s;}
@keyframes typing-bounce { 0%,60%,100%{transform:translateY(0);opacity:.4}30%{transform:translateY(-6px);opacity:1} }

.bot-mini-avatar {
    width: 30px; height: 30px; border-radius: 50%;
    background: var(--navy); border: 1px solid rgba(99,179,237,0.28);
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; flex-shrink: 0;
}
.bubble-bot-wrap { max-width: 72%; }
.bubble-bot {
    background: var(--bubble-bot); border: .5px solid var(--border);
    border-radius: 18px 18px 18px 4px; padding: 12px 16px;
    font-family: var(--font-sans); font-size: .88rem;
    line-height: 1.65; color: #1A2035;
}
.bubble-user {
    background: var(--navy); border-radius: 18px 18px 4px 18px;
    padding: 12px 16px; font-family: var(--font-sans);
    font-size: .88rem; line-height: 1.65; color: var(--text); max-width: 72%;
}
.bubble-meta {
    display: flex; align-items: center; justify-content: space-between;
    margin-top: 5px; padding: 0 2px;
}
.bubble-time { font-family: var(--font-sans); font-size: .65rem; color: var(--muted); }

/* SOURCES SECTION */
.sources-section { margin-top:10px; }
.sources-toggle { font-family:var(--font-sans);font-size:.75rem;font-weight:500;color:var(--accent2);cursor:pointer;display:flex;align-items:center;gap:5px;user-select:none;margin-bottom:6px;list-style:none; }
.source-card { background:#FFFFFF;border:.5px solid rgba(0,0,0,0.07);border-radius:10px;padding:8px 12px;margin-bottom:5px;display:flex;align-items:flex-start;gap:9px;text-decoration:none;transition:border-color .15s,transform .15s; }
.source-card:hover { border-color:rgba(59,130,246,0.3);transform:translateX(2px); }
.source-icon { font-size:14px;flex-shrink:0;margin-top:1px; }
.source-title { font-family:var(--font-sans);font-size:.72rem;font-weight:500;color:#1A2035;line-height:1.3; }
.source-sub { font-family:var(--font-sans);font-size:.63rem;color:var(--muted);margin-top:1px; }

/* CHIPS */
.chips-row { display:flex;flex-wrap:wrap;gap:6px;margin:14px 0 6px 40px;animation:slide-left .4s ease .1s both; }
.chip { font-family:var(--font-sans);font-size:.7rem;padding:5px 12px;border-radius:20px;background:white;border:.5px solid rgba(59,130,246,0.25);color:var(--accent2);cursor:pointer;transition:background .15s,transform .12s;white-space:nowrap; }
.chip:hover { background:#EFF6FF;border-color:var(--accent2);transform:translateY(-1px); }

.stChatInput > div {
    border-radius: 28px !important;
    border: 1px solid rgba(10,15,30,0.15) !important;
    background: white !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important;
    font-family: var(--font-sans) !important;
}
</style>
"""

# ── page config ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="Sales Assistant", page_icon="◈", layout="centered")

# ── session defaults ──────────────────────────────────────────────────────────

if "initialized"  not in st.session_state: st.session_state.initialized  = False
if "messages"     not in st.session_state: st.session_state.messages     = []
if "ratings"      not in st.session_state: st.session_state.ratings      = {}
if "session_id"   not in st.session_state: st.session_state.session_id   = None  # ← FastAPI session
if "message_ids"  not in st.session_state: st.session_state.message_ids  = {}    # {msg_index: message_id}

# ── RENDER SCRIPTS ──
st.markdown(SCRIPTS, unsafe_allow_html=True)

# ── LOADING SCREEN ────────────────────────────────────────────────────────────

if not st.session_state.initialized:
    st.markdown(LOADING_CSS, unsafe_allow_html=True)

    placeholder      = st.empty()
    type_placeholder = st.empty()

    with placeholder.container():
        st.markdown("""
        <div class="bg-grid"></div>
        <div class="bg-glow"></div>
        <div class="loading-wrapper">
            <div class="logo-ring"><div class="logo-inner">◈</div></div>
            <div class="loading-name">SalesAssist</div>
            <div class="loading-tag">Your intelligent sales companion</div>
        </div>
        """, unsafe_allow_html=True)

    time.sleep(1.0)

    sentence = "Connecting to your assistant..."
    typed = ""
    for char in sentence:
        typed += char
        type_placeholder.markdown(
            f'<div style="position:fixed;top:62%;left:0;width:100vw;text-align:center;'
            f'font-family:\'DM Sans\',sans-serif;font-size:.98rem;font-weight:300;'
            f'color:#94A3B8;letter-spacing:.02em;z-index:20;">{typed}▍</div>',
            unsafe_allow_html=True,
        )
        time.sleep(0.055)

    time.sleep(0.5)

    with st.spinner(""):
        init_backend()

    st.session_state.initialized = True
    placeholder.empty()
    type_placeholder.empty()
    st.rerun()

# ── CHAT SCREEN ───────────────────────────────────────────────────────────────

if st.session_state.initialized:

    st.markdown(CHAT_CSS, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="sa-header">
        <div class="sa-header-left">
            <div class="sa-avatar">◈</div>
            <div>
                <div class="sa-header-name">SalesAssist</div>
                <div class="sa-status">
                    <div class="sa-status-dot"></div>
                    Online &middot; Ready to help
                </div>
            </div>
        </div>
        <div class="sa-header-actions">
            <div class="sa-pill" onclick="window.location.reload()">+ New topic</div>
            <div class="sa-pill" onclick="copyMsg(document.querySelector('.bubble-bot')?.innerText||'')">&#x2197; Copy last</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="chat-area">', unsafe_allow_html=True)

    for i, msg in enumerate(st.session_state.messages):
        ts      = msg.get("time", "")
        role    = msg["role"]
        content = msg["content"]

        if role == "assistant":
            rating = st.session_state.ratings.get(i)
            db_sources = msg.get("db_sources", [])
            internet_sources = msg.get("internet_sources", [])
            
            # Build source cards
            source_cards_html = """"""
            if db_sources or internet_sources:
                cards = """"""
                for src_item in db_sources:
                    cards += f'<div class="source-card"><div class="source-icon">&#128196;</div><div><div class="source-title">{src_item}</div><div class="source-sub">Internal knowledge base</div></div></div>'
                for src_item in internet_sources:
                    stitle = src_item.get("title", "Web source")
                    surl   = src_item.get("url", "#")
                    short_url = surl[:45] + ("..." if len(surl) > 45 else "")
                    cards += f'<a class="source-card" href="{surl}" target="_blank"><div class="source-icon">&#127760;</div><div><div class="source-title">{stitle}</div><div class="source-sub">{short_url}</div></div></a>'
                count = len(db_sources) + len(internet_sources)
                source_cards_html = f'<details class="sources-section"><summary class="sources-toggle">◈ View Sources ({count})</summary><div style="margin-top:6px">{cards}</div></details>'

            bot_bubble_html = f"""
<div class="msg-row-bot">
<div class="bot-mini-avatar">◈</div>
<div class="bubble-bot-wrap">
<div class="bubble-bot">{content}</div>
{source_cards_html}
<div class="bubble-meta">
<span class="bubble-time">{ts}</span>
</div>
</div>
</div>"""
            st.markdown(bot_bubble_html, unsafe_allow_html=True)

            # Rating buttons
            col_gap, col_label, col_up, col_dn, col_rest = st.columns([4, 2, 0.45, 0.45, 3])
            with col_label:
                st.markdown('<div style="font-family:\'DM Sans\';font-size:.7rem;color:#94A3B8;margin-top:7px;text-align:right;">Was this helpful?</div>', unsafe_allow_html=True)
            with col_up:
                up_type = "primary" if rating == "yes" else "secondary"
                if st.button("👍", key=f"up_{i}", type=up_type):
                    st.session_state.ratings[i] = "yes"
                    rate_message(st.session_state.message_ids.get(i), "yes")
                    st.rerun()
            with col_dn:
                dn_type = "primary" if rating == "no" else "secondary"
                if st.button("👎", key=f"dn_{i}", type=dn_type):
                    st.session_state.ratings[i] = "no"
                    rate_message(st.session_state.message_ids.get(i), "no")
                    st.rerun()

            # Suggested chips after last bot message
            if i == len(st.session_state.messages) - 1:
                CHIP_LABELS = ["Show pricing breakdown", "Compare with competitor", "Draft a follow-up email", "Summarise key benefits"]
                chips_markup = "".join(f'<div class="chip" onclick="sendChip(\'{c}\')">{c}</div>' for c in CHIP_LABELS)
                st.markdown(f'<div class="chips-row">{chips_markup}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="msg-row-user">
                <div class="bubble-user">{content}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ── Input ──
if prompt := st.chat_input("Ask me anything..."):
    now_ist = datetime.datetime.now(IST).strftime("%I:%M %p") # Use IST
    st.session_state.messages.append({
        "role": "user", "content": prompt, "time": now_ist,
    })
    st.rerun()

# ── Generate response after rerun ────────────────────────────────────────────

if st.session_state.initialized and len(st.session_state.messages) > 0:
    last_msg = st.session_state.messages[-1]

    if last_msg["role"] == "user":
        typing_ph = st.empty()
        with typing_ph:
            st.markdown('<div class="chat-area" style="padding-top:0;padding-bottom:0;"><div class="typing-bubble"><div class="bot-mini-avatar">◈</div><div class="typing-dots"><span></span><span></span><span></span></div></div></div>', unsafe_allow_html=True)
        
        data = send_message(last_msg["content"])
        typing_ph.empty()

        answer           = data.get("answer", "Sorry, something went wrong.")
        db_sources       = data.get("db_sources", [])
        internet_sources = data.get("internet_sources", [])
        message_id       = data.get("message_id")

        idx = len(st.session_state.messages)

        st.session_state.messages.append({
            "role"            : "assistant",
            "content"         : answer,
            "time"            : datetime.datetime.now(IST).strftime("%I:%M %p"),
            "db_sources"      : db_sources,
            "internet_sources": internet_sources,
            "message_id"      : message_id,
        })

        # Store message_id so rating buttons can call /rate endpoint
        st.session_state.message_ids[idx] = message_id
        st.session_state.ratings[idx]     = None
        st.rerun()
        st.session_state.messages.append({
            "content"         : answer,
            "time"            : datetime.datetime.now(IST).strftime("%I:%M %p"),
            "db_sources"      : db_sources,
            "internet_sources": internet_sources,
        })

        # Store message_id so rating buttons can call /rate endpoint
        st.session_state.message_ids[idx] = message_id
        st.session_state.ratings[idx]     = None
        st.rerun()
