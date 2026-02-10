import os
from pydub import AudioSegment


# Force ffmpeg path (Streamlit Cloud compatible)
AudioSegment.converter = "ffmpeg"
AudioSegment.ffmpeg = "ffmpeg"
AudioSegment.ffprobe = "ffprobe"


MAX_AUDIO_MB = 8   # free tier safety limit


def chunk_audio(file_path, chunk_length_ms=4000):

    if not os.path.exists(file_path):
        raise FileNotFoundError("Audio file not found")

    size_mb = os.path.getsize(file_path) / (1024 * 1024)

    if size_mb > MAX_AUDIO_MB:
        raise ValueError("Audio file too large (max 8MB allowed)")

    try:
        audio = AudioSegment.from_file(file_path)
    except Exception as e:
        raise RuntimeError(f"Audio decode failed: {e}")

    if len(audio) < 500:
        raise ValueError("Audio too short")

    chunks = []

    for i in range(0, len(audio), chunk_length_ms):

        chunk = audio[i:i + chunk_length_ms]

        if len(chunk) < 300:
            continue

        chunks.append({
            "time": round(i / 1000, 2),
            "chunk": chunk
        })

    if not chunks:
        raise RuntimeError("No valid audio chunks generated")

    return chunks
