import streamlit as st
import requests
import json
import os
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
    ["Generate Podcast", "Scheduled Podcasts", "Recent Podcasts", "Podcast Details", "About"]
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
                
                # Show link to the podcast details
                if "podcast_id" in response:
                    podcast_id = response["podcast_id"]
                    st.markdown(f"[View Podcast Details](/?page=Podcast%20Details&podcast_id={podcast_id})")
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
                
                # Show link to the podcast details
                if "podcast_id" in response:
                    podcast_id = response["podcast_id"]
                    st.markdown(f"[View Podcast Details](/?page=Podcast%20Details&podcast_id={podcast_id})")
                    
                    # Add a button to view the podcast details
                    if st.button("View Podcast Details"):
                        st.session_state.page = "Podcast Details"
                        st.session_state.podcast_id = podcast_id
                        st.experimental_rerun()

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
    
    # Get all podcasts with status "scheduled"
    endpoint = "/podcasts?limit=50"
    if sport_filter != "All":
        endpoint += f"&sport={sport_filter}"
    
    all_podcasts = call_api(endpoint)
    
    if all_podcasts:
        # Filter to only scheduled podcasts
        scheduled_podcasts = [p for p in all_podcasts if p.get("status") == "scheduled"]
        
        if len(scheduled_podcasts) == 0:
            st.info("No scheduled podcasts found.")
        else:
            for podcast in scheduled_podcasts:
                # Format the podcast title
                title = podcast.get("title", "Untitled Podcast")
                sport = podcast.get("sport", "").upper()
                created_at = datetime.fromisoformat(podcast.get("created_at", "")).strftime("%Y-%m-%d %H:%M")
                
                # Get the scheduled time from metadata
                schedule_time = "Unknown"
                if podcast.get("metadata") and podcast["metadata"].get("schedule_time"):
                    schedule_time = datetime.fromisoformat(podcast["metadata"]["schedule_time"]).strftime("%Y-%m-%d %H:%M")
                
                with st.expander(f"{title} - Scheduled for {schedule_time}"):
                    # Display podcast details
                    st.write(f"**Sport:** {sport}")
                    st.write(f"**Created:** {created_at}")
                    
                    # Display metadata in JSON format
                    with st.expander("View Details"):
                        st.json(podcast)
                    
                    # Link to full details
                    st.markdown(f"[View Full Details](/?page=Podcast%20Details&podcast_id={podcast['id']})")
                    
                    # Cancel button
                    if "metadata" in podcast and "schedule_id" in podcast["metadata"]:
                        schedule_id = podcast["metadata"]["schedule_id"]
                        if st.button(f"Cancel", key=f"cancel_{podcast['id']}"):
                            cancel_response = call_api(f"/podcasts/scheduled/{schedule_id}", method="DELETE")
                            if cancel_response:
                                st.success("Scheduled podcast cancelled.")
                                st.experimental_rerun()

