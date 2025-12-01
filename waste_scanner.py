"""
Waste Scanner page for GreenGuard AI.

The scanner looks for common contamination cues (grease, black plastic,
plastic film, lined paper cups, etc.) using lightweight image heuristics
so that we can provide actionable recycling guidance without requiring a
full computer-vision model.
"""

from __future__ import annotations

import io
import random
from typing import Dict, Tuple

import streamlit as st
from PIL import Image

try:
    import numpy as np
except Exception:  # pragma: no cover - numpy should exist but we handle gracefully
    np = None  # type: ignore


IMPACT_STATEMENTS = {
    "recycle": [
        "You kept a clean stream that protects ~20 other recyclables.",
        "Nice! That’s enough material to offset a day of curbside pickups.",
        "Clean recyclables like this can be turned into new packaging within weeks.",
    ],
    "rinse": [
        "A 30-second rinse protects trucks from contamination residues.",
        "Rinsing keeps this out of landfill and saves energy in sorting centers.",
        "Quick cleaning like this can salvage an entire batch of plastics.",
    ],
    "reject": [
        "Spotting non-recyclables early prevents machinery jams downstream.",
        "Diverting this now keeps recycling loads from being rejected.",
        "Good catch—disposing properly avoids contaminating ~10 kg of recyclables.",
    ],
}


def waste_scanner_page() -> None:
    """Render the waste scanner workflow."""
    st.title("♻ Waste Scanner")
    st.caption(
        "Upload any item you're unsure about. The scanner looks for food residue, "
        "plastic films, black plastic, and other tricky details that affect "
        "whether it can go in the recycling bin."
    )

    st.session_state.setdefault("waste_result", None)
    st.session_state.setdefault("waste_last_filename", None)

    uploaded_file = st.file_uploader(
        "Upload a photo (PNG, JPG, or WebP)",
        type=["png", "jpg", "jpeg", "webp"],
        help="Natural lighting works best. Avoid super small or blurry photos.",
    )

    if uploaded_file and uploaded_file.name != st.session_state.get("waste_last_filename"):
        st.session_state["waste_result"] = None
        st.session_state["waste_last_filename"] = uploaded_file.name

    if uploaded_file:
        image = Image.open(io.BytesIO(uploaded_file.read())).convert("RGB")
        st.image(image, caption="Uploaded item", use_column_width=True)

        analyze = st.button("Analyze Item", type="primary")
        if analyze:
            st.session_state["waste_result"] = analyze_waste_item(image)
    else:
        st.info("Upload a photo to see recycling guidance.")
        st.session_state["waste_result"] = None

    result = st.session_state.get("waste_result")
    if result:
        display_result_card(result)
        if st.button("Scan Another Item"):
            st.session_state["waste_result"] = None
            st.session_state["waste_last_filename"] = None
            st.rerun()


def analyze_waste_item(image: Image.Image) -> Dict[str, object]:
    """Generate heuristics, classification, and advice for the uploaded image."""
    metrics, flags = inspect_image(image)
    verdict, action, explanation, bucket = classify_item(flags)
    confidence = estimate_confidence(flags, metrics["brightness"])
    impact = random.choice(IMPACT_STATEMENTS[bucket])

    return {
        "verdict": verdict,
        "action": action,
        "explanation": explanation,
        "impact": impact,
        "features": flags,
        "metrics": metrics,
        "confidence": confidence,
    }


def inspect_image(image: Image.Image) -> Tuple[Dict[str, float], Dict[str, bool]]:
    """Extract lightweight heuristics from the image to mimic CV cues."""
    if np is None:
        # Fallback when numpy is unavailable; assume neutral medium brightness.
        metrics = {
            "brightness": 0.55,
            "dark_fraction": 0.2,
            "warm_fraction": 0.2,
            "shiny_fraction": 0.2,
            "neutral_fraction": 0.2,
        }
    else:
        resized = image.resize((224, 224))
        arr = np.asarray(resized).astype("float32") / 255.0
        brightness = float(arr.mean())
        channel_mean = arr.mean(axis=2)
        dark_fraction = float((channel_mean < 0.25).mean())
        warm_mask = (arr[:, :, 0] - arr[:, :, 1] > 0.08) & (arr[:, :, 0] - arr[:, :, 2] > 0.08)
        warm_fraction = float(warm_mask.mean())
        shiny_mask = (arr.max(axis=2) > 0.9) & (arr.min(axis=2) < 0.2)
        shiny_fraction = float(shiny_mask.mean())
        neutral_fraction = float((arr.std(axis=2) < 0.05).mean())

        metrics = {
            "brightness": brightness,
            "dark_fraction": dark_fraction,
            "warm_fraction": warm_fraction,
            "shiny_fraction": shiny_fraction,
            "neutral_fraction": neutral_fraction,
        }

    flags = {
        "food_residue": metrics["warm_fraction"] > 0.32 and metrics["brightness"] < 0.7,
        "black_plastic": metrics["dark_fraction"] > 0.5 and metrics["brightness"] < 0.4,
        "soft_plastic": metrics["shiny_fraction"] > 0.45 and metrics["brightness"] > 0.35,
        "paper_lining": metrics["brightness"] > 0.65 and metrics["shiny_fraction"] > 0.25,
        "clean_material": metrics["neutral_fraction"] > 0.45,
    }

    if flags["food_residue"] or flags["black_plastic"] or flags["soft_plastic"]:
        flags["clean_material"] = False

    return metrics, flags


