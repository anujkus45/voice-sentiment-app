from pydub import AudioSegment
import os

# Optional: set custom ffmpeg paths via environment variables
ffmpeg_path = os.getenv("FFMPEG_PATH")
ffprobe_path = os.getenv("FFPROBE_PATH")

if ffmpeg_path:
    AudioSegment.converter = ffmpeg_path
    AudioSegment.ffmpeg = ffmpeg_path
if ffprobe_path:
    AudioSegment.ffprobe = ffprobe_path


def chunk_audio(file_path, chunk_length_ms=4000):
    audio = AudioSegment.from_file(file_path)

    chunks = []
    for i in range(0, len(audio), chunk_length_ms):
        chunks.append({
            "time": i / 1000,
            "chunk": audio[i:i + chunk_length_ms]
        })

    return chunks
