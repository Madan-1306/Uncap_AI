from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

app = Flask(__name__)

# -----------------------------
# Load BERT fake news detection model
# -----------------------------
MODEL_NAME = "mrm8488/bert-tiny-finetuned-fake-news-detection"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

# -----------------------------
# Helper functions
# -----------------------------
def analyze_line(text):
    """
    Analyze a single line of transcript for fake news / real info
    """
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    probs = torch.softmax(outputs.logits, dim=1)
    labels = ["REAL", "FAKE"]
    return {"label": labels[torch.argmax(probs)], "score": torch.max(probs).item()}

def extract_video_id(url):
    """
    Extract YouTube video ID from URL
    """
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        return None

# -----------------------------
# Routes
# -----------------------------
@app.route('/analyze', methods=['POST'])
def analyze_video():
    data = request.json
    video_url = data.get("url")

    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    video_id = extract_video_id(video_url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    try:
        # Fetch transcript
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
    except Exception as e:
        return jsonify({"error": f"Could not fetch transcript: {str(e)}"}), 500

    # Analyze each transcript line
    analyzed_transcript = []
    misconceptions = []
    for line in transcript:
        analysis = analyze_line(line["text"])
        line_data = {
            "timestamp": line["start"],  # start time in seconds
            "text": line["text"],
            "misinformation": analysis["label"],
            "score": analysis["score"]
        }
        analyzed_transcript.append(line_data)

        # If line is FAKE, store in separate list
        if analysis["label"] == "FAKE":
            misconceptions.append(line_data)

    # Return JSON
    return jsonify({
        "video_url": video_url,
        "transcript": analyzed_transcript,
        "misconceptions": misconceptions
    })

# -----------------------------
# Main
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True, port=8000)
