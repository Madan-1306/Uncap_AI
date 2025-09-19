from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allow frontend (index.html) to call backend

# 🔹 Load Intel Guard model (misinformation detector)
MODEL_NAME = "facebook/roberta-base"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

# Fake labels (you can adjust with a fine-tuned model)
LABELS = ["not_misconception", "misconception"]

def analyze_text(text):
    """Classify a single text line for misconception detection"""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)
        confidence, predicted = torch.max(probs, dim=-1)
    
    return {
        "label": LABELS[predicted.item()],
        "confidence": confidence.item()
    }

@app.route("/analyze_video", methods=["POST"])
def analyze_video():
    try:
        data = request.get_json()
        video_id = data.get("video_id")

        if not video_id:
            return jsonify({"error": "No video_id provided"}), 400

        # 🔹 Fetch transcript from YouTube
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])

        results = []
        misconceptions = []
        total_high, total_medium, total_low = 0, 0, 0

        for entry in transcript:
            text = entry["text"]
            analysis = analyze_text(text)

            # Mark misconception if label = misconception
            has_misconception = analysis["label"] == "misconception"
            result_entry = {
                "timestamp": f"{int(entry['start']//60)}:{int(entry['start']%60):02}",
                "text": text,
                "hasMisconception": has_misconception
            }
            results.append(result_entry)

            if has_misconception:
                severity = "high" if analysis["confidence"] > 0.8 else "medium" if analysis["confidence"] > 0.5 else "low"
                if severity == "high":
                    total_high += 1
                elif severity == "medium":
                    total_medium += 1
                else:
                    total_low += 1

                misconceptions.append({
                    "text": text,
                    "severity": severity,
                    "confidence": analysis["confidence"]
                })

        summary = {
            "totalMisconceptions": len(misconceptions),
            "highSeverity": total_high,
            "mediumSeverity": total_medium,
            "lowSeverity": total_low,
            "overallRating": (
                "Concerning" if total_high > 2
                else "Moderate" if total_medium > 2
                else "Safe"
            ),
            "recommendation": (
                "Be cautious while trusting this video." if len(misconceptions) > 0
                else "This video appears safe from misconceptions."
            )
        }

        return jsonify({
            "transcript": results,
            "misconceptions": misconceptions,
            "summary": summary
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
