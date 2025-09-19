class YouTubeFactChecker {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        const analyzeBtn = document.getElementById('analyzeBtn');
        const urlInput = document.getElementById('youtubeUrl');
        const tabs = document.querySelectorAll('.tab');

        analyzeBtn.addEventListener('click', () => this.analyzeVideo());
        urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.analyzeVideo();
        });

        tabs.forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
        });
    }

    extractVideoId(url) {
        const regex = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/;
        const match = url.match(regex);
        return match ? match[1] : null;
    }

    showError(message) {
        const errorDiv = document.getElementById('errorMessage');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }

    hideError() {
        document.getElementById('errorMessage').style.display = 'none';
    }

    showLoading() {
        document.getElementById('loading').style.display = 'block';
        document.getElementById('analyzeBtn').disabled = true;
    }

    hideLoading() {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('analyzeBtn').disabled = false;
    }

    async analyzeVideo() {
        const url = document.getElementById('youtubeUrl').value.trim();
        if (!url) {
            this.showError('Please enter a YouTube URL');
            return;
        }

        const videoId = this.extractVideoId(url);
        if (!videoId) {
            this.showError('Please enter a valid YouTube URL');
            return;
        }

        this.hideError();
        this.showLoading();

        try {
            const response = await fetch(`${this.apiBaseUrl}/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const data = await response.json();
            this.displayResults(data);
            document.getElementById('resultsSection').style.display = 'block';

        } catch (error) {
            console.error('Analysis failed:', error);
            this.showError('Analysis failed. Please try again later.');
        } finally {
            this.hideLoading();
        }
    }

    displayResults(data) {
        this.displayTranscript(data.transcript);
        this.displayMisconceptions(data.misconceptions);
    }

    displayTranscript(transcript) {
        const container = document.getElementById('transcriptContainer');
        container.innerHTML = transcript.map(line => `
            <div class="transcript-line ${line.misinformation === 'MISINFORMATION' ? 'has-misconception' : ''}">
                <div class="timestamp">${this.formatTime(line.timestamp)}</div>
                <div class="text">
                    ${line.text}
                    ${line.misinformation === 'MISINFORMATION' ? '<span class="misconception-badge">Potential Misconception</span>' : ''}
                </div>
            </div>
        `).join('');
    }

    displayMisconceptions(misconceptions) {
        const container = document.getElementById('misconceptionsList');

        if (misconceptions.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #38a169; font-size: 1.1rem;">🎉 No misconceptions detected!</p>';
            return;
        }

        container.innerHTML = misconceptions.map(item => `
            <div class="misconception-item">
                <div class="misconception-header">
                    <span class="severity-badge severity-high">HIGH</span>
                    <span class="timestamp">At ${this.formatTime(item.timestamp)}</span>
                </div>
                <div class="misconception-claim">${item.text}</div>
                <div class="fact-check">
                    <div class="fact-check-header">⚠️ Predicted as Misinformation</div>
                    <p>Confidence: ${(item.score * 100).toFixed(2)}%</p>
                </div>
            </div>
        `).join('');
    }

    switchTab(tabName) {
        document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(`${tabName}-content`).classList.add('active');
    }

    formatTime(seconds) {
        const min = Math.floor(seconds / 60);
        const sec = Math.floor(seconds % 60).toString().padStart(2, '0');
        return `${min}:${sec}`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new YouTubeFactChecker();
});