# Recent Podcasts page
elif page == "Recent Podcasts":
    st.header("Recent Podcasts")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        sport_filter = st.selectbox(
            "Filter by Sport", 
            ["All", "f1", "motogp"],
            index=0
        )
    with col2:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "generating", "completed", "failed"],
            index=0
        )
    with col3:
        limit = st.slider("Number of podcasts to show", 5, 50, 10)
    
    # Refresh button
    if st.button("Refresh List"):
        st.experimental_rerun()
    
    # Get recent podcasts from Supabase
    endpoint = f"/podcasts?limit={limit}"
    if sport_filter != "All":
        endpoint += f"&sport={sport_filter}"
    
    recent_podcasts = call_api(endpoint)
    
    if recent_podcasts:
        # Apply status filter if needed
        if status_filter != "All":
            recent_podcasts = [p for p in recent_podcasts if p.get("status") == status_filter]
        
        if len(recent_podcasts) == 0:
            st.info("No podcasts found matching your filters.")
        else:
            for podcast in recent_podcasts:
                # Format the podcast title and status
                title = podcast.get("title", "Untitled Podcast")
                status = podcast.get("status", "unknown")
                created_at = datetime.fromisoformat(podcast.get("created_at", "")).strftime("%Y-%m-%d %H:%M")
                
                # Create a card for each podcast with status-based styling
                status_color = {
                    "completed": "green",
                    "generating": "blue",
                    "scheduled": "orange",
                    "failed": "red"
                }.get(status, "gray")
                
                st.markdown(f"""
                <div style="padding: 10px; border-left: 5px solid {status_color}; margin-bottom: 10px;">
                    <h3>{title}</h3>
                    <p>Status: <span style="color: {status_color};">{status.upper()}</span> | Created: {created_at}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Show audio player if available
                    if podcast.get("audio_url"):
                        st.audio(podcast["audio_url"])
                    elif status == "generating":
                        st.info("Audio is being generated...")
                    elif status == "failed":
                        st.error("Audio generation failed.")
                    
                    # Show script snippet if available
                    if podcast.get("script_text"):
                        with st.expander("View Script Snippet"):
                            # Show the first 500 characters of the script
                            script_snippet = podcast["script_text"][:500] + "..." if len(podcast["script_text"]) > 500 else podcast["script_text"]
                            st.markdown(script_snippet)
                
                with col2:
                    # Button to view full details
                    if st.button("View Details", key=f"view_{podcast['id']}"):
                        st.session_state.page = "Podcast Details"
                        st.session_state.podcast_id = podcast["id"]
                        st.experimental_rerun()
                
                st.markdown("---")

# Podcast Details page
elif page == "Podcast Details":
    st.header("Podcast Details")
    
    # Get podcast ID from URL parameter or session state
    podcast_id = st.query_params.get("podcast_id", None)
    if not podcast_id and "podcast_id" in st.session_state:
        podcast_id = st.session_state.podcast_id
    
    if not podcast_id:
        # No podcast ID provided, show a form to enter one
        with st.form("podcast_id_form"):
            podcast_id_input = st.text_input("Enter Podcast ID")
            submit = st.form_submit_button("View Podcast")
            
            if submit and podcast_id_input:
                podcast_id = podcast_id_input
                st.session_state.podcast_id = podcast_id
                st.experimental_rerun()
    
    if podcast_id:
        # Get podcast details
        podcast = call_api(f"/podcasts/{podcast_id}")
        
        if podcast:
            # Display podcast info
            title = podcast.get("title", "Untitled Podcast")
            status = podcast.get("status", "unknown")
            
            # Show podcast title and status with color coding
            status_color = {
                "completed": "green",
                "generating": "blue",
                "scheduled": "orange",
                "failed": "red"
            }.get(status, "gray")
            
            st.markdown(f"# {title}")
            st.markdown(f"<h3>Status: <span style='color: {status_color};'>{status.upper()}</span></h3>", unsafe_allow_html=True)
            
            # Show metadata
            sport = podcast.get("sport", "").upper()
            event_id = podcast.get("event_id", "N/A")
            episode_type = podcast.get("episode_type", "N/A")
            created_at = datetime.fromisoformat(podcast.get("created_at", "")).strftime("%Y-%m-%d %H:%M")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Sport:** {sport}")
                st.markdown(f"**Event:** {event_id}")
            with col2:
                st.markdown(f"**Episode Type:** {episode_type}")
                st.markdown(f"**Created:** {created_at}")
            with col3:
                if podcast.get("duration"):
                    duration_min = podcast["duration"] // 60
                    duration_sec = podcast["duration"] % 60
                    st.markdown(f"**Duration:** {duration_min}m {duration_sec}s")
            
            # Audio player if available
            if podcast.get("audio_url"):
                st.subheader("Listen")
                st.audio(podcast["audio_url"])
                
                # Download button for audio
                st.markdown(f"[Download Audio]({podcast['audio_url']})", unsafe_allow_html=True)
            
            # Script if available
            if podcast.get("script_text"):
                st.subheader("Podcast Script")
                with st.expander("View Full Script", expanded=True):
                    st.markdown(podcast["script_text"])
                
                # Download button for script
                if podcast.get("script_url"):
                    st.markdown(f"[Download Script]({podcast['script_url']})", unsafe_allow_html=True)
            
            # Get podcast generation logs
            logs = call_api(f"/podcasts/{podcast_id}/logs")
            
            if logs:
                st.subheader("Generation Logs")
                with st.expander("View Generation Logs"):
                    # Sort logs by timestamp
                    logs.sort(key=lambda x: x.get("timestamp", ""), reverse=False)
                    
                    for log in logs:
                        # Format the log entry with color based on level
                        agent = log.get("agent_name", "system")
                        message = log.get("message", "")
                        timestamp = datetime.fromisoformat(log.get("timestamp", "")).strftime("%H:%M:%S")
                        level = log.get("level", "info")
                        
                        level_color = {
                            "info": "blue",
                            "warning": "orange",
                            "error": "red",
                            "debug": "gray"
                        }.get(level, "black")
                        
                        st.markdown(f"<span style='color: gray;'>[{timestamp}]</span> <span style='color: purple;'>{agent}</span>: <span style='color: {level_color};'>{message}</span>", unsafe_allow_html=True)
            
            # Show raw data in expandable section
            with st.expander("View Raw Data"):
                st.json(podcast)
            
            # Refresh button
            if st.button("Refresh"):
                st.experimental_rerun()
        else:
            st.error(f"Podcast with ID {podcast_id} not found.")

# About page
elif page == "About":
    st.header("About DopCast")
    
    st.markdown("""
    ## AI-Powered Motorsport Podcasts
    
    DopCast is a platform that uses multiple AI agents to generate engaging podcasts about motorsport events.
    Each agent has a specific role in the content creation pipeline, working together to deliver timely and insightful audio content for fans.
    
    ### How It Works
    
    1. **Research Agent** gathers information about motorsport events
    2. **Content Planning Agent** structures the podcast episode
    3. **Script Generation Agent** creates natural, conversational scripts
    4. **Voice Synthesis Agent** converts scripts to realistic speech
    5. **Audio Production Agent** adds music, effects, and polish
    
    All of this is orchestrated by the **Coordination Agent**, which manages the workflow and ensures quality output.
    
    ### Technologies Used
    
    - Python for the backend
    - Streamlit for this web interface
    - FastAPI for the REST API
    - OpenAI GPT models for content generation
    - Supabase for database and storage
    """)
    
    st.image("https://via.placeholder.com/800x200?text=DopCast", use_column_width=True)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("© 2025 DopCast AI")
st.sidebar.markdown("Version 0.1.0")
