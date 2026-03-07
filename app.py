import os
import streamlit as st
import google.generativeai as genai
import re

st.set_page_config(page_title="Brand Detector", page_icon="🎬", layout="wide")

st.title("Brand & Logo Detector")
st.caption("Paste a YouTube link — Gemini will timestamp every brand, product, or logo appearance.")

with st.sidebar:
    st.header("Setup")
    api_key = st.secrets.get("GEMINI_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")
    st.markdown("---")
    st.markdown("**How it works:**")
    st.markdown("1. Enter your Gemini API key")
    st.markdown("2. Paste a YouTube URL")
    st.markdown("3. Gemini analyses the video directly")
    st.markdown("4. Get timestamped brand appearances")

def analyse_brands(youtube_url, model):
    prompt = """Watch this video carefully and identify every moment where a brand, product name, logo, or branded item appears visually on screen.

For each appearance, provide:
- The exact timestamp (MM:SS format)
- The brand or product name
- A brief description of how it appears (e.g., logo on shirt, product on table, billboard in background, sponsor overlay)

Format your response as a structured list like this:
[MM:SS] Brand Name — description

Be thorough and include ALL brand appearances, even brief ones. If the same brand appears multiple times, list each occurrence separately.

If no brands are visible, say "No brands detected."
"""
    response = model.generate_content([
        {"file_data": {"mime_type": "video/mp4", "file_uri": youtube_url}},
        prompt
    ])
    return response.text

def parse_timestamps(text):
    pattern = r'\[(\d{1,2}:\d{2})\]\s+(.+?)(?=\n\[|\Z)'
    matches = re.findall(pattern, text, re.DOTALL)
    return [(ts, desc.strip()) for ts, desc in matches]

# Main UI
youtube_url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")

if st.button("Detect Brands", type="primary", disabled=not youtube_url):
    if not youtube_url:
        st.error("Please enter a YouTube URL.")
    else:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-pro")

        try:
            with st.spinner("Gemini is analysing the video for brands and logos..."):
                result_text = analyse_brands(youtube_url, model)

            st.markdown("---")
            st.subheader("Brand Appearances")

            entries = parse_timestamps(result_text)
            if entries:
                unique_brands = set(e[1].split("—")[0].strip() for e in entries)
                col1, col2 = st.columns(2)
                col1.metric("Total Appearances", len(entries))
                col2.metric("Unique Brands", len(unique_brands))

                st.markdown("---")
                for ts, desc in entries:
                    parts = desc.split("—", 1)
                    brand = parts[0].strip()
                    detail = parts[1].strip() if len(parts) > 1 else ""
                    col_ts, col_brand, col_desc = st.columns([1, 2, 4])
                    col_ts.markdown(f"**`{ts}`**")
                    col_brand.markdown(f"**{brand}**")
                    col_desc.markdown(detail)
            else:
                st.markdown(result_text)

        except Exception as e:
            st.error(f"Error: {e}")