def classify_item(flags: Dict[str, bool]) -> Tuple[str, str, str, str]:
    """Map detected flags to a user-facing verdict and guidance."""
    if flags["black_plastic"]:
        return (
            "🚯 Not Recyclable",
            "Place this in general waste—black plastic is rarely detected by optical sorters.",
            "Deep black pigments absorb the sorting lasers, so recycling centers cannot identify it.",
            "reject",
        )

    if flags["soft_plastic"]:
        return (
            "🚯 Not Recyclable",
            "Drop soft plastic films at a store take-back bin or dispose with trash if none exist.",
            "Thin, reflective plastic film tangles in machinery at curbside facilities.",
            "reject",
        )

    if flags["food_residue"]:
        return (
            "⚠ Rinse & Recycle",
            "Rinse off the food residue, scrape any grease, and let it dry before recycling.",
            "Organic residue can contaminate paper and cardboard in the recycling stream.",
            "rinse",
        )

    if flags["paper_lining"]:
        return (
            "⚠ Rinse & Recycle",
            "Peel out the plastic lining or lid where possible, then recycle the clean paper portion.",
            "Paper cups and cartons often have thin plastic liners that need separating to be recycled.",
            "rinse",
        )

    if flags["clean_material"]:
        return (
            "♻ Recyclable",
            "Place it in your mixed recycling bin—clean single-material items are accepted curbside.",
            "No contamination detected; facilities can easily process glass, metal, or cardboard like this.",
            "recycle",
        )

    return (
        "⚠ Rinse & Recycle",
        "Give it a quick check—if it’s rigid and mostly clean, recycle; otherwise rinse first.",
        "The scanner saw mixed cues, so a quick clean ensures it won’t be rejected for contamination.",
        "rinse",
    )


def estimate_confidence(flags: Dict[str, bool], brightness: float) -> float:
    """Provide a friendly confidence indicator based on how decisive the cues were."""
    true_flags = sum(1 for v in flags.values() if v)
    base = 0.6 + 0.08 * max(true_flags - 1, 0)
    if flags["clean_material"] or flags["black_plastic"]:
        base += 0.1
    if 0.35 < brightness < 0.8:
        base += 0.05
    return max(0.45, min(0.95, round(base, 2)))


def display_result_card(result: Dict[str, object]) -> None:
    """Render the scanner output in a friendly card."""
    verdict = result["verdict"]
    action = result["action"]
    explanation = result["explanation"]
    impact = result["impact"]
    features = result["features"]
    confidence = result["confidence"]

    st.markdown("### Result")
    st.markdown(
        f"""
        <div style="
            border-radius:18px;
            padding:20px;
            border:1px solid rgba(76,175,80,0.35);
            background:rgba(244,255,244,0.8);
        ">
            <div style="font-size:28px; font-weight:700; margin-bottom:6px;">{verdict}</div>
            <div style="font-size:18px; font-weight:600; color:#1b5e20; margin-bottom:8px;">{action}</div>
            <div style="color:#2f5f38; margin-bottom:8px;">{explanation}</div>
            <div style="color:#3d7044; font-style:italic;">{impact}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    feature_labels = {
        "food_residue": "Food residue",
        "black_plastic": "Black plastic",
        "soft_plastic": "Plastic film",
        "paper_lining": "Paper cup lining",
        "clean_material": "Clean single material",
    }
    detected = [label for key, label in feature_labels.items() if features.get(key)]

    if detected:
        st.markdown("**Detected features:**")
        chips = " ".join(
            f"<span style='display:inline-block;padding:6px 12px;margin:4px;"
            f"border-radius:999px;background:#e8f5e9;border:1px solid #c8e6c9;"
            f"color:#1b5e20;font-size:13px;'>{label}</span>"
            for label in detected
        )
        st.markdown(f"<div>{chips}</div>", unsafe_allow_html=True)
    else:
        st.markdown("No contamination cues detected.")

    st.markdown("**Scanner confidence**")
    st.progress(confidence)
    st.caption(f"Estimated confidence: {int(confidence * 100)}% based on color and texture cues.")


if __name__ == "__main__":  # pragma: no cover
    waste_scanner_page()

