# 🏎️ F1 Pit Wall AI

> **Real-time Voice-Enabled Race Strategist powered by Google Gemini Live API**

[![Built for Gemini Live Agent Challenge](https://img.shields.io/badge/Hackathon-Gemini%20Live%20Agent%20Challenge-e10600?style=for-the-badge)](https://devpost.com)
[![Google Cloud](https://img.shields.io/badge/Deployed%20on-Google%20Cloud-4285F4?style=for-the-badge&logo=googlecloud)](https://cloud.google.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python)](https://python.org)

## 📋 Overview

**F1 Pit Wall AI** is a next-generation AI agent that brings the expertise of a Formula 1 race strategist directly to your fingertips through natural voice interaction. Built for the **Gemini Live Agent Challenge**, this project demonstrates the power of multimodal AI by combining:

- 🎙️ **Real-time Voice Interaction** - Talk naturally, get instant strategic advice
- 👁️ **Visual Analysis** - Share telemetry screenshots for detailed analysis  
- 📊 **Data-Driven Insights** - Powered by real F1 data and strategy algorithms
- ⚡ **Live Interruption Handling** - Natural conversation flow, just like real radio comms

### The Problem We Solve

F1 fans and amateur teams lack access to professional-grade race strategy assistance. Our AI acts as your personal Pit Wall engineer, helping you:
- Make optimal pit stop timing decisions
- Select the right tyre compound
- React to changing weather conditions
- Understand competitor strategies

---

## 🎥 Demo Video

> *[Link to 4-minute demonstration video]*

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           F1 PIT WALL AI ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐                                     ┌──────────────────┐  │
│  │   Frontend   │◄────── WebSocket (Real-time) ──────►│   Cloud Run      │  │
│  │   (React)    │                                     │   Backend        │  │
│  │              │         HTTP REST API               │   (FastAPI)      │  │
│  │  • Voice UI  │◄───────────────────────────────────►│                  │  │
│  │  • Chat      │                                     │  • Agent Logic   │  │
│  │  • Telemetry │                                     │  • F1 Service    │  │
│  └──────────────┘                                     │  • Strategy Algo │  │
│         │                                             └────────┬─────────┘  │
│         │                                                      │            │
│         │ Audio/Video Input                                    │            │
│         ▼                                                      ▼            │
│  ┌──────────────┐                                     ┌──────────────────┐  │
│  │   Browser    │                                     │   Gemini Live    │  │
│  │   APIs       │                                     │   API            │  │
│  │              │                                     │                  │  │
│  │  • MediaRec  │                                     │  • Voice I/O     │  │
│  │  • WebAudio  │                                     │  • Vision        │  │
│  │  • Canvas    │                                     │  • Text Gen      │  │
│  └──────────────┘                                     └──────────────────┘  │
│                                                                │            │
│                        ┌───────────────────────────────────────┘            │
│                        │                                                    │
│                        ▼                                                    │
│               ┌──────────────────┐      ┌──────────────────┐               │
│               │   Google Cloud   │      │   Secret Manager │               │
│               │   Logging        │      │   (API Keys)     │               │
│               └──────────────────┘      └──────────────────┘               │
│                                                                              │
│               ┌──────────────────────────────────────────────┐              │
│               │                  F1 DATA LAYER               │              │
│               │                                              │              │
│               │   FastF1 Library ──► Race Data Cache         │              │
│               │                                              │              │
│               │   • Telemetry    • Lap Times    • Weather    │              │
│               │   • Positions    • Tyre Data    • Strategy   │              │
│               └──────────────────────────────────────────────┘              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | HTML5/JavaScript | Voice capture, visualization |
| Backend | FastAPI + Python 3.11 | WebSocket server, API endpoints |
| AI Agent | Gemini 2.0 Flash + ADK | Voice interaction, strategy generation |
| F1 Data | FastF1 Library | Historical & simulated race data |
| Deployment | Cloud Run | Serverless, auto-scaling backend |
| IaC | Terraform | Infrastructure as code |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud account with billing enabled
- Gemini API key ([Get one here](https://aistudio.google.com/apikey))

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/mrehan0516/F1-analytics.git
cd F1-analytics

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY

# 5. Run the application
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8080

# 6. Open in browser
# http://localhost:8080/demo
```

### Docker

```bash
# Build and run with Docker
docker build -t f1-pit-wall-ai .
docker run -p 8080:8080 -e GOOGLE_API_KEY=your-key f1-pit-wall-ai
```

---

## ☁️ Google Cloud Deployment

### Option 1: Automated Script

```bash
# Set your project ID
export GOOGLE_CLOUD_PROJECT=your-project-id

# Run deployment script
chmod +x deployment/deploy.sh
./deployment/deploy.sh
```

### Option 2: Terraform (Infrastructure as Code)

```bash
cd deployment

# Initialize Terraform
terraform init

# Create terraform.tfvars with your values
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars

# Plan and apply
terraform plan
terraform apply
```

### Google Cloud Services Used

- **Cloud Run** - Serverless container hosting
- **Container Registry** - Docker image storage
- **Secret Manager** - Secure API key storage
- **Cloud Logging** - Application monitoring
- **Vertex AI** - Gemini API access

---

## 📡 API Reference

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/schedule` | GET | Get F1 race schedule |
| `/api/strategy` | POST | Analyze pit strategy |
| `/api/telemetry/{year}/{race}/{driver}` | GET | Get driver telemetry |
| `/demo` | GET | Interactive demo page |

### WebSocket

Connect to `/ws/{session_id}` for real-time voice interaction.

**Message Format:**
```json
// Send text
{"type": "text", "data": "Should we pit now?"}

// Send audio (base64)
{"type": "audio", "data": "base64...", "mime_type": "audio/webm"}

// Send image for analysis
{"type": "image", "data": "base64...", "mime_type": "image/jpeg", "prompt": "Analyze this telemetry"}
```

---

## 🎯 Features

### Core Capabilities

1. **Real-time Strategy Calls**
   - "Should we pit now?" → Instant recommendation with confidence level
   - Considers tyre wear, position, weather, competitor strategies

2. **Voice Interaction**
   - Natural conversation with interruption support
   - F1 radio-style communication persona
   - Energetic voice with racing expertise

3. **Visual Analysis**
   - Upload telemetry screenshots for analysis
   - Track position visualization
   - Sector-by-sector breakdown

4. **Weather Adaptation**
   - Rain detection triggers immediate strategy update
   - Intermediate/wet tyre recommendations
   - Track evolution analysis

### Technical Highlights

- **Gemini Live API** integration for streaming voice
- **WebSocket** real-time bidirectional communication  
- **FastF1** integration for authentic race data
- **Async Python** for high-performance I/O
- **Infrastructure as Code** with Terraform

---

## 📁 Project Structure

```
F1-analytics/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   └── f1_strategist.py    # Gemini Live API agent
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py             # FastAPI application
│   ├── services/
│   │   ├── __init__.py
│   │   └── f1_data_service.py  # F1 data processing
│   └── config.py               # Configuration settings
├── deployment/
│   ├── deploy.sh               # Cloud Run deployment script
│   ├── main.tf                 # Terraform infrastructure
│   └── terraform.tfvars.example
├── tests/
│   ├── test_api.py
│   └── test_f1_service.py
├── docs/
│   └── architecture.md
├── Dockerfile
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_f1_service.py -v
```

---

## 🔧 Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `GOOGLE_API_KEY` | Gemini API key | Required |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | Required for deployment |
| `GEMINI_MODEL` | Model to use | `gemini-2.0-flash-exp` |
| `PORT` | Server port | `8080` |
| `LOG_LEVEL` | Logging level | `INFO` |

---

## 📊 Judging Criteria Alignment

### Innovation & Multimodal UX (40%)
- ✅ Breaks the "text box" paradigm with voice-first interaction
- ✅ Agent can "See" (telemetry images), "Hear" (voice input), "Speak" (audio responses)
- ✅ Distinct F1 race engineer persona
- ✅ Live, context-aware, natural conversation flow

### Technical Implementation (30%)
- ✅ Uses Google GenAI SDK / Gemini Live API
- ✅ Hosted on Google Cloud (Cloud Run)
- ✅ Sound agent logic with strategy algorithms
- ✅ Graceful error handling
- ✅ Grounded in real F1 data (FastF1)

### Demo & Presentation (30%)
- ✅ Clear problem/solution definition
- ✅ Architecture diagram included
- ✅ Cloud deployment proof (see /health endpoint)
- ✅ Working software demonstration

---

## 📚 Resources & Learning

### Built With
- [Google Gemini Live API](https://ai.google.dev/docs/gemini_api/live)
- [Google ADK (Agent Development Kit)](https://github.com/google/adk)
- [FastAPI](https://fastapi.tiangolo.com/)
- [FastF1](https://docs.fastf1.dev/) - F1 Data Library

### Learnings
1. Gemini Live API enables truly conversational AI experiences
2. WebSocket is essential for real-time voice streaming
3. F1 strategy involves complex multi-variable optimization
4. Google Cloud Run provides excellent serverless container hosting

---

## 👨‍💻 Author

**Md. Rehan Arvi**

Built with ❤️ for the Gemini Live Agent Challenge

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🏆 Submission Checklist

- [x] **Text Description**: Project features and functionality documented
- [x] **Public Code Repository**: GitHub repo with full source code
- [x] **Spin-up Instructions**: Complete setup guide in README
- [x] **Architecture Diagram**: Visual system representation
- [x] **Google Cloud Deployment**: Cloud Run + Infrastructure as Code
- [ ] **Demo Video**: 4-minute demonstration (to be recorded)
- [x] **Uses Gemini Live API**: Core requirement met
- [x] **Hosted on Google Cloud**: Cloud Run deployment

---

*#GeminiLiveAgentChallenge*
