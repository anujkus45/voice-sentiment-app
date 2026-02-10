import os
import io
import time
import pandas as pd
import streamlit as st
from werkzeug.utils import secure_filename

from audio_utils import chunk_audio
from emotion_detector import predict_emotion

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.title("Voice Sentiment — Streamlit")

st.sidebar.header("Settings")
chunk_ms = st.sidebar.number_input("Chunk length (ms)", value=2000, min_value=100, step=100)
model_name = st.sidebar.selectbox("Model", ["superb/wav2vec2-base-superb-er"], index=0)

uploaded = st.file_uploader("Upload audio file (.wav or .mp3)", type=["wav", "mp3"])

use_latest = st.checkbox("Use latest uploaded file from uploads/", value=False)

if uploaded is not None:
    filename = secure_filename(uploaded.name)
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(uploaded.getvalue())
    st.success(f"Saved to {path}")
    st.audio(uploaded.getvalue(), format="audio/wav")

if use_latest:
    # find latest file
    candidates = []
    for f in os.listdir(UPLOAD_DIR):
        if f.endswith(".wav") or f.endswith(".mp3"):
            p = os.path.join(UPLOAD_DIR, f)
            candidates.append((os.path.getmtime(p), p))
    if candidates:
        candidates.sort(reverse=True)
        latest_path = candidates[0][1]
        st.info(f"Using latest file: {os.path.basename(latest_path)}")
        st.audio(open(latest_path, "rb").read(), format="audio/wav")
    else:
        st.warning("No files found in uploads/")

analyze_btn = st.button("Analyze")

if analyze_btn:
    # determine file to analyze
    if use_latest:
        try:
            file_to_use = latest_path
        except NameError:
            st.error("No latest file available")
            st.stop()
    else:
        if uploaded is None:
            st.error("Upload a file or select 'Use latest'")
            st.stop()
        file_to_use = path

    with st.spinner("Analyzing audio — this may take a while..."):
        chunks = chunk_audio(file_to_use, chunk_length_ms=chunk_ms)

        timeline = []
        prev_emotion = None
        for c in chunks:
            res = predict_emotion(c["chunk"], model_name)
            label = res.get("emotion", "neutral")
            confidence = float(res.get("confidence", 0.0))
            if label != prev_emotion:
                timeline.append({
                    "time": f"{int(c['time']) // 60:02d}:{int(c['time']) % 60:02d}",
                    "seconds": int(c["time"]),
                    "emotion": label,
                    "confidence": round(confidence, 2),
                })
                prev_emotion = label

    if not timeline:
        st.info("No emotion changes detected; result may be neutral.")
    else:
        df = pd.DataFrame(timeline)
        st.subheader("Timeline")
        st.table(df[["time", "emotion", "confidence"]])

        st.subheader("Confidence over time")
        chart_df = df.set_index("time")["confidence"]
        st.bar_chart(chart_df)

        st.subheader("Raw JSON")
        st.json(timeline)
