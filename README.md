# 🏎️ F1 Race Strategist - Pit Wall AI

> **Real-time multimodal AI agent for Formula 1 race strategy analysis**
>
> Built for the [Gemini Live Agent Challenge](https://gemini-live-agent-challenge.devpost.com/)

[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-Deployed-4285F4?logo=googlecloud)](https://cloud.google.com)
[![Gemini](https://img.shields.io/badge/Gemini-Live%20API-8E75B2?logo=google)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 Project Overview

**Pit Wall AI** is a Live Agent that acts as your personal F1 race strategist, bringing the pit wall experience to every fan. Using Google's Gemini Live API, it can:

- 🎤 **HEAR**: Listen to your race strategy questions in real-time
- 👁️ **SEE**: Analyze timing screens, telemetry data, and race footage
- 🔊 **SPEAK**: Provide instant strategic recommendations like a race engineer

### Why F1 + AI?

Formula 1 race strategy happens in split seconds. Tire choices, pit windows, weather decisions - all require instant analysis. This agent brings professional-grade strategy insights to every fan, making complex data accessible through natural conversation.

---

## 🏆 Hackathon Track: Live Agents 🗣️

This project is built for the **Live Agents** track, featuring:

- ✅ Real-time voice interaction (can be interrupted)
- ✅ Vision-enabled analysis of race data
- ✅ Context-aware strategic recommendations
- ✅ Built with Gemini Live API
- ✅ Hosted on Google Cloud Run

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud account with billing enabled
- Gemini API key ([Get one here](https://ai.google.dev/))

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/mrehan0516/F1-analytics.git
cd F1-analytics

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your Google API key

# 5. Run the application
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8080

# 6. Open in browser
# Navigate to http://localhost:8080
```

### Docker Deployment

```bash
# Build the image
docker build -t f1-strategist-agent .

# Run the container
docker run -p 8080:8080 -e GOOGLE_API_KEY=your-key f1-strategist-agent
```

---

## ☁️ Google Cloud Deployment

### Automated Deployment (Recommended)

```bash
# Set your project ID
export GOOGLE_CLOUD_PROJECT=your-project-id

# Run the deployment script
chmod +x deployment/deploy.sh
./deployment/deploy.sh
```

### Manual Deployment Steps

1. **Enable APIs**:
```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com aiplatform.googleapis.com
```

2. **Build and Deploy**:
```bash
gcloud builds submit --config cloudbuild.yaml
```

3. **Access Your Service**:
```bash
gcloud run services describe f1-strategist-agent --region us-central1 --format='value(status.url)'
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │   Voice Input   │  │   Text Chat     │  │   Image Upload          │  │
│  │   (Microphone)  │  │   (Keyboard)    │  │   (Timing/Telemetry)    │  │
│  └────────┬────────┘  └────────┬────────┘  └───────────┬─────────────┘  │
│           │                    │                       │                 │
└───────────┼────────────────────┼───────────────────────┼─────────────────┘
            │                    │                       │
            ▼                    ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        FASTAPI BACKEND                                   │
│                     (Google Cloud Run)                                   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    WebSocket Handler                             │   │
│  │              (Real-time bidirectional communication)             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │  /api/live       │  │  /api/chat       │  │  /api/analyze    │      │
│  │  (WebSocket)     │  │  (REST)          │  │  (REST + Upload) │      │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘      │
│           │                     │                      │                 │
│           └─────────────────────┴──────────────────────┘                 │
│                                 │                                        │
│                                 ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              F1 RACE STRATEGIST AGENT                            │   │
│  │  ┌─────────────────────────────────────────────────────────┐    │   │
│  │  │               System Prompt: "Pit Wall AI"               │    │   │
│  │  │  - F1 Strategy Expert (tires, pits, weather)            │    │   │
│  │  │  - Race Engineer Communication Style                     │    │   │
│  │  │  - Real-time Decision Making                             │    │   │
│  │  └─────────────────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                 │                                        │
└─────────────────────────────────┼────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      GOOGLE AI SERVICES                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                   GEMINI LIVE API                                │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │   │
│  │  │ Audio Input  │  │ Vision Input │  │ Multimodal Generation │  │   │
│  │  │ (Real-time)  │  │ (Images)     │  │ (Text + Audio Output) │  │   │
│  │  └──────────────┘  └──────────────┘  └───────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  Model: gemini-2.0-flash-exp                                            │
│  Features: Live streaming, interruption handling, multimodal I/O        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
F1-analytics/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   └── f1_strategist.py      # Core agent with Gemini Live API
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py               # FastAPI application
│   └── utils/
│       └── __init__.py
├── config/
│   ├── __init__.py
│   └── settings.py               # Configuration management
├── frontend/
│   └── index.html                # Demo UI
├── deployment/
│   └── deploy.sh                 # Automated deployment script
├── tests/
│   ├── __init__.py
│   └── test_f1_strategist.py     # Unit tests
├── .env.example                  # Environment template
├── .gitignore
├── Dockerfile                    # Container configuration
├── cloudbuild.yaml               # CI/CD configuration
├── requirements.txt              # Python dependencies
├── LICENSE
└── README.md
```

---

## 🛠️ Technologies Used

| Technology | Purpose |
|------------|---------|
| **Google Gemini Live API** | Real-time multimodal AI (voice, vision, text) |
| **Google Cloud Run** | Serverless container deployment |
| **Google Cloud Build** | CI/CD pipeline |
| **FastAPI** | High-performance Python web framework |
| **WebSockets** | Real-time bidirectional communication |
| **Docker** | Containerization |

---

## 🎮 API Endpoints

### Health Check
```bash
GET /health
# Returns: { "status": "healthy", "agent": "F1 Race Strategist - Pit Wall AI" }
```

### Chat (Text)
```bash
POST /api/chat
Content-Type: application/json

{
  "message": "What tire strategy for Monaco?",
  "history": []
}
```

### Analyze Image
```bash
POST /api/analyze
Content-Type: multipart/form-data

file: <image_file>
prompt: "Analyze this timing screen"
```

### Live Session (WebSocket)
```javascript
// Connect
const ws = new WebSocket('wss://your-service.run.app/api/live');

// Send text
ws.send(JSON.stringify({ type: 'text', data: 'What tires next?' }));

// Send audio (base64)
ws.send(JSON.stringify({ type: 'audio', data: base64AudioData }));

// Receive responses
ws.onmessage = (event) => {
  const { type, data } = JSON.parse(event.data);
  // type: 'text' or 'audio'
};
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

---

## 📹 Demo Video

*[Link to 4-minute demo video showing:]*
1. Real-time voice interaction with the agent
2. Image analysis of F1 timing screens
3. Strategic recommendations in action
4. Google Cloud deployment proof

---

## 🔐 Security Considerations

- API keys are stored in environment variables, never in code
- Google Cloud IAM for service authentication
- CORS configured for production domains
- Input validation on all endpoints

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Google for the Gemini Live API and Cloud services
- The F1 community for inspiration
- Devpost for hosting the Gemini Live Agent Challenge

---

## 📧 Contact

**Rehan** - Built with ❤️ for the Gemini Live Agent Challenge

---

*This project was created for the Gemini Live Agent Challenge hackathon (#GeminiLiveAgentChallenge)*
