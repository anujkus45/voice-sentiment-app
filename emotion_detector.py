from transformers import pipeline
import numpy as np


emotion_classifier = None   # lazy-load the model
TARGET_SAMPLE_RATE = 16000


def get_model():
    global emotion_classifier

    if emotion_classifier is None:
        emotion_classifier = pipeline(
            "audio-classification",
            model="superb/wav2vec2-base-superb-er",
            top_k=None,
        )

    return emotion_classifier


def predict_emotion(audio_segment):
    """
    Input: pydub AudioSegment
    Output: dict {emotion, confidence}
    """

    # Ensure mono + target sample rate
    if audio_segment.channels != 1:
        audio_segment = audio_segment.set_channels(1)

    if audio_segment.frame_rate != TARGET_SAMPLE_RATE:
        audio_segment = audio_segment.set_frame_rate(TARGET_SAMPLE_RATE)

    # AudioSegment -> numpy
    samples = np.array(audio_segment.get_array_of_samples())

    if samples.size == 0:
        return {"emotion": "neutral", "confidence": 0.0}

    # Normalize
    max_val = float(1 << (8 * audio_segment.sample_width - 1))
    samples = samples.astype("float32")
    if max_val > 0:
        samples = samples / max_val

    try:
        model = get_model()
        outputs = model(samples, sampling_rate=TARGET_SAMPLE_RATE)
    except Exception:
        # Fallback to neutral on inference errors
        return {"emotion": "neutral", "confidence": 0.0}

    if not outputs:
        return {"emotion": "neutral", "confidence": 0.0}

    if isinstance(outputs, dict):
        outputs = [outputs]

    best = max(outputs, key=lambda x: x.get("score", 0.0))
    label = best.get("label") or "neutral"
    score = float(best.get("score", 0.0) or 0.0)

    return {"emotion": label, "confidence": score}
