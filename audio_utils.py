from pydub import AudioSegment

# HARD-CODED paths (Windows fix)
AudioSegment.converter = r"C:\Users\anuj04\Downloads\ffmpeg-2026-02-04-git-627da1111c-full_build\ffmpeg-2026-02-04-git-627da1111c-full_build\bin\ffmpeg.exe"
AudioSegment.ffmpeg    = AudioSegment.converter
AudioSegment.ffprobe   = r"C:\Users\anuj04\Downloads\ffmpeg-2026-02-04-git-627da1111c-full_build\ffmpeg-2026-02-04-git-627da1111c-full_build\bin\ffprobe.exe"


def chunk_audio(file_path, chunk_length_ms=4000):
    audio = AudioSegment.from_file(file_path)

    chunks = []
    for i in range(0, len(audio), chunk_length_ms):
        chunks.append({
            "time": i / 1000,
            "chunk": audio[i:i + chunk_length_ms]
        })

    return chunks
