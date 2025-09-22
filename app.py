"""
Streamlit frontend for the Disaster Response AI system.
Interactive dashboard for emergency management and coordination.
"""

import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import time
from typing import Dict, List, Any, Optional

# Page configuration
st.set_page_config(
    page_title="🚨 Disaster Response AI Dashboard",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #d32f2f;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #f5f5f5 0%, #ffffff 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #d32f2f;
        margin: 0.5rem 0;
    }
    .risk-critical { border-left-color: #d32f2f !important; }
    .risk-high { border-left-color: #ff9800 !important; }
    .risk-moderate { border-left-color: #ffc107 !important; }
    .risk-low { border-left-color: #4caf50 !important; }
    .alert-banner {
        background-color: #d32f2f;
        color: white;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        font-weight: bold;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    }
    </style>
    """, unsafe_allow_html=True)

load_css()

# Configuration
@st.cache_data
def load_config():
    """Load configuration from secrets or environment."""
    try:
        # Try to load from Streamlit secrets
        backend_url = st.secrets.get("backend_url", "https://nbws-disaster-response.hf.space")
        default_lat = st.secrets.get("default_lat", 40.7128)
        default_lon = st.secrets.get("default_lon", -74.0060)
    except:
        # Fallback to defaults
        backend_url = "https://nbws-disaster-response.hf.space"
        default_lat = 40.7128
        default_lon = -74.0060
    
    return {
        "backend_url": backend_url,
        "default_location": {"lat": default_lat, "lon": default_lon},
        "refresh_interval": 30  # seconds
    }

config = load_config()

# API client functions
class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
    
    def get(self, endpoint: str, params: Dict = None) -> Dict:
        """Make GET request to API."""
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API Error: {response.status_code}"}
        except requests.RequestException as e:
            return {"error": f"Connection Error: {str(e)}"}
    
    def post(self, endpoint: str, data: Dict = None) -> Dict:
        """Make POST request to API."""
        try:
            response = requests.post(f"{self.base_url}{endpoint}", json=data, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API Error: {response.status_code}"}
        except requests.RequestException as e:
            return {"error": f"Connection Error: {str(e)}"}

api = APIClient(config["backend_url"])

# Utility functions
def get_risk_color(risk_score: float) -> str:
    """Get color based on risk score."""
    if risk_score >= 8.5:
        return "red"
    elif risk_score >= 7.0:
        return "orange"
    elif risk_score >= 5.0:
        return "yellow"
    elif risk_score >= 3.0:
        return "lightgreen"
    else:
        return "green"

def format_timestamp(timestamp_str: str) -> str:
    """Format timestamp for display."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except:
        return timestamp_str

# Session state initialization
if 'active_incident' not in st.session_state:
    st.session_state.active_incident = None
if 'monitoring_active' not in st.session_state:
    st.session_state.monitoring_active = False
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()
if 'map_center' not in st.session_state:
    st.session_state.map_center = config["default_location"]

# Main app layout
def main():
    """Main application function."""
    
    # Header
    st.markdown('<h1 class="main-header">🚨 Disaster Response AI Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Control Panel")
        
        # System status
        with st.expander("📊 System Status", expanded=True):
            health_data = api.get("/health/detailed")
            if "error" not in health_data:
                st.success("✅ System Operational")
                st.metric("CPU Usage", f"{health_data.get('system_metrics', {}).get('cpu_percent', 0):.1f}%")
                st.metric("Memory Usage", f"{health_data.get('system_metrics', {}).get('memory_percent', 0):.1f}%")
            else:
                st.error("❌ System Error")
        
        # Location selection
        st.subheader("📍 Location Settings")
        col1, col2 = st.columns(2)
        with col1:
            lat = st.number_input("Latitude", value=st.session_state.map_center["lat"], 
                                min_value=-90.0, max_value=90.0, step=0.001, format="%.6f")
        with col2:
            lon = st.number_input("Longitude", value=st.session_state.map_center["lon"],
                                min_value=-180.0, max_value=180.0, step=0.001, format="%.6f")
        
        if st.button("📍 Update Location"):
            st.session_state.map_center = {"lat": lat, "lon": lon}
            st.rerun()
        
        # Monitoring controls
        st.subheader("📡 Monitoring")
        if st.button("▶️ Start Monitoring" if not st.session_state.monitoring_active else "⏸️ Stop Monitoring"):
            st.session_state.monitoring_active = not st.session_state.monitoring_active
            st.rerun()
        
        if st.session_state.monitoring_active:
            st.success("🟢 Monitoring Active")
        else:
            st.info("🔴 Monitoring Inactive")
        
        # Emergency actions
        st.subheader("🚨 Emergency Actions")
        incident_type = st.selectbox(
            "Incident Type",
            ["earthquake", "flood", "fire", "storm", "general"]
        )
        severity = st.slider("Severity", 1, 10, 5)
        
        if st.button("🚨 Trigger Emergency Assessment"):
            trigger_emergency_assessment(lat, lon, incident_type, severity)
        
        # Auto-refresh
        auto_refresh = st.checkbox("🔄 Auto-refresh (30s)", value=True)
        if auto_refresh:
            time.sleep(1)
            st.rerun()

    # Main content area
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🗺️ Situation Map", 
        "📊 Risk Assessment", 
        "🚛 Resources", 
        "📢 Communications", 
        "📈 Analytics"
    ])
    
    with tab1:
        render_situation_map()
    
    with tab2:
        render_risk_assessment()
    
    with tab3:
        render_resource_management()
    
    with tab4:
        render_communications()
    
    with tab5:
        render_analytics()

def render_situation_map():
    """Render the main situation awareness map."""
    st.header("🗺️ Real-time Situation Map")
    
    # Map controls
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        show_weather = st.checkbox("🌤️ Weather", value=True)
    with col2:
        show_social = st.checkbox("📱 Social Reports", value=True)
    with col3:
        show_earthquakes = st.checkbox("🌍 Earthquakes", value=True)
    with col4:
        show_risk_zones = st.checkbox("⚠️ Risk Zones", value=True)
    
    # Create map
    center_lat = st.session_state.map_center["lat"]
    center_lon = st.session_state.map_center["lon"]
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles="OpenStreetMap"
    )
    
    # Add weather data
    if show_weather:
        weather_data = api.get("/api/v1/monitoring/weather", {
            "lat": center_lat, 
            "lon": center_lon,
            "include_alerts": True
        })
        
        if "error" not in weather_data:
            add_weather_to_map(m, weather_data, center_lat, center_lon)
    
    # Add social media reports
    if show_social:
        social_data = api.get("/api/v1/monitoring/social/reports", {
            "lat": center_lat,
            "lon": center_lon,
            "radius_km": 50
        })
        
        if "error" not in social_data:
            add_social_reports_to_map(m, social_data)
    
    # Add earthquake data
    if show_earthquakes:
        earthquake_data = api.get("/api/v1/monitoring/earthquakes", {"timeframe": "all_day"})
        
        if "error" not in earthquake_data:
            add_earthquakes_to_map(m, earthquake_data)
    
    # Add risk zones (mock data for demo)
    if show_risk_zones:
        add_risk_zones_to_map(m, center_lat, center_lon)
    
    # Display map
    map_data = st_folium(m, width=700, height=500, returned_objects=["last_object_clicked"])
    
    # Handle map clicks
    if map_data["last_object_clicked"]:
        clicked_lat = map_data["last_object_clicked"]["lat"]
        clicked_lon = map_data["last_object_clicked"]["lng"]
        st.info(f"📍 Clicked: {clicked_lat:.4f}, {clicked_lon:.4f}")

def add_weather_to_map(m, weather_data, lat, lon):
    """Add weather information to map."""
    current = weather_data.get("current_weather", {})
    alerts = weather_data.get("alerts", [])
    
    # Weather station marker
    popup_text = f"""
    <b>Weather Station</b><br>
    Temperature: {current.get('temperature', 'N/A')}°C<br>
    Conditions: {current.get('description', 'N/A')}<br>
    Wind: {current.get('wind_speed', 'N/A')} m/s<br>
    Humidity: {current.get('humidity', 'N/A')}%
    """
    
    folium.Marker(
        [lat, lon],
        popup=popup_text,
        icon=folium.Icon(color="blue", icon="cloud")
    ).add_to(m)
    
    # Weather alerts
    for alert in alerts:
        if alert.get("severity") == "high":
            color = "red"
        elif alert.get("severity") == "medium":
            color = "orange"
        else:
            color = "yellow"
        
        folium.Circle(
            [lat, lon],
            radius=5000,  # 5km radius
            popup=f"Alert: {alert.get('event', 'Weather Alert')}",
            color=color,
            fill=True,
            opacity=0.3
        ).add_to(m)

def add_social_reports_to_map(m, social_data):
    """Add social media reports to map."""
    reports = social_data.get("disaster_reports", [])
    
    for report in reports[:10]:  # Limit to 10 reports
        # Mock coordinates (in production, extract from report or geocode)
        lat = social_data.get("location", {}).get("lat", 0) + (hash(report.get("id", "")) % 20 - 10) * 0.01
        lon = social_data.get("location", {}).get("lon", 0) + (hash(report.get("id", "")) % 20 - 10) * 0.01
        
        credibility = report.get("credibility_score", 5)
        if credibility >= 8:
            color = "green"
        elif credibility >= 6:
            color = "orange"
        else:
            color = "red"
        
        popup_text = f"""
        <b>Social Report</b><br>
        Credibility: {credibility:.1f}/10<br>
        Urgency: {report.get('urgency_level', 'N/A')}<br>
        Text: {report.get('text', 'N/A')[:100]}...
        """
        
        folium.Marker(
            [lat, lon],
            popup=popup_text,
            icon=folium.Icon(color=color, icon="comment")
        ).add_to(m)

def add_earthquakes_to_map(m, earthquake_data):
    """Add earthquake data to map."""
    earthquakes = earthquake_data.get("earthquakes", [])
    
    for eq in earthquakes[:10]:  # Limit to 10 earthquakes
        if "latitude" in eq and "longitude" in eq:
            magnitude = eq.get("magnitude", 0)
            
            # Size and color based on magnitude
            if magnitude >= 6.0:
                color = "red"
                radius = 20000
            elif magnitude >= 4.0:
                color = "orange"
                radius = 10000
            else:
                color = "yellow"
                radius = 5000
            
            popup_text = f"""
            <b>Earthquake</b><br>
            Magnitude: {magnitude}<br>
            Location: {eq.get('location', 'Unknown')}<br>
            Time: {format_timestamp(eq.get('time', ''))}
            """
            
            folium.Circle(
                [eq["latitude"], eq["longitude"]],
                radius=radius,
                popup=popup_text,
                color=color,
                fill=True,
                opacity=0.5
            ).add_to(m)

def add_risk_zones_to_map(m, center_lat, center_lon):
    """Add risk assessment zones to map."""
    # Mock risk zones for demonstration
    risk_zones = [
        {"lat": center_lat + 0.05, "lon": center_lon + 0.05, "risk": 8.5, "name": "Zone A"},
        {"lat": center_lat - 0.03, "lon": center_lon + 0.02, "risk": 6.2, "name": "Zone B"},
        {"lat": center_lat + 0.02, "lon": center_lon - 0.04, "risk": 4.1, "name": "Zone C"},
        {"lat": center_lat - 0.05, "lon": center_lon - 0.03, "risk": 7.8, "name": "Zone D"}
    ]
    
    for zone in risk_zones:
        color = get_risk_color(zone["risk"])
        
        popup_text = f"""
        <b>{zone['name']}</b><br>
        Risk Score: {zone['risk']}/10<br>
        Risk Level: {get_risk_level(zone['risk'])}
        """
        
        folium.Circle(
            [zone["lat"], zone["lon"]],
            radius=3000,  # 3km radius
            popup=popup_text,
            color=color,
            fill=True,
            opacity=0.4
        ).add_to(m)

def get_risk_level(risk_score):
    """Get risk level from score."""
    if risk_score >= 8.5:
        return "Critical"
    elif risk_score >= 7.0:
        return "High"
    elif risk_score >= 5.0:
        return "Moderate"
    elif risk_score >= 3.0:
        return "Low"
    else:
        return "Minimal"

def render_risk_assessment():
    """Render risk assessment dashboard."""
    st.header("📊 Risk Assessment Dashboard")
    
    # Current risk metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🌡️ Overall Risk", "6.5/10", "↑ 0.8")
    with col2:
        st.metric("👥 Population at Risk", "15,000", "↑ 2,000")
    with col3:
        st.metric("🏠 Critical Zones", "2", "↑ 1")
    with col4:
        st.metric("⏱️ Last Update", "2 min ago", "")
    
    # Risk assessment details
    st.subheader("🎯 Zone Risk Analysis")
    
    # Mock risk data
    risk_data = {
        "Zone A": {"risk": 8.5, "population": 5000, "factors": ["High wind exposure", "Older buildings"]},
        "Zone B": {"risk": 6.2, "population": 3000, "factors": ["Moderate elevation", "Good evacuation routes"]},
        "Zone C": {"risk": 4.1, "population": 4000, "factors": ["Low hazard exposure", "Modern infrastructure"]},
        "Zone D": {"risk": 7.8, "population": 3000, "factors": ["Flood zone", "Limited access routes"]}
    }
    
    # Risk chart
    zones = list(risk_data.keys())
    scores = [risk_data[zone]["risk"] for zone in zones]
    populations = [risk_data[zone]["population"] for zone in zones]
    
    fig = px.bar(
        x=zones,
        y=scores,
        title="Risk Scores by Zone",
        labels={"x": "Zone", "y": "Risk Score"},
        color=scores,
        color_continuous_scale=["green", "yellow", "orange", "red"]
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Risk details table
    st.subheader("📋 Detailed Risk Assessment")
    
    risk_df = pd.DataFrame([
        {
            "Zone": zone,
            "Risk Score": data["risk"],
            "Risk Level": get_risk_level(data["risk"]),
            "Population": data["population"],
            "Key Factors": ", ".join(data["factors"])
        }
        for zone, data in risk_data.items()
    ])
    
    st.dataframe(risk_df, use_container_width=True)
    
    # Recommendations
    st.subheader("💡 AI Recommendations")
    
    high_risk_zones = [zone for zone, data in risk_data.items() if data["risk"] >= 7.0]
    
    if high_risk_zones:
        st.error(f"🚨 **High Risk Alert**: Zones {', '.join(high_risk_zones)} require immediate attention")
        
        recommendations = [
            "Deploy emergency response teams to high-risk zones",
            "Issue evacuation advisories for Zone A residents", 
            "Activate emergency shelters in safe areas",
            "Monitor weather conditions for changes",
            "Coordinate with local authorities for traffic management"
        ]
        
        for i, rec in enumerate(recommendations, 1):
            st.write(f"{i}. {rec}")

def render_resource_management():
    """Render resource management dashboard."""
    st.header("🚛 Resource Management")
    
    # Resource status
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🚓 Emergency Services", "12 units", "3 deployed")
    with col2:
        st.metric("🏥 Medical Teams", "8 teams", "2 on standby")
    with col3:
        st.metric("🏠 Shelters Open", "5 facilities", "320 capacity available")
    with col4:
        st.metric("🚗 Evacuation Routes", "8 routes", "2 at capacity")
    
    # Resource allocation
    st.subheader("📍 Resource Allocation")
    
    allocation_data = [
        {"Resource": "Fire Dept Unit 1", "Type": "Fire Service", "Location": "Zone A", "Status": "En Route", "ETA": "8 min"},
        {"Resource": "Ambulance 3", "Type": "Medical", "Location": "Zone D", "Status": "On Scene", "ETA": "-"},
        {"Resource": "Police Unit 5", "Type": "Security", "Location": "Zone B", "Status": "Available", "ETA": "15 min"},
        {"Resource": "Rescue Team Alpha", "Type": "Search & Rescue", "Location": "Headquarters", "Status": "Standby", "ETA": "25 min"}
    ]
    
    allocation_df = pd.DataFrame(allocation_data)
    st.dataframe(allocation_df, use_container_width=True)
    
    # Evacuation routes
    st.subheader("🛣️ Evacuation Routes")
    
    route_data = [
        {"Route": "Route 1", "From": "Zone A", "To": "Shelter North", "Capacity": "500/hour", "Status": "Clear", "Time": "25 min"},
        {"Route": "Route 2", "From": "Zone B", "To": "Shelter East", "Capacity": "300/hour", "Status": "Heavy Traffic", "Time": "35 min"},
        {"Route": "Route 3", "From": "Zone C", "To": "Shelter West", "Capacity": "400/hour", "Status": "Clear", "Time": "20 min"},
        {"Route": "Route 4", "From": "Zone D", "To": "Shelter South", "Capacity": "200/hour", "Status": "Blocked", "Time": "N/A"}
    ]
    
    route_df = pd.DataFrame(route_data)
    st.dataframe(route_df, use_container_width=True)
    
    # Shelter status
    st.subheader("🏠 Emergency Shelters")
    
    shelter_data = [
        {"Shelter": "Community Center North", "Capacity": 200, "Occupied": 45, "Available": 155, "Status": "Open"},
        {"Shelter": "High School East", "Capacity": 150, "Occupied": 78, "Available": 72, "Status": "Open"},
        {"Shelter": "Recreation Center West", "Capacity": 100, "Occupied": 23, "Available": 77, "Status": "Open"},
        {"Shelter": "Sports Complex South", "Capacity": 180, "Occupied": 0, "Available": 180, "Status": "Standby"}
    ]
    
    shelter_df = pd.DataFrame(shelter_data)
    
    # Shelter utilization chart
    fig = px.bar(
        shelter_df,
        x="Shelter",
        y=["Occupied", "Available"],
        title="Shelter Capacity Utilization",
        barmode="stack"
    )
    st.plotly_chart(fig, use_container_width=True)

def render_communications():
    """Render communications dashboard."""
    st.header("📢 Communications Center")
    
    # Communication status
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📨 Messages Sent", "47", "↑ 12")
    with col2:
        st.metric("👥 People Reached", "15,230", "↑ 3,450")
    with col3:
        st.metric("⏰ Pending Approvals", "3", "")
    with col4:
        st.metric("📱 Social Media Reach", "8,900", "↑ 2,100")
    
    # Draft new communication
    st.subheader("✍️ Draft New Communication")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        message_type = st.selectbox(
            "Message Type",
            ["Public Alert", "Responder Brief", "Social Media Post", "Stakeholder Update"]
        )
        
        target_audience = st.multiselect(
            "Target Audience",
            ["General Public", "Emergency Services", "Government Officials", "Media", "NGOs"],
            default=["General Public"]
        )
        
        urgency = st.select_slider(
            "Urgency Level",
            options=["Low", "Medium", "High", "Critical"],
            value="Medium"
        )
    
    with col2:
        if st.button("🤖 Generate AI Draft"):
            st.success("AI draft generated!")
        
        if st.button("📤 Send for Approval"):
            st.info("Sent for approval")
    
    # Message composition
    st.text_area(
        "Message Content",
        value="Emergency weather alert: Strong winds expected in the area. Residents should secure loose objects and avoid outdoor activities. Monitor official channels for updates.",
        height=150
    )
    
    # Pending approvals
    st.subheader("⏳ Pending Approvals")
    
    approval_data = [
        {
            "ID": "MSG-001", 
            "Type": "Public Alert", 
            "Subject": "High Wind Warning", 
            "Urgency": "High",
            "Created": "10 min ago",
            "Status": "Pending Review"
        },
        {
            "ID": "MSG-002",
            "Type": "Social Media",
            "Subject": "Evacuation Route Update",
            "Urgency": "Medium", 
            "Created": "25 min ago",
            "Status": "Pending Review"
        }
    ]
    
    for msg in approval_data:
        with st.expander(f"{msg['ID']} - {msg['Subject']} ({msg['Urgency']})"):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**Type:** {msg['Type']}")
                st.write(f"**Created:** {msg['Created']}")
                st.write(f"**Status:** {msg['Status']}")
            with col2:
                if st.button("✅ Approve", key=f"approve_{msg['ID']}"):
                    st.success(f"Approved {msg['ID']}")
            with col3:
                if st.button("❌ Reject", key=f"reject_{msg['ID']}"):
                    st.error(f"Rejected {msg['ID']}")
    
    # Recent communications
    st.subheader("📋 Recent Communications")
    
    recent_data = [
        {"Time": "15:45", "Type": "Public Alert", "Subject": "Weather Advisory", "Reach": "5,200", "Status": "Sent"},
        {"Time": "15:30", "Type": "Responder Brief", "Subject": "Deployment Orders", "Reach": "45", "Status": "Sent"},
        {"Time": "15:15", "Type": "Social Media", "Subject": "Safety Reminder", "Reach": "2,800", "Status": "Sent"}
    ]
    
    recent_df = pd.DataFrame(recent_data)
    st.dataframe(recent_df, use_container_width=True)

def render_analytics():
    """Render analytics dashboard."""
    st.header("📈 Analytics & Insights")
    
    # Time series data (mock)
    dates = pd.date_range(start="2024-01-01", end="2024-01-07", freq="D")
    incidents = [3, 5, 2, 8, 6, 4, 7]
    risk_scores = [4.2, 5.8, 3.1, 7.6, 6.2, 4.9, 6.5]
    
    # Incidents over time
    st.subheader("📊 Incidents Over Time")
    
    fig = px.line(
        x=dates,
        y=incidents,
        title="Daily Incident Count",
        labels={"x": "Date", "y": "Number of Incidents"}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Risk trends
    st.subheader("⚠️ Risk Score Trends")
    
    fig = px.line(
        x=dates,
        y=risk_scores,
        title="Average Daily Risk Score",
        labels={"x": "Date", "y": "Risk Score"}
    )
    fig.add_hline(y=7.0, line_dash="dash", line_color="red", annotation_text="High Risk Threshold")
    st.plotly_chart(fig, use_container_width=True)
    
    # Response time analysis
    st.subheader("⏱️ Response Time Analysis")
    
    response_data = {
        "Service Type": ["Fire", "Medical", "Police", "Rescue"],
        "Avg Response Time (min)": [8.5, 12.3, 6.7, 15.2],
        "Target Time (min)": [10, 8, 8, 20]
    }
    
    fig = px.bar(
        response_data,
        x="Service Type",
        y=["Avg Response Time (min)", "Target Time (min)"],
        title="Response Time vs Targets",
        barmode="group"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Performance metrics
    st.subheader("🎯 Performance Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("False Alarm Rate", "12%", "↓ 3%")
        st.metric("Detection Accuracy", "94%", "↑ 2%")
    
    with col2:
        st.metric("Avg Decision Time", "18 min", "↓ 5 min")
        st.metric("Resource Utilization", "78%", "↑ 8%")
    
    with col3:
        st.metric("Public Satisfaction", "4.2/5", "↑ 0.3")
        st.metric("Coverage Area", "95%", "↑ 2%")

def trigger_emergency_assessment(lat: float, lon: float, incident_type: str, severity: int):
    """Trigger emergency assessment."""
    try:
        response = api.post("/api/v1/trigger-assessment", {
            "location": {"lat": lat, "lon": lon},
            "incident_type": incident_type,
            "severity": severity
        })
        
        if "error" not in response:
            st.success("🚨 Emergency assessment triggered successfully!")
            st.session_state.active_incident = response
        else:
            st.error(f"Failed to trigger assessment: {response['error']}")
    
    except Exception as e:
        st.error(f"Error triggering assessment: {str(e)}")

# Run the app
if __name__ == "__main__":
    main()
