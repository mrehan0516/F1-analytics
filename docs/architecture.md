# F1 Pit Wall AI - Architecture Documentation

## System Overview

The F1 Pit Wall AI is a real-time voice-enabled AI agent built on Google's Gemini Live API. It provides F1 race strategy assistance through natural voice conversation.

## Architecture Layers

### 1. Presentation Layer
- **Demo Web Interface**: HTML5/JS single-page application
- **Voice Capture**: Web Audio API and MediaRecorder
- **Real-time Updates**: WebSocket connection for bidirectional streaming

### 2. Application Layer
- **FastAPI Server**: Async Python web framework
- **WebSocket Handler**: Manages real-time voice sessions
- **REST API**: Traditional HTTP endpoints for data queries
- **Session Manager**: Tracks active agent connections

### 3. Agent Layer
- **F1 Strategist Agent**: Core AI agent implementation
- **Gemini Live Integration**: Connection to Gemini 2.0 Flash
- **State Machine**: Manages agent connection states
- **Response Streaming**: Handles incremental audio/text output

### 4. Data Layer
- **F1 Data Service**: Interface to F1 telemetry and race data
- **FastF1 Integration**: Historical race data library
- **Strategy Engine**: Pit stop timing algorithms
- **Cache Layer**: Local caching for F1 data

### 5. Infrastructure Layer
- **Google Cloud Run**: Serverless container hosting
- **Secret Manager**: API key storage
- **Cloud Logging**: Centralized logging
- **Container Registry**: Docker image storage

## Data Flow

```
User Voice Input
      │
      ▼
Browser MediaRecorder
      │
      ▼
WebSocket Connection ──► FastAPI Server
                              │
                              ▼
                        Agent Session
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
            F1 Data Service    Gemini Live API
                    │                   │
                    └─────────┬─────────┘
                              │
                              ▼
                      Response Stream
                              │
                              ▼
                    WebSocket Response
                              │
                              ▼
                    Browser Audio Playback
```

## Key Design Decisions

1. **WebSocket over HTTP**: Real-time voice requires low-latency bidirectional communication
2. **Async Python**: High concurrency for multiple simultaneous users
3. **Session-based Agents**: Each user gets dedicated agent instance for conversation context
4. **Terraform IaC**: Reproducible infrastructure deployments
5. **Serverless Architecture**: Auto-scaling, cost-efficient deployment

## Security Considerations

- API keys stored in Google Secret Manager
- HTTPS enforced for all connections
- CORS configured for allowed origins
- No sensitive data logged

## Scalability

- Cloud Run auto-scales 0-10 instances
- Each instance handles 80 concurrent connections
- Stateless design enables horizontal scaling
- F1 data cached locally for performance
