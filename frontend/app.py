import streamlit as st
import requests
import pandas as pd

# --- 1. THE ULTIMATE MINIMALIST CSS ---
st.markdown("""
<style>
    /* Apple System Fonts */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Helvetica Neue", sans-serif;
    }

    /* Floating Mode Toggle (Bottom Left) */
    .floating-toggle {
        position: fixed;
        bottom: 30px;
        left: 30px;
        width: 50px;
        height: 50px;
        background: transparent;
        border: 1px solid rgba(128, 128, 128, 0.3);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        z-index: 999999;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        color: inherit;
    }

    .floating-toggle:hover {
        transform: scale(1.15) rotate(15deg);
        border-color: #3b82f6;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }

    /* Clean Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: transparent !important;
        border-right: 1px solid rgba(128, 128, 128, 0.1);
    }

    /* Hide the ugly standard Streamlit button we use for the logic */
    #hidden_logic_btn {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. STATE & THEME LOGIC ---
if 'theme' not in st.session_state:
    st.session_state.theme = "light"

# --- 3. THE FLOATING BUTTON (VISUAL) ---
sun_svg = '<svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="1.5" fill="none"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>'
moon_svg = '<svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="1.5" fill="none"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>'

icon = sun_svg if st.session_state.theme == "light" else moon_svg

# This creates the clickable circle in the bottom left
st.markdown(f'''
    <div class="floating-toggle" id="mode-trigger">
        {icon}
    </div>
    <script>
        const trigger = window.parent.document.getElementById('mode-trigger');
        // Find the invisible streamlit button by its text content
        const btn = window.parent.document.querySelectorAll('button');
        trigger.onclick = () => {{
            for (let b of btn) {{
                if (b.innerText === "LOGIC_TICK") b.click();
            }}
        }};
    </script>
''', unsafe_allow_html=True)

# The invisible logic driver
if st.button("LOGIC_TICK", key="hidden_logic_btn"):
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
    # Note: Streamlit standard themes (dark/light) are still controlled by the system 
    # unless you change it in Settings -> Theme -> Light/Dark.
    st.rerun()

# --- 4. THE CLEAN SIDEBAR ---
with st.sidebar:
    st.markdown("### Settings")
    patient_id = st.text_input("Patient ID", value="PT-001")
    st.divider()
    st.caption("Minimalist Clinical Pipeline v2.0")

# --- 5. MAIN UI ---
st.title("Clinical AI Hub")
st.markdown("---")

# Navigation
col1, col2 = st.columns(2)
view = col1.button("Run ETL", use_container_width=True)
view2 = col2.button("Mining Stats", use_container_width=True)

# Your existing logic for Mining or Extraction goes here...
# (Just as we had it before, but inside this cleaner layout)

note_text = st.chat_input("Enter clinical note...")
if note_text:
    st.write(f"Processing note for: {patient_id}")