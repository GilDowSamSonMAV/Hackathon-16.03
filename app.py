import streamlit as st
from classifier import classify
from responder import respond
from alerter import create_alert, create_medical_summary
from config import PATIENT_NAME, PATIENT_ID

# ─── Page Config ───
st.set_page_config(
    page_title="Savta — Smart Check-in",
    page_icon="🫶",
    layout="wide",
)

# ─── Custom CSS ───
st.markdown("""
<style>
    /* RTL support */
    .rtl { direction: rtl; text-align: right; font-size: 1.1rem; line-height: 1.8; }

    /* Badge styles */
    .badge-green {
        display: inline-block; padding: 2px 12px; border-radius: 12px;
        background: #25D366; color: #000; font-weight: 700; font-size: 0.8rem; margin-bottom: 4px;
    }
    .badge-yellow {
        display: inline-block; padding: 2px 12px; border-radius: 12px;
        background: #FFD600; color: #000; font-weight: 700; font-size: 0.8rem; margin-bottom: 4px;
    }
    .badge-red {
        display: inline-block; padding: 2px 12px; border-radius: 12px;
        background: #FF3B30; color: #FFF; font-weight: 700; font-size: 0.8rem; margin-bottom: 4px;
    }

    /* Alert log styles */
    .alert-entry { padding: 10px; border-radius: 8px; margin-bottom: 8px; direction: rtl; text-align: right; }
    .alert-green { background: rgba(37,211,102,0.15); border-left: 4px solid #25D366; }
    .alert-yellow { background: rgba(255,214,0,0.15); border-left: 4px solid #FFD600; }
    .alert-red { background: rgba(255,59,48,0.15); border-left: 4px solid #FF3B30; }

    /* Chat area */
    .stChatMessage { max-width: 85%; }
    [data-testid="stSidebar"] { direction: rtl; }

    /* Header */
    .main-header {
        text-align: center; padding: 10px 0 20px 0;
        border-bottom: 1px solid rgba(250,250,250,0.1); margin-bottom: 20px;
    }
    .main-header h1 { margin: 0; font-size: 2rem; }
    .main-header p { margin: 4px 0 0 0; opacity: 0.7; font-size: 0.95rem; }
</style>
""", unsafe_allow_html=True)

# ─── Session State ───
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "alert_log" not in st.session_state:
    st.session_state.alert_log = []

# ─── Layout: Chat (left) + Alerts (right) ───
chat_col, alert_col = st.columns([7, 3])

# ─── Right Column: Alert Log ───
with alert_col:
    st.markdown("### 🚨 יומן התראות משפחה")
    st.caption(f"מטופל/ת: {PATIENT_NAME} ({PATIENT_ID})")
    st.divider()

    if not st.session_state.alert_log:
        st.info("אין התראות עדיין — הכל תקין 💚")
    else:
        for alert in reversed(st.session_state.alert_log):
            level = alert["alert_level"]
            emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}[level]
            css_class = f"alert-{level}"

            st.markdown(f"""
            <div class="alert-entry {css_class}">
                <strong>{emoji} {alert['timestamp']}</strong><br>
                <span style="font-size:0.9rem;">{alert['message_snippet']}</span><br>
                <span style="font-size:0.85rem; opacity:0.8;">📋 {alert['recommended_action']}</span>
            </div>
            """, unsafe_allow_html=True)

            if level == "red" and "medical_summary" in alert:
                with st.expander("📄 סיכום רפואי (JSON)"):
                    st.json(alert["medical_summary"])

# ─── Left Column: Chat Interface ───
with chat_col:
    st.markdown("""
    <div class="main-header">
        <h1>🫶 Savta — סבתא</h1>
        <p>מערכת צ'ק-אין חכמה למבוגרים</p>
    </div>
    """, unsafe_allow_html=True)

    # Display chat history
    for entry in st.session_state.chat_history:
        if entry["role"] == "user":
            with st.chat_message("user"):
                st.markdown(f'<div class="rtl">{entry["content"]}</div>', unsafe_allow_html=True)
        else:
            with st.chat_message("assistant", avatar="🫶"):
                level = entry.get("level", "green")
                badge_label = {"green": "🟢 ירוק", "yellow": "🟡 צהוב", "red": "🔴 אדום"}[level]
                st.markdown(f'<span class="badge-{level}">{badge_label}</span>', unsafe_allow_html=True)
                st.markdown(f'<div class="rtl">{entry["content"]}</div>', unsafe_allow_html=True)

    # Chat input
    if user_input := st.chat_input("הקלידו הודעה כאן..."):
        # Show user message immediately
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(f'<div class="rtl">{user_input}</div>', unsafe_allow_html=True)

        # Process
        with st.chat_message("assistant", avatar="🫶"):
            with st.spinner("מעבד... 🔄"):
                classification = classify(user_input)
                bot_reply = respond(user_input, classification)

            level = classification.get("level", "green")
            badge_label = {"green": "🟢 GREEN", "yellow": "🟡 YELLOW", "red": "🔴 RED"}[level]
            st.markdown(f'<span class="badge-{level}">{badge_label}</span>', unsafe_allow_html=True)
            st.markdown(f'<div class="rtl">{bot_reply}</div>', unsafe_allow_html=True)

        # Save to history
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": bot_reply,
            "level": level,
        })

        # Alert if yellow/red
        if level in ("yellow", "red"):
            alert = create_alert(user_input, classification)
            if level == "red":
                with st.spinner("מכין סיכום רפואי..."):
                    alert["medical_summary"] = create_medical_summary(user_input, classification)
            st.session_state.alert_log.append(alert)

        st.rerun()
