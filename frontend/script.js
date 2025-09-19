/**
 * YouTube Fact Checker - Frontend
 * - Extracts YouTube video ID from URL
 * - Fetches transcript using YouTube Transcript API (via backend)
 * - Sends transcript lines to backend (Intel Guard)
 * - Displays misconceptions in UI
 */
class YouTubeFactChecker {
    constructor() {
        this.apiBaseUrl = "http://localhost:8000"; // Flask backend
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        const analyzeBtn = document.getElementById("analyzeBtn");
        const urlInput = document.getElementById("youtubeUrl");

        analyzeBtn.addEventListener("click", () => this.analyzeVideo());

        urlInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter") this.analyzeVideo();
        });
    }

    extractVideoId(url) {
        const regex = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/;
        const match = url.match(regex);
        return match ? match[1] : null;
    }

    showError(message) {
        const errorDiv = document.getElementById("errorMessage");
        errorDiv.textContent = message;
        errorDiv.style.display = "block";
    }

    hideError() {
        document.getElementById("errorMessage").style.display = "none";
    }

    showLoading() {
        document.getElementById("loading").style.display = "block";
        document.getElementById("analyzeBtn").disabled = true;
    }

    hideLoading() {
        document.getElementById("loading").style.display = "none";
        document.getElementById("analyzeBtn").disabled = false;
    }

    async analyzeVideo() {
        const url = document.getElementById("youtubeUrl").value.trim();

        if (!url) {
            this.showError("Please enter a YouTube URL");
            return;
        }

        const videoId = this.extractVideoId(url);
        if (!videoId) {
            this.showError("Please enter a valid YouTube URL");
            return;
        }

        this.hideError();
        this.showLoading();

        try {
            // Ask backend to fetch transcript and analyze
            const response = await fetch(`${this.apiBaseUrl}/analyze_video`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ video_id: videoId }),
            });

            if (!response.ok) throw new Error("Backend error");

            const data = await response.json();

            console.log("🔍 Analysis Results:", data);

            this.displayResults(data);
            document.getElementById("resultsSection").style.display = "block";
        } catch (error) {
            console.error("Analysis failed:", error);
            this.showError("Analysis failed. Please try again later.");
        } finally {
            this.hideLoading();
        }
    }

    displayResults(data) {
        this.displayTranscript(data.transcript);
        this.displayMisconceptions(data.misconceptions);
        this.displaySummary(data.summary);
    }

    displayTranscript(transcript) {
        const container = document.getElementById("transcriptContainer");
        container.innerHTML = transcript
            .map(
                (line) => `
            <div class="transcript-line ${
                line.hasMisconception ? "has-misconception" : ""
            }">
                <div class="timestamp">${line.timestamp}</div>
                <div class="text">
                    ${line.text}
                    ${
                        line.hasMisconception
                            ? '<span class="misconception-badge">⚠️ Misconception</span>'
                            : ""
                    }
                </div>
            </div>
        `
            )
            .join("");
    }

    displayMisconceptions(misconceptions) {
        const container = document.getElementById("misconceptionsList");

        if (!misconceptions || misconceptions.length === 0) {
            container.innerHTML =
                '<p style="text-align: center; color: green;">🎉 No misconceptions detected!</p>';
            return;
        }

        container.innerHTML = misconceptions
            .map(
                (item) => `
            <div class="misconception-item">
                <div class="misconception-header">
                    <span class="severity-badge severity-${item.severity}">
                        ${item.severity.toUpperCase()}
                    </span>
                    <span class="confidence">Confidence: ${(item.confidence * 100).toFixed(1)}%</span>
                </div>
                <div class="misconception-claim">Claim: "${item.text}"</div>
            </div>
        `
            )
            .join("");
    }

    displaySummary(summary) {
        const container = document.getElementById("summaryContainer");
        container.innerHTML = `
            <h3>📊 Analysis Summary</h3>
            <p>Total Misconceptions: ${summary.totalMisconceptions}</p>
            <p>High Severity: ${summary.highSeverity}</p>
            <p>Medium Severity: ${summary.mediumSeverity}</p>
            <p>Low Severity: ${summary.lowSeverity}</p>
            <h4>Overall Rating: ${summary.overallRating}</h4>
            <p>${summary.recommendation}</p>
        `;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    new YouTubeFactChecker();
});
