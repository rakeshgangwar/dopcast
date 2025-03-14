import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import time

# API configuration
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="DopCast - AI Motorsport Podcasts",
    page_icon="🎙️",
    layout="wide"
)

# Title and description
st.title("🎙️ DopCast")
st.subheader("AI-Powered Motorsport Podcasts")

st.markdown("""
    Generate engaging podcasts about MotoGP and Formula 1 using AI agents.
    Each podcast is created through a pipeline of specialized agents that handle research,
    content planning, script generation, voice synthesis, and audio production.
""")

# Sidebar navigation
page = st.sidebar.selectbox(
    "Navigation", 
    ["Generate Podcast", "Scheduled Podcasts", "Recent Podcasts", "About"]
)

# Function to call the API
def call_api(endpoint, method="GET", data=None):
    url = f"{API_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
            
        if response.status_code in [200, 201]:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None

# Generate Podcast page
if page == "Generate Podcast":
    st.header("Generate New Podcast")
    
    # Form for podcast generation
    with st.form("podcast_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            sport = st.selectbox("Sport", ["f1", "motogp"], index=0)
            trigger = st.selectbox("Trigger Type", [
                "manual", "race", "qualifying", "practice", "news"
            ], index=0)
            event_id = st.text_input("Event ID (optional)", "")
        
        with col2:
            episode_type = st.selectbox("Episode Type", [
                "race_review", "qualifying_analysis", "news_update", "technical_deep_dive"
            ], index=0)
            duration = st.slider("Target Duration (minutes)", 5, 60, 30)
            technical_level = st.select_slider(
                "Technical Detail Level",
                options=["basic", "mixed", "advanced"],
                value="mixed"
            )
        
        # Schedule options
        schedule_podcast = st.checkbox("Schedule for later")
        if schedule_podcast:
            schedule_date = st.date_input("Schedule Date", datetime.now().date())
            schedule_time = st.time_input("Schedule Time", datetime.now().time())
        
        # Custom parameters
        st.subheader("Advanced Settings")
        show_advanced = st.checkbox("Show advanced settings")
        
        custom_parameters = {}
        if show_advanced:
            with st.expander("Content Planning Settings"):
                host_count = st.slider("Number of Hosts", 1, 4, 2)
                content_tone = st.selectbox(
                    "Content Tone", 
                    ["conversational", "formal", "enthusiastic", "analytical"],
                    index=0
                )
                custom_parameters["content_planning"] = {
                    "host_count": host_count,
                    "content_tone": content_tone,
                    "duration": duration * 60  # Convert to seconds
                }
            
            with st.expander("Script Generation Settings"):
                script_style = st.selectbox(
                    "Script Style", 
                    ["conversational", "interview", "narrative", "debate"],
                    index=0
                )
                humor_level = st.select_slider(
                    "Humor Level",
                    options=["none", "light", "moderate", "heavy"],
                    value="moderate"
                )
                custom_parameters["script_generation"] = {
                    "script_style": script_style,
                    "humor_level": humor_level
                }
            
            with st.expander("Audio Settings"):
                audio_format = st.selectbox("Audio Format", ["mp3", "ogg", "wav"], index=0)
                custom_parameters["voice_synthesis"] = {
                    "audio_format": audio_format
                }
                custom_parameters["audio_production"] = {
                    "output_formats": [
                        {"format": audio_format, "bitrate": "192k"}
                    ]
                }
        
        # Always add episode type and technical level
        custom_parameters["episode_type"] = episode_type
        custom_parameters["technical_level"] = technical_level
        
        submit_button = st.form_submit_button("Generate Podcast")
    
    if submit_button:
        if schedule_podcast:
            # Schedule the podcast
            schedule_datetime = datetime.combine(schedule_date, schedule_time)
            data = {
                "sport": sport,
                "trigger": trigger,
                "schedule_time": schedule_datetime.isoformat(),
                "event_id": event_id if event_id else None,
                "custom_parameters": custom_parameters
            }
            response = call_api("/podcasts/schedule", method="POST", data=data)
            if response:
                st.success(f"Podcast scheduled for {schedule_datetime}")
                st.json(response)
        else:
            # Generate the podcast immediately
            data = {
                "sport": sport,
                "trigger": trigger,
                "event_id": event_id if event_id else None,
                "custom_parameters": custom_parameters
            }
            response = call_api("/podcasts/generate", method="POST", data=data)
            if response:
                st.success("Podcast generation started!")
                st.json(response)
                
                # Show a spinner while waiting for the podcast
                run_id = response.get("run_id")
                if run_id:
                    with st.spinner("Generating podcast... This may take several minutes."):
                        # Poll for status updates
                        status = "started"
                        while status in ["started", "running"]:
                            time.sleep(5)  # Check every 5 seconds
                            status_response = call_api(f"/podcasts/runs/{run_id}")
                            if status_response:
                                status = status_response.get("status", "unknown")
                                st.text(f"Current status: {status}")
                        
                        if status == "completed":
                            st.success("Podcast generated successfully!")
                            st.json(status_response)
                        else:
                            st.error(f"Podcast generation failed with status: {status}")

# Scheduled Podcasts page
elif page == "Scheduled Podcasts":
    st.header("Scheduled Podcasts")
    
    # Filter options
    sport_filter = st.selectbox(
        "Filter by Sport", 
        ["All", "f1", "motogp"],
        index=0
    )
    
    # Refresh button
    if st.button("Refresh List"):
        st.experimental_rerun()
    
    # Get scheduled podcasts
    endpoint = "/podcasts/scheduled"
    if sport_filter != "All":
        endpoint += f"?sport={sport_filter}"
    
    scheduled = call_api(endpoint)
    
    if scheduled:
        if len(scheduled) == 0:
            st.info("No scheduled podcasts found.")
        else:
            for run in scheduled:
                with st.expander(f"{run['sport'].upper()} - {run['trigger']} - {run['schedule_time']}"):
                    st.json(run)
                    if st.button(f"Cancel", key=f"cancel_{run['id']}"):
                        cancel_response = call_api(f"/podcasts/scheduled/{run['id']}", method="DELETE")
                        if cancel_response:
                            st.success("Scheduled podcast cancelled.")
                            st.experimental_rerun()

# Recent Podcasts page
elif page == "Recent Podcasts":
    st.header("Recent Podcasts")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        sport_filter = st.selectbox(
            "Filter by Sport", 
            ["All", "f1", "motogp"],
            index=0
        )
    with col2:
        limit = st.slider("Number of podcasts to show", 5, 50, 10)
    
    # Refresh button
    if st.button("Refresh List"):
        st.experimental_rerun()
    
    # Get recent podcasts
    endpoint = f"/podcasts/runs?limit={limit}"
    if sport_filter != "All":
        endpoint += f"&sport={sport_filter}"
    
    recent = call_api(endpoint)
    
    if recent:
        if len(recent) == 0:
            st.info("No recent podcasts found.")
        else:
            for run in recent:
                status = run.get("status", "unknown")
                if status == "completed":
                    icon = "✅"
                elif status == "failed":
                    icon = "❌"
                elif status == "running":
                    icon = "⏳"
                else:
                    icon = "❓"
                
                with st.expander(f"{icon} {run['sport'].upper()} - {run.get('episode_type', 'unknown')} - {run['started_at']}"):
                    st.json(run)
                    
                    # If completed, show download links
                    if status == "completed" and "result" in run and "audio_files" in run["result"]:
                        st.subheader("Download Podcast")
                        for audio_file in run["result"]["audio_files"]:
                            st.download_button(
                                f"Download {audio_file['format'].upper()}",
                                data=b"Placeholder",  # In a real app, this would be the actual file
                                file_name=audio_file["filename"],
                                mime=f"audio/{audio_file['format']}"
                            )

# About page
elif page == "About":
    st.header("About DopCast")
    
    st.markdown("""
        ## Overview
        
        DopCast is an innovative platform that uses AI agents to generate engaging podcasts about motorsport events.
        Each agent has a specific role in the content creation pipeline, working together to deliver timely and insightful audio content for fans.
        
        ## How It Works
        
        1. **Research Agent** gathers information about races, qualifying, and news
        2. **Content Planning Agent** structures the podcast episode
        3. **Script Generation Agent** writes natural, engaging dialogue
        4. **Voice Synthesis Agent** converts the script to realistic speech
        5. **Audio Production Agent** adds music, effects, and professional polish
        6. **Coordination Agent** orchestrates the entire process
        
        ## Features
        
        - Multi-agent system with specialized roles
        - Automated research and data collection
        - Natural-sounding voice synthesis
        - Regular podcast episodes following race weekends
        - Expandable to additional motorsports
    """)
    
    st.image("https://via.placeholder.com/800x400?text=DopCast+Architecture", caption="DopCast Architecture")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("© 2025 DopCast AI")
st.sidebar.markdown("Version 0.1.0")
