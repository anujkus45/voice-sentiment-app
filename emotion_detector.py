from transformers import pipeline
import numpy as np


# Load emotion classification pipeline (first time slow, normal)
emotion_classifier = pipeline(
    "audio-classification",
    model="superb/wav2vec2-base-superb-er",
    top_k=None,
)

TARGET_SAMPLE_RATE = 16000

def predict_emotion(audio_segment):
    """
    Input: pydub AudioSegment
    Output: dict {emotion, confidence}
    """

    # Ensure mono + target sample rate for the model
    if audio_segment.channels != 1:
        audio_segment = audio_segment.set_channels(1)
    if audio_segment.frame_rate != TARGET_SAMPLE_RATE:
        audio_segment = audio_segment.set_frame_rate(TARGET_SAMPLE_RATE)

    # AudioSegment -> numpy array
    samples = np.array(audio_segment.get_array_of_samples())
    if samples.size == 0:
        return {"emotion": "neutral", "confidence": 0.0}

    # normalize with dtype range to avoid divide-by-zero on silent audio
    max_val = float(1 << (8 * audio_segment.sample_width - 1))
    samples = samples.astype("float32") / max_val

    # Run model
    results = emotion_classifier(
        samples,
        sampling_rate=TARGET_SAMPLE_RATE,
    )

    top = results[0]

    return {
        "emotion": top["label"],
        "confidence": round(top["score"], 3)
    }
