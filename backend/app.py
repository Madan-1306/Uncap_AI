from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, VideoUnavailable, TranscriptsDisabled
from transformers import AutoTokenizer, AutoModelForSequenceClassification, logging as hf_logging
import torch
import traceback
import re
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
hf_logging.set_verbosity_info()  # Hugging Face logging

app = Flask(__name__)
CORS(app, resources={r"/analyze": {"origins": "*"}})

# Load BERT model (force main branch)
MODEL_NAME = "mariagrandury/roberta-base-finetuned-sms-spam-detection"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, revision="main")
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, revision="main")

label_map = {
    0: "pants-fire",
    1: "false",
    2: "barely-true",
    3: "half-true",
    4: "mostly-true",
    5: "true"
}

# Helper functions
def analyze_line(text):
    """Analyze a single line of transcript for fake news / real info"""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    probs = torch.softmax(outputs.logits, dim=1)
    pred_id = torch.argmax(probs).item()
    label = label_map[pred_id]
    confidence = torch.max(probs).item()

    # Group into your UI labels
    if label in ["true", "mostly-true"]:
        misinfo_label = "REAL"
    elif label in ["half-true", "barely-true"]:
        misinfo_label = "UNCERTAIN"
    else:  # false, pants-fire
        misinfo_label = "MISINFORMATION"

    return {"label": misinfo_label, "raw_label": label, "score": confidence}

def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    patterns = [
        r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([^"&?\/\s]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

# Routes
@app.route('/analyze', methods=['POST'])
def analyze_video():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Empty request body"}), 400
        video_url = data.get("url")
        logging.debug(f"Received video URL: {video_url}")
    except ValueError:
        return jsonify({"error": "Invalid JSON format"}), 400

    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    video_id = extract_video_id(video_url)
    logging.debug(f"Extracted video ID: {video_id}")
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    # Fetch transcript
    transcript = None
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)  # returns TranscriptList object

        for t in transcript_list:
            try:
                transcript = t.fetch()  # FetchedTranscript object
                logging.debug(f"Using transcript in language: {t.language_code}")
                break
            except Exception as e:
                logging.warning(f"Failed to fetch transcript for language {t.language_code}: {e}")
                continue

        if not transcript:
            return jsonify({"error": "No valid transcript found for any language."}), 400

    except NoTranscriptFound:
        return jsonify({"error": "No transcript found for this video."}), 400
    except VideoUnavailable:
        return jsonify({"error": "Video is unavailable or private."}), 400
    except TranscriptsDisabled:
        return jsonify({"error": "Transcripts are disabled for this video."}), 400
    except Exception as e:
        logging.error(f"Unexpected error for video ID {video_id}: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Failed to fetch transcript: {str(e)}"}), 500

    # Analyze transcript
    analyzed_transcript = []
    misconceptions = []
    for snippet in transcript:  # FetchedTranscriptSnippet objects
        text = snippet.text
        start = snippet.start
        analysis = analyze_line(text)
        line_data = {
            "timestamp": start,
            "text": text,
            "misinformation": analysis["label"],
            "score": analysis["score"]
        }
        analyzed_transcript.append(line_data)
        if analysis["label"] == "MISINFORMATION":
            misconceptions.append(line_data)

    return jsonify({
        "video_url": video_url,
        "transcript": analyzed_transcript,
        "misconceptions": misconceptions
    })

if __name__ == '__main__':
    app.run(debug=True, port=8001, host='0.0.0.0')
