import os
import io
import json
import requests


# Prefer using the Hugging Face Inference API (serverless-friendly).
# If `HF_API_TOKEN` is set in env, the API will be used. Otherwise fall back
# to local `transformers` pipeline if available (for local dev only).

TARGET_SAMPLE_RATE = 16000


def _call_hf_inference(model_name, wav_bytes):
    token = os.environ.get("HF_API_TOKEN")
    if not token:
        raise RuntimeError("HF_API_TOKEN not set")

    url = f"https://api-inference.huggingface.co/models/{model_name}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/octet-stream",
    }
    resp = requests.post(url, headers=headers, data=wav_bytes, timeout=60)
    resp.raise_for_status()
    return resp.json()


def predict_emotion(audio_segment, model_name="superb/wav2vec2-base-superb-er"):
    """Input: pydub AudioSegment; Output: dict {emotion, confidence}

    Behavior:
    - If `HF_API_TOKEN` is set, send WAV bytes to HF Inference API and parse
      the returned labels/scores.
    - Otherwise, attempt to use local `transformers` pipeline if installed.
    """

    # Ensure mono + target sample rate
    if audio_segment.channels != 1:
        audio_segment = audio_segment.set_channels(1)
    if audio_segment.frame_rate != TARGET_SAMPLE_RATE:
        audio_segment = audio_segment.set_frame_rate(TARGET_SAMPLE_RATE)

    # Export to WAV bytes
    wav_io = io.BytesIO()
    audio_segment.export(wav_io, format="wav")
    wav_bytes = wav_io.getvalue()

    # Try HF Inference API
    try:
        if os.environ.get("HF_API_TOKEN"):
            outputs = _call_hf_inference(model_name, wav_bytes)
            # Expected: list of {label: ..., score: ...} or similar
            if not outputs:
                return {"emotion": "neutral", "confidence": 0.0}
            # Some HF audio classifiers return a list; pick highest score
            if isinstance(outputs, dict) and "error" in outputs:
                return {"emotion": "neutral", "confidence": 0.0}

            if isinstance(outputs, dict):
                # handle unexpected single-dict response
                outputs = [outputs]

            best = max(outputs, key=lambda x: x.get("score", 0.0))
            label = best.get("label") or "neutral"
            score = float(best.get("score", 0.0) or 0.0)
            return {"emotion": label, "confidence": score}
    except Exception:
        # fall through to local fallback
        pass

    # Local fallback (for development only)
    try:
        from transformers import pipeline
        import numpy as np

        # Convert AudioSegment -> numpy samples (normalized)
        samples = np.array(audio_segment.get_array_of_samples())
        if samples.size == 0:
            return {"emotion": "neutral", "confidence": 0.0}
        max_val = float(1 << (8 * audio_segment.sample_width - 1))
        samples = samples.astype("float32")
        if max_val > 0:
            samples = samples / max_val

        model = pipeline("audio-classification", model=model_name, top_k=None)
        outputs = model(samples, sampling_rate=TARGET_SAMPLE_RATE)
        if not outputs:
            return {"emotion": "neutral", "confidence": 0.0}
        if isinstance(outputs, dict):
            outputs = [outputs]
        best = max(outputs, key=lambda x: x.get("score", 0.0))
        label = best.get("label") or "neutral"
        score = float(best.get("score", 0.0) or 0.0)
        return {"emotion": label, "confidence": score}
    except Exception:
        return {"emotion": "neutral", "confidence": 0.0}
