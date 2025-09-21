from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, VideoUnavailable, TranscriptsDisabled
from transformers import AutoTokenizer, AutoModelForSequenceClassification, logging as hf_logging
import torch
import re
import traceback
import logging

# ------------------ Setup ------------------
logging.basicConfig(level=logging.DEBUG)
hf_logging.set_verbosity_info()

app = Flask(__name__)
CORS(app, resources={r"/analyze": {"origins": "*"}})

# ------------------ Model ------------------
MODEL_NAME = "facebook/bart-large-mnli"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, revision="main")
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, revision="main")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

label_map = {
    0: "pants-fire",
    1: "false",
    2: "barely-true",
    3: "half-true",
    4: "mostly-true",
    5: "true"
}

# ------------------ Stopwords / filler words ------------------
STOPWORDS = ["hi", "hello", "you know", "zoom in", "wooh", "hey friends", "obvious reasons"]

# ------------------ Knowledge Retrieval ------------------
def retrieve_correct_fact(snippet_text):
    """Fetch correct fact + source dynamically (Wikipedia as placeholder)"""
    try:
        from wikipedia import summary, page, exceptions
        result = page(snippet_text)
        fact = summary(result.title, sentences=2)
        source = f"Wikipedia: {result.url}"
        return fact, source
    except exceptions.DisambiguationError as e:
        fact = summary(e.options[0], sentences=2)
        source = f"Wikipedia: {e.options[0]}"
        return fact, source
    except Exception:
        return None, None

# ------------------ Transcript Analysis ------------------
def analyze_line_safe(text):
    """Analyze a snippet safely; returns partial info if snippet fails"""
    try:
        # Ignore filler/short snippets
        if len(text.split()) < 3 or any(sw in text.lower() for sw in STOPWORDS):
            return {"label": "IGNORED", "raw_label": None, "score": None, "correct_fact": None, "source": None}

        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True).to(device)
        with torch.no_grad():
            outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)
        pred_id = torch.argmax(probs).item()
        label = label_map[pred_id]
        confidence = torch.max(probs).item()

        # Map to UI labels
        if label in ["true", "mostly-true"]:
            misinfo_label = "REAL"
            correct_fact, source = None, None
        elif label in ["half-true", "barely-true"]:
            misinfo_label = "UNCERTAIN"
            correct_fact, source = None, None
        else:
            misinfo_label = "MISINFORMATION"
            try:
                correct_fact, source = retrieve_correct_fact(text)
            except Exception as e:
                correct_fact, source = None, f"Fact retrieval failed: {str(e)}"

        return {
            "label": misinfo_label,
            "raw_label": label,
            "score": confidence,
            "correct_fact": correct_fact,
            "source": source
        }
    except Exception as e:
        return {
            "label": "ERROR",
            "raw_label": None,
            "score": None,
            "correct_fact": None,
            "source": f"Snippet processing failed: {str(e)}"
        }

# ------------------ Helper ------------------
def extract_video_id(url):
    patterns = [
        r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([^"&?\/\s]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

# ------------------ Route ------------------
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
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    # Fetch transcript
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
        transcript = None
        for t in transcript_list:
            try:
                transcript = t.fetch()
                break
            except:
                continue
        if not transcript:
            return jsonify({"error": "No valid transcript found"}), 400
    except (NoTranscriptFound, VideoUnavailable, TranscriptsDisabled) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Failed to fetch transcript: {str(e)}"}), 500

    # Analyze transcript safely
    analyzed_transcript = []
    misconceptions = []
    summary_facts = []
    for snippet in transcript:
        text = snippet.text
        start = snippet.start
        analysis = analyze_line_safe(text)
        if analysis["label"] == "IGNORED":
            continue

        line_data = {
            "timestamp": start,
            "text": text,
            "misinformation": analysis["label"],
            "score": analysis["score"],
            "correct_fact": analysis.get("correct_fact"),
            "source": analysis.get("source")
        }
        analyzed_transcript.append(line_data)
        if analysis["label"] == "MISINFORMATION":
            misconceptions.append(line_data)
            if analysis.get("correct_fact"):
                summary_facts.append({
                    "term": text,
                    "fact": analysis["correct_fact"],
                    "source": analysis["source"]
                })

    # Summary
    summary = {
        "total_snippets": len(analyzed_transcript),
        "misinformation_count": len(misconceptions),
        "real_count": len([x for x in analyzed_transcript if x["misinformation"] == "REAL"])
    }

    return jsonify({
        "video_url": video_url,
        "transcript": analyzed_transcript,
        "misconceptions": misconceptions,
        "summary": summary,
        "summary_facts": summary_facts
    })

if __name__ == '__main__':
    app.run(debug=True, port=8001, host='0.0.0.0')
