🧠 Uncap - Misconception Detector AI
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

A Gen AI system that detects misconceptions, fake facts, or misleading claims in YouTube / social media videos by analyzing transcripts and cross-verifying them with trusted knowledge sources using RAG (Retrieval-Augmented Generation).

With the explosion of online educational videos on YouTube, Instagram, and TikTok, learners often encounter misleading or partially incorrect content. Uncap is designed to detect misinformation specifically in educational and factual videos, helping students, teachers, and researchers verify learning material.

🎯 Goal: Ensure educational content and factual videos are trustworthy, improving media literacy and critical thinking.

The Story Behind Uncap 📖
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

We noticed:

Even educational videos sometimes contain misleading facts or outdated information, and existing tools either focus on general text content or pre-recorded videos, without providing real-time snippet-wise analysis.

Uncap fills this gap by:

Fetching video transcripts (captions)

Analyzing each snippet for truthfulness as the video plays

Classifying snippets as:

❌ MISINFORMATION

⚠️ UNCERTAIN

✅ REAL

Optionally providing corrective references (demo only)

Summarizing misinformation patterns in the video

🔍 Key Insight: While other software focuses on offline text or static video analysis, Uncap provides real-time fact-checking for educational video streams.

Why Uncap is Unique 🌟
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Real-Time Detection: Snippet-wise classification while the video plays.

Educational Focus: Tailored for learning/factual videos, not general entertainment.

Corrective References: Shows possible factual corrections (demo).

Prototype Workflow: Demonstrates a real-time video fact-checking system for educational content.

Fine-Tuning Ready: Can be trained for specific educational domains like science, history, or technology.

How It Works ⚙️
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Input Video URL: YouTube (future: Instagram/TikTok educational videos).

Fetch Transcript: Using video captions.

Analyze Each Snippet:

Output: ❌ MISINFORMATION | ⚠️ UNCERTAIN | ✅ REAL

Corrective Fact Retrieval: (Demo using online references)

Summary Generation:

Total snippets analyzed

Number of misinformation snippets

List of corrective facts and sources

⚠️ Prototype Note: Processing long videos may take time, and demo references are not guaranteed accurate. This is a demo of workflow, not a production-grade system.

Tech Stack 🛠️
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Python 3.13 – Programming language

Flask + Flask-CORS – Backend API

PyTorch + Transformers – AI inference (demo model)

YouTube Transcript API – Captions for analysis

Demo Knowledge References – Wikipedia (placeholder for real fact-checking)

Limitations & Considerations ⚠️
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Time-Consuming: Long videos may take several minutes.

Prototype Stage: Results may be irrelevant or partial.

References Demo: Only for demonstration, not verified facts.

Domain-Specific Accuracy: Requires fine-tuning for educational subjects.

🔧 Future Improvements:
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Real-time Instagram/TikTok educational content support

Fine-tuned models for specific educational domains

Visual dashboards showing misinformation trends

Integration with trusted educational databases

Enhanced student/teacher learning tools

Intended Use 🎓
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Uncap is designed to:

Detect misinformation in educational videos

Help learners verify facts in science, history, and other subjects

Provide a demo workflow for real-time educational video fact-checking-

Installation & Usage 🚀
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Clone the repository:

git clone https://github.com/yourusername/uncap.git
cd uncap


Install dependencies:

pip install -r requirements.txt


Run Flask App:

python app.py


Analyze a Video: POST a YouTube URL to /analyze endpoint and receive JSON output.

Acknowledgements 🙏
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Existing AI text-classification models and libraries inspired this prototype workflow

YouTube Transcript API – Captions for video analysis

Flask & PyTorch – Backend and AI inference engine

Wikipedia – Demo corrective facts


Helps users separate facts from fiction, fighting misinformation in education, science, health, and news.
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
