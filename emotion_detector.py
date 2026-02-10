import streamlit as st
import numpy as np
from transformers import pipeline


TARGET_SAMPLE_RATE = 16000


@st.cache_resource
def load_model():
    """
    Loads model only once per app lifetime.
    Cached in memory.
    """
    return pipeline(
        "audio-classification",
        model="superb/wav2vec2-base-superb-er",
        top_k=None
    )


def audiosegment_to_numpy(audio_segment):

    samples = np.array(audio_segment.get_array_of_samples())

    if samples.size == 0:
        return None

    max_val = float(1 << (8 * audio_segment.sample_width - 1))

    samples = samples.astype("float32")

    if max_val > 0:
        samples /= max_val

    return samples


def predict_emotion(audio_segment):

    # convert audio
    samples = audiosegment_to_numpy(audio_segment)

    if samples is None:
        return {"emotion": "neutral", "confidence": 0.0}

    # load cached model
    model = load_model()

    # predict
    outputs = model(
        samples,
        sampling_rate=TARGET_SAMPLE_RATE
    )

    if not outputs:
        return {"emotion": "neutral", "confidence": 0.0}

    best = max(outputs, key=lambda x: x["score"])

    return {
        "emotion": best["label"],
        "confidence": round(float(best["score"]), 3)
    }
