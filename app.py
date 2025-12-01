# ---------> Libraries <----------------- #
from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import streamlit as st

from carbon_check import carbon_check_page
from waste_scanner import waste_scanner_page

try:
    import ollama
    HAS_LLM = True
except Exception:
    ollama = None
    HAS_LLM = False
# ---------------------------------------------- #

# --> Configuration Loading <-- #
CONFIG_PATH = Path(__file__).with_name("appjson.json")

def load_config() -> Dict[str, Any]:
    """Load the JSON configuration."""
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"[GreenGuard AI] Configuration error: {exc}")
    return {}

CONFIG = load_config()
C = {
    "PAGE_TITLE": CONFIG.get("pageconfig", {}).get("Title"),
    "PAGE_ICON": CONFIG.get("pageconfig", {}).get("Icon"),
    "PAGE_LAYOUT": CONFIG.get("pageconfig", {}).get("Layout"),
    "SIDEBAR_STATE": CONFIG.get("pageconfig", {}).get("SidebarState"),
    "OLLAMA_MODEL": CONFIG.get("ollama", {}).get("OllamaModel"),
    "SYSTEM_PROMPT": CONFIG.get("ollama", {}).get("OllamaPrompt"),
    "TIPS": CONFIG.get("tips", []),
    "AI_CONFIG": CONFIG.get("AI", {}),
    "TEXT_CONFIG": CONFIG.get("text", {}),
    "STYLE_CSS": CONFIG.get("style", {}).get("StyleCss"),
}

# --- General Helper Functions ---

def _nav_to(page: str) -> None:
    """Navigate to a new page state and trigger a rerun."""
    st.session_state["page"] = page
    st.rerun()

def _back_button() -> None:
    """Renders the back-to-home button for tool pages."""
    back_text = C["TEXT_CONFIG"].get("Navigation", {}).get("BackToHome")
    if st.button(back_text, key="back_to_home"):
        _nav_to("home")

# --- Streamlit Core Functions ---

def apply_global_style() -> None:
    """Applies the global CSS style from the config."""
    if C["STYLE_CSS"]:
        st.markdown(C["STYLE_CSS"], unsafe_allow_html=True)


def init_session_state() -> None:
    """Initializes all necessary session state variables."""
    st.session_state.setdefault("page", "home")
    st.session_state.setdefault("chat_history", [])
    st.session_state.setdefault("daily_tip", None)
    if HAS_LLM and "ollama_client" not in st.session_state:
        st.session_state["ollama_client"] = ollama


def ensure_daily_tip() -> None:
    """Selects and stores the daily tip based on the current day."""
    if st.session_state.daily_tip is not None or not C["TIPS"]:
        return
    
    index = datetime.utcnow().timetuple().tm_yday % len(C["TIPS"])
    st.session_state.daily_tip = C["TIPS"][index]


def call_llm(user_text: str) -> str:
    """Calls the Ollama chat endpoint to get an AI response."""
    if not HAS_LLM or "ollama_client" not in st.session_state:
        return (
            "Ollama is not available. Please ensure the service is running and "
            f"the `{C['OLLAMA_MODEL']}` model is pulled."
        )

    thinking_msg = C["AI_CONFIG"].get("ThinkingMessage", "Thinking...")
    messages = [{"role": "system", "content": C["SYSTEM_PROMPT"]}]
    
    for msg in st.session_state.chat_history:
        if msg["text"] == thinking_msg:
            continue
        role = "assistant" if msg["who"] == "ai" else "user"
        messages.append({"role": role, "content": msg["text"]})

    messages.append({"role": "user", "content": user_text})

    try:
        resp = st.session_state.ollama_client.chat(
            model=C["OLLAMA_MODEL"],
            messages=messages,
            stream=False,
        )
        return resp.get("message", {}).get("content", "").strip() or (
            "I couldn't generate a response this time. Please try asking in a different way."
        )
    except Exception as exc:
        return f"Error calling model: {exc}"


def process_pending_ai_response() -> None:
    """Checks for a 'Thinking...' message and replaces it with the LLM response."""
    history = st.session_state.chat_history
    if len(history) < 2:
        return
        
    thinking_msg = C["AI_CONFIG"].get("ThinkingMessage", "Thinking...")
    last = history[-1]
    
    if last.get("who") != "ai" or last.get("text") != thinking_msg:
        return
        
    user_input = history[-2]["text"]
    last["text"] = call_llm(user_input)
    st.rerun()

