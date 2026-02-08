from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
import os
from audio_utils import chunk_audio
from emotion_detector import predict_emotion

# Emotion label normalization
EMOTION_MAPS = {
    "short_to_full": {
        "ang": "angry",
        "sad": "sad",
        "hap": "happy",
        "neu": "neutral",
    },
    "none": {},
}

DEFAULT_MAP = "short_to_full"
ALLOWED_MODELS = {
    "superb": "superb/wav2vec2-base-superb-er",
}


app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def ensure_upload_dir():
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def get_latest_audio():
    ensure_upload_dir()
    candidates = []
    for f in os.listdir(app.config["UPLOAD_FOLDER"]):
        if f.endswith(".wav") or f.endswith(".mp3"):
            path = os.path.join(app.config["UPLOAD_FOLDER"], f)
            candidates.append((os.path.getmtime(path), path))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def format_time(sec):
    m = sec // 60
    s = sec % 60
    return f"{m:02d}:{s:02d}"


@app.route("/")
def index():
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "audio" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["audio"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    ensure_upload_dir()
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    return jsonify({"message": "Audio uploaded successfully", "filename": filename})


@app.route("/analyze", methods=["POST"])
def analyze():
    payload = request.get_json(silent=True) or {}

    filename = payload.get("filename")
    chunk_ms = payload.get("chunk_ms", 2000)
    emotion_map_name = payload.get("emotion_map", DEFAULT_MAP)
    model_name = payload.get("model", "superb")

    try:
        chunk_ms = int(chunk_ms)
    except (TypeError, ValueError):
        return jsonify({"error": "chunk_ms must be an integer"}), 400

    if chunk_ms <= 0:
        return jsonify({"error": "chunk_ms must be > 0"}), 400

    if model_name not in ALLOWED_MODELS:
        return jsonify({"error": f"Unknown model: {model_name}"}), 400

    emotion_map = EMOTION_MAPS.get(emotion_map_name)
    if emotion_map is None:
        return jsonify({"error": f"Unknown emotion map: {emotion_map_name}"}), 400

    if filename:
        test_file = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        if not os.path.exists(test_file):
            return jsonify({"error": "Uploaded file not found"}), 404
    else:
        test_file = get_latest_audio()

    if not test_file:
        return jsonify({"error": "No audio file found"}), 404

    chunks = chunk_audio(test_file, chunk_length_ms=chunk_ms)

    timeline = []
    prev_emotion = None

    for c in chunks:
        result = predict_emotion(c["chunk"])
        label = emotion_map.get(result["emotion"], result["emotion"])

        if label != prev_emotion:
            timeline.append({
                "time": format_time(int(c["time"])),
                "emotion": label,
                "confidence": round(result["confidence"], 2),
            })
            prev_emotion = label

    return jsonify({
        "filename": os.path.basename(test_file),
        "chunk_ms": chunk_ms,
        "emotion_map": emotion_map_name,
        "model": model_name,
        "timeline": timeline,
    })


@app.route("/clear", methods=["POST"])
def clear():
    ensure_upload_dir()
    deleted = 0
    for f in os.listdir(app.config["UPLOAD_FOLDER"]):
        if f.endswith(".wav") or f.endswith(".mp3"):
            try:
                os.remove(os.path.join(app.config["UPLOAD_FOLDER"], f))
                deleted += 1
            except OSError:
                pass
    return jsonify({"deleted": deleted})


if __name__ == "__main__":
    app.run(debug=False)
