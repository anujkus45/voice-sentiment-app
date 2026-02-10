import os
import time
import pandas as pd
import streamlit as st

from audio_utils import chunk_audio
from emotion_detector import predict_emotion


# ================= PAGE CONFIG =================

st.set_page_config(
    page_title="Voice Emotion Dashboard",
    layout="wide"
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_SECONDS = 60   # limit analysis to 1 minute


# ================= CUSTOM UI =================

st.markdown("""
<style>

body {
    background-color: #F6F7FB;
}

.main-title {
    font-size: 38px;
    font-weight: 700;
}

.subtitle {
    color: #6c757d;
    margin-bottom: 25px;
}

.card {
    background: white;
    padding: 22px;
    border-radius: 12px;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
    margin-bottom: 25px;
}

.section-title {
    font-size: 22px;
    font-weight: 600;
    margin-bottom: 15px;
}

button {
    border-radius: 8px !important;
}

</style>
""", unsafe_allow_html=True)


# ================= HEADER =================

st.markdown('<div class="main-title">Voice Emotion Dashboard</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="subtitle">Upload audio, analyze emotion changes, and view results in one place.</div>',
    unsafe_allow_html=True
)


# ================= INPUT CARD =================

st.markdown('<div class="card">', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    uploaded = st.file_uploader("Audio file", type=["wav", "mp3"])

with col2:
    chunk_ms = st.number_input(
        "Chunk size (ms)",
        value=10000,
        min_value=2000,
        step=1000
    )

with col3:
    st.selectbox("Model", ["wav2vec2-superb-er"])

st.markdown("</div>", unsafe_allow_html=True)


# ================= BUTTON CARD =================

st.markdown('<div class="card">', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    analyze_btn = st.button("Analyze")

with col2:
    clear_btn = st.button("Clear Uploads")

with col3:
    download_btn = st.button("Download JSON")

st.markdown("</div>", unsafe_allow_html=True)


# ================= CLEAR UPLOADS =================

if clear_btn:
    for f in os.listdir(UPLOAD_DIR):
        os.remove(os.path.join(UPLOAD_DIR, f))
    st.success("Uploads cleared")


# ================= SAVE FILE =================

path = None

if uploaded:

    filename = uploaded.name.replace(" ", "_")
    path = os.path.join(UPLOAD_DIR, filename)

    with open(path, "wb") as f:
        f.write(uploaded.getbuffer())

    st.audio(uploaded.getvalue())

    st.success(f"File uploaded: {filename}")


# ================= ANALYZE =================

timeline = None


if analyze_btn:

    if not uploaded:
        st.error("Please upload an audio file first.")
        st.stop()

    with st.spinner("Analyzing audio... Please wait..."):

        start = time.time()

        try:
            chunks = chunk_audio(path, chunk_length_ms=chunk_ms)

            # limit duration
            max_chunks = int((MAX_SECONDS * 1000) / chunk_ms)

            if len(chunks) > max_chunks:
                st.warning("Only first 60 seconds analyzed.")
                chunks = chunks[:max_chunks]

            timeline = []
            prev_emotion = None

            for i, c in enumerate(chunks):

                # skip alternate chunks
                if i % 2 == 1:
                    continue

                res = predict_emotion(c["chunk"])

                label = res.get("emotion", "neutral")
                conf = float(res.get("confidence", 0.0))

                if label != prev_emotion:

                    timeline.append({
                        "time": f"{int(c['time']//60):02d}:{int(c['time']%60):02d}",
                        "emotion": label,
                        "confidence": round(conf, 3),
                    })

                    prev_emotion = label

        except Exception as e:
            st.error(f"Processing failed: {e}")
            st.stop()

        end = time.time()

    st.success(f"Analysis completed in {round(end-start,2)} sec")


# ================= RESULTS =================

if timeline:

    df = pd.DataFrame(timeline)


    # -------- TABLE --------

    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">Detected Emotion Changes</div>',
        unsafe_allow_html=True
    )

    st.dataframe(df, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


    # -------- CHART --------

    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">Emotion Changes Over Time</div>',
        unsafe_allow_html=True
    )

    chart_df = df.set_index("time")["confidence"]

    st.line_chart(chart_df)

    st.markdown("</div>", unsafe_allow_html=True)


    # -------- JSON --------

    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">Raw JSON</div>',
        unsafe_allow_html=True
    )

    st.json(timeline)

    st.markdown("</div>", unsafe_allow_html=True)


    # -------- DOWNLOAD --------

    if download_btn:

        json_data = df.to_json(orient="records", indent=2)

        st.download_button(
            label="Download Results",
            data=json_data,
            file_name="emotion_results.json",
            mime="application/json"
        )
