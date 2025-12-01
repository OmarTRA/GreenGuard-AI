
import streamlit as st
import pandas as pd


def _init_state() -> None:
    """Ensure we have state to track answers and submission."""
    st.session_state.setdefault("carbon_submitted", False)
    st.session_state.setdefault("carbon_answers", {})


def _questions_ui() -> None:
    """Render a short, friendly questionnaire."""
    st.title("🟢 Carbon Quick Check")
    st.markdown(
        """
        Answer a few quick questions and we'll show where your footprint is highest,
        plus a simple plan with 3 high‑impact actions.
        """
    )

    with st.container():
        st.markdown("### Your weekly travel")
        car_km = st.slider(
            "About how many kilometers do you travel by car per week?",
            min_value=0,
            max_value=1000,
            step=25,
            value=150,
        )
        st.caption("Includes driving yourself, taxis, or ride-hailing.")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Home energy")
        electricity_kwh = st.slider(
            "Approximate electricity use per month (kWh)",
            min_value=50,
            max_value=1200,
            step=50,
            value=300,
        )
        ac_usage = st.radio(
            "Air‑conditioning use",
            ["Rarely", "Sometimes", "Most days"],
            horizontal=True,
        )

    with col2:
        st.markdown("### Food & shopping")
        diet = st.radio(
            "Typical diet",
            ["Mostly plant‑based", "Mixed", "High meat"],
            horizontal=False,
        )
        shopping = st.slider(
            "New clothes / gadgets you buy per month",
            min_value=0,
            max_value=10,
            step=1,
            value=2,
        )

    if st.button("Show my impact and tips", type="primary", use_container_width=True):
        st.session_state["carbon_answers"] = {
            "car_km": car_km,
            "electricity_kwh": electricity_kwh,
            "ac_usage": ac_usage,
            "diet": diet,
            "shopping": shopping,
        }
        st.session_state["carbon_submitted"] = True
        st.rerun()


def _score_from_answers(answers: dict) -> dict:
    """Turn raw answers into rough relative impact scores per area."""
    car_km = answers["car_km"]
    electricity = answers["electricity_kwh"]
    ac_usage = answers["ac_usage"]
    diet = answers["diet"]
    shopping = answers["shopping"]

    transport_score = min(car_km / 200.0, 3.0)  # 0–3

    home_base = electricity / 400.0
    ac_boost = {"Rarely": 0.0, "Sometimes": 0.4, "Most days": 0.8}[ac_usage]
    home_score = min(home_base + ac_boost, 3.0)

    diet_map = {"Mostly plant‑based": 0.8, "Mixed": 1.6, "High meat": 2.4}
    diet_score = diet_map.get(diet, 1.6)

    shopping_score = min(shopping / 2.0, 3.0)

    return {
        "Transport": round(transport_score, 2),
        "Home energy": round(home_score, 2),
        "Food": round(diet_score, 2),
        "Shopping": round(shopping_score, 2),
    }


def _actions_from_scores(scores: dict) -> list[str]:
    """Pick 3 high‑impact, tailored actions based on the strongest areas."""
    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_areas = [name for name, _ in ordered[:3]]

    library = {
        "Transport": [
            "For trips under 5 km, try walking, cycling, or public transport 1–2 times per week.",
            "Consider car‑sharing or combining errands into one trip instead of several short drives.",
        ],
        "Home energy": [
            "Set your AC to around 24 °C and close doors/windows to reduce wasted cooling.",
            "Swap the 3 most‑used bulbs at home for LEDs and switch off devices fully at night.",
        ],
        "Food": [
            "Try 1–2 meat‑free days per week focusing on beans, lentils, or local vegetables.",
            "Reduce beef and lamb first—they usually have the highest carbon footprint.",
        ],
        "Shopping": [
            "Pause impulse buys for 30 days; only buy clothes/gadgets you planned ahead.",
            "Choose durable, repairable items and second‑hand where possible.",
        ],
    }

    tips: list[str] = []
    for area in top_areas:
        tips.extend(library.get(area, []))

    # Return the first 3 concise, high‑impact tips
    return tips[:3]


def _results_ui() -> None:
    """Show the modern results view with graph and recommendations."""
    answers = st.session_state.get("carbon_answers", {})
    if not answers:
        # Fallback: if state was lost, show questions again.
        st.session_state["carbon_submitted"] = False
        _questions_ui()
        return

    scores = _score_from_answers(answers)

    st.title("Your footprint snapshot")
    st.markdown(
        "<div style='color:#2E7D32; margin-bottom:6px;'>Higher bars = bigger opportunity to cut emissions.</div>",
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(
        {"Area": list(scores.keys()), "Impact": list(scores.values())}
    ).set_index("Area")

    st.bar_chart(df, height=320, use_container_width=True)

    total_score = sum(scores.values())
    if total_score < 4:
        summary = "Your footprint looks relatively light overall — nice work. There are still a few easy wins below."
    elif total_score < 7:
        summary = "You have a balanced footprint with several areas where small changes could add up quickly."
    else:
        summary = "There are some big opportunities to cut emissions — starting with the tallest bars in your chart."

    st.markdown(
        f"""
        <div style="
            border-radius:18px;
            padding:20px;
            border:1px solid rgba(76,175,80,0.35);
            background:rgba(244,255,244,0.9);
            margin-top:12px;
        ">
            <div style="font-size:20px; font-weight:700; color:#1b5e20; margin-bottom:6px;">
                What this means
            </div>
            <div style="color:#2f5f38;">{summary}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tips = _actions_from_scores(scores)

    st.markdown("### 3 high‑impact actions for you")
    for i, tip in enumerate(tips, start=1):
        st.markdown(
            f"""
            <div style="
                border-radius:14px;
                padding:12px 14px;
                margin-bottom:8px;
                background:#ffffff;
                border:1px solid #D9EFD9;
                box-shadow:0 4px 10px rgba(0,0,0,0.03);
                color:#225e33;
            ">
                <strong>#{i}</strong> {tip}
            </div>
            """,
            unsafe_allow_html=True,
        )

    cols = st.columns([0.4, 0.6])
    with cols[0]:
        if st.button("Edit my answers", use_container_width=True):
            st.session_state["carbon_submitted"] = False
            st.rerun()
    with cols[1]:
        st.caption("You can tweak your answers and instantly see how your graph changes.")


def carbon_check_page() -> None:
    """Public entry point for the Carbon Quick Check page."""
    _init_state()
    if st.session_state.get("carbon_submitted"):
        _results_ui()
    else:
        _questions_ui()


if __name__ == "__main__":
    carbon_check_page()
