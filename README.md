---
title: Disaster Response AI API
emoji: 🚨
colorFrom: red
colorTo: orange
sdk: gradio
sdk_version: 4.7.1
app_file: app.py
pinned: false
license: mit
---

# 🚨 Disaster Response AI API

A multi-agent AI system that coordinates disaster response efforts by aggregating real-time weather, social media, and sensor data.

## 🎯 Features

- **Real-time Monitoring**: Weather alerts, social signals, seismic data
- **Risk Assessment**: AI-powered zone scoring with uncertainty quantification  
- **Resource Optimization**: Evacuation routes, shelter matching, task allocation
- **Communication**: Automated alerts with human approval workflow
- **Decision Support**: Precedent-based recommendations from vector knowledge base

## 🏗️ Architecture

The system uses a multi-agent architecture powered by CrewAI and Groq LLM:

- **Data Ingestion Agent**: Polls APIs, dedupes, geocodes incidents
- **Signal Triage Agent**: Classifies credibility, filters noise
- **Risk Scoring Agent**: Fuses hazard + exposure + vulnerability data
- **Resource Allocation Agent**: Optimizes routes, shelters, assignments
- **Communications Agent**: Drafts alerts, requires human approval

## 🔧 Tech Stack

- **LLM**: Groq (Llama3-70B) - Fast inference
- **Agents**: CrewAI framework  
- **Backend**: FastAPI
- **Vector DB**: Chroma (embedded)
- **Observability**: LangSmith tracing

## 🌐 APIs Integrated

- **OpenWeatherMap**: Weather alerts, forecasts
- **Twitter API v2**: Social monitoring
- **USGS Earthquake**: Real-time seismic data
- **OpenRouteService**: Routing and directions

## 📋 API Endpoints

### Health & Monitoring
- `GET /health` - Health check
- `GET /api/v1/monitoring/weather` - Weather data
- `GET /api/v1/monitoring/social/reports` - Social media reports
- `GET /api/v1/monitoring/earthquakes` - Earthquake data

### Risk Assessment
- `POST /api/v1/risk/assess` - Comprehensive risk assessment
- `GET /api/v1/risk/zones/scores` - Zone risk scores
- `GET /api/v1/risk/vulnerability/analysis` - Vulnerability analysis

### Resource Management
- `POST /api/v1/resources/allocate` - Resource allocation
- `GET /api/v1/resources/available` - Available resources
- `GET /api/v1/resources/shelters` - Emergency shelters
- `GET /api/v1/resources/evacuation-routes` - Evacuation routes

### Communications
- `POST /api/v1/communications/plan` - Create communication plan
- `POST /api/v1/communications/send` - Send communications
- `GET /api/v1/communications/pending-approvals` - Pending approvals

## 🚀 Quick Start

1. **Set Environment Variables** (in HF Spaces Settings):
   ```
   GROQ_API_KEY=your_groq_key
   OPENWEATHER_API_KEY=your_openweather_key  
   OPENROUTESERVICE_KEY=your_openrouteservice_key
   TWITTER_BEARER_TOKEN=your_twitter_token (optional)
   LANGSMITH_API_KEY=your_langsmith_key (optional)
   ```

2. **Test the API**:
   ```bash
   curl https://your-space-name.hf.space/health
   ```

3. **View Documentation**:
   Visit `https://your-space-name.hf.space/docs` for interactive API docs

## 📊 Demo Usage

### Weather Monitoring
```python
import requests

# Get weather data for New York
response = requests.get(
    "https://your-space-name.hf.space/api/v1/monitoring/weather",
    params={"lat": 40.7128, "lon": -74.0060, "include_alerts": True}
)
weather_data = response.json()
```

### Risk Assessment
```python
# Assess risk for multiple zones
zones = [
    {
        "id": "zone_1",
        "center_coordinates": {"lat": 40.7128, "lon": -74.0060},
        "population": 5000
    }
]

response = requests.post(
    "https://your-space-name.hf.space/api/v1/risk/assess",
    json={
        "location": {"lat": 40.7128, "lon": -74.0060},
        "zones": zones,
        "incident_type": "storm"
    }
)
risk_assessment = response.json()
```

### Resource Allocation
```python
# Find available resources
response = requests.get(
    "https://your-space-name.hf.space/api/v1/resources/available",
    params={
        "lat": 40.7128, 
        "lon": -74.0060, 
        "radius_km": 25,
        "resource_types": "personnel,vehicle"
    }
)
resources = response.json()
```

## 🔒 Security

- API key authentication for external services
- Rate limiting implemented
- Input validation on all endpoints
- CORS configured for web access

## 📈 Monitoring

- Health checks available at `/health`
- Detailed system metrics at `/health/detailed`
- LangSmith integration for agent tracing (if configured)

## 🤝 Contributing

This is part of the Disaster Response AI project. For the full system including Streamlit frontend, visit: [GitHub Repository Link]

## 📄 License

MIT License - Built for disaster preparedness and response coordination.

---

**Note**: This API is designed for emergency management and disaster response coordination. Always follow official emergency procedures and protocols.