# ------> Page rendering functions starting from here <----------- #
def _render_card(config_key: str, nav_key: str, page_name: str) -> None:
    """Helper to render a feature card and its navigation button."""
    tool_config = C["TEXT_CONFIG"].get("Tools", {}).get(config_key, {})
    
    st.markdown(
        f"""
        <div class='feature-card'>
            <div class='feature-title'>{tool_config.get("Title", "")}</div>
            <div class='feature-desc'>
                {tool_config.get("Description", "")}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button(tool_config.get("StartButton", "Start"), key=nav_key, use_container_width=True):
        _nav_to(page_name)

def render_feature_cards() -> None:
    """Renders the main page feature cards."""
    col1, col2 = st.columns(2, gap="large")

    with col1:
        _render_card("CarbonCheck", "start_carbon", "carbon_check")

    with col2:
        _render_card("WasteScanner", "open_waste", "waste_scanner")


def render_tip_card() -> None:
    """Renders the daily eco tip card."""
    ensure_daily_tip()
    tip_prefix = C["TEXT_CONFIG"].get("DailyTipPrefix", "Tip:")
    st.markdown(
        f"<div class='tip-card'>{tip_prefix}<br><em>{st.session_state.daily_tip}</em></div>",
        unsafe_allow_html=True,
    )


# --> Renders the Ai chat sidebar section <-- #
def render_chat_section() -> None:
    """Renders the sidebar chat history and input form."""
    ai_config = C["AI_CONFIG"]
    
    header_color = ai_config.get('Styles', {}).get('SidebarHeaderColor', '#2E7D32')
    st.sidebar.markdown(f"<h3 style='margin-top:40px; color:{header_color};'>{ai_config.get('Header')}</h3>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("<div class='chat-history'>", unsafe_allow_html=True)
    for entry in st.session_state.chat_history[-40:]:
        bubble_class = "bubble-ai" if entry["who"] == "ai" else "bubble-user"
        speaker = ai_config.get("AiName") if entry["who"] == "ai" else ai_config.get("UserName")
        st.sidebar.markdown(
            f"<div class='{bubble_class}'>**{speaker}**<div>{entry['text']}</div></div>",
            unsafe_allow_html=True,
        )
    st.sidebar.markdown("</div>", unsafe_allow_html=True)

    with st.sidebar.form("chat_form", clear_on_submit=True):
        cols = st.columns([0.85, 0.15])
        
        user_input = cols[0].text_input("", placeholder=ai_config.get("InputPlaceholder"))
        submit = cols[1].form_submit_button(ai_config.get("SendButton"))
        
        if submit and user_input:
            st.session_state.chat_history.append({"who": "user", "text": user_input, "time": time.time()})
            st.session_state.chat_history.append({"who": "ai", "text": ai_config.get("ThinkingMessage"), "time": time.time()})
            st.rerun()
# --> ******************************************* <--

# --> Important: renders the main body of the website <--
def render_home_page() -> None:

    col1, col2, col3 = st.columns([1.3, 1, 1])
    with col2:
        st.image('logo.png', width=100)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    
    st.markdown(f"<h1 class='title'>{C['TEXT_CONFIG'].get('AppTitle')}</h1>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='subtitle'>{C['TEXT_CONFIG'].get('AppSubtitle')}</div>",
        unsafe_allow_html=True,
    )
    
    render_feature_cards()
    render_tip_card()
    render_chat_section()
    
    st.markdown(
        f"<div style='text-align:center; color:#4a774a; font-size:12px; margin:28px 0;'>"
        f"{C['TEXT_CONFIG'].get('FooterNote')}"
        "</div>",
        unsafe_allow_html=True,
    )
# --> ************************************************** <--

# -> Renders other pages if the feature cards were clicked <-
def render_tool_page(page_name: str) -> None:
    """Renders the specific tool pages."""
    _back_button()
    if page_name == "carbon_check":
        carbon_check_page()
    elif page_name == "waste_scanner":
        waste_scanner_page()
# -> ********************************************* <--

# ---------> Page rendering functions end here <-------------- #

# ---------> Main functions wich sends a signal to all other functions <------------ #
def main() -> None:
    """Main application entry point."""
    apply_global_style()
    init_session_state()
    process_pending_ai_response()

    current_page = st.session_state["page"]
    if current_page == "carbon_check" or current_page == "waste_scanner":
        render_tool_page(current_page)
        st.stop()

    render_home_page()
# ------------------------------------------------------------------------------------ #

# ----> Main Code <---- #
if __name__ == "__main__":
    st.set_page_config(
        page_title=C["PAGE_TITLE"],
        page_icon=C["PAGE_ICON"],
        layout=C["PAGE_LAYOUT"],
        initial_sidebar_state=C["SIDEBAR_STATE"],
    )
    main()
# ---------------------- #
