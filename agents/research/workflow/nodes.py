"""
Node functions for the Research Agent LangGraph workflow.
Each function represents a node in the research workflow graph.
"""

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..tools.web_scraper import WebScraperTool
from ..tools.data_processor import DataProcessorTool
from ..tools.entity_extractor import EntityExtractorTool
from ..tools.youtube_transcript_tool import YouTubeTranscriptTool
from ..memory.cache_memory import CacheMemory
from ..memory.entity_memory import EntityMemory
from ..memory.research_memory import ResearchMemory

from .state import ResearchState

# Configure logging
logger = logging.getLogger(__name__)

# Initialize tools and memory components
# These will be properly initialized in the initialize_research node
web_scraper = None
data_processor = None
entity_extractor = None
youtube_transcript_tool = None
cache_memory = None
entity_memory = None
research_memory = None

def initialize_research(state: ResearchState) -> Dict[str, Any]:
    """
    Initialize the research workflow.

    Args:
        state: Current state

    Returns:
        Updated state
    """
    global web_scraper, data_processor, entity_extractor, youtube_transcript_tool, cache_memory, entity_memory, research_memory

    logger.info("Initializing research workflow")

    try:
        input_data = state["input_data"]
        sport = input_data.get("sport", "f1")
        event_type = input_data.get("event_type", "latest")
        event_id = input_data.get("event_id")
        force_refresh = input_data.get("force_refresh", False)

        # Set up data directories
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        output_dir = os.path.join(base_dir, "output")
        data_dir = os.path.join(output_dir, "data")
        cache_dir = os.path.join(data_dir, "cache")
        memory_dir = os.path.join(data_dir, "memory")

        # Ensure directories exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(memory_dir, exist_ok=True)

        # Initialize tools
        web_scraper = WebScraperTool(data_dir)
        data_processor = DataProcessorTool(data_dir)
        entity_extractor = EntityExtractorTool()
        youtube_transcript_tool = YouTubeTranscriptTool(data_dir)

        # Initialize memory components
        cache_memory = CacheMemory(cache_dir)
        entity_memory = EntityMemory(memory_dir)
        research_memory = ResearchMemory(memory_dir)

        # Create cache key
        cache_key = f"{sport}_{event_type}_{event_id if event_id else 'latest'}"

        # Check cache if not forcing refresh
        if not force_refresh:
            cached_data = cache_memory.get(cache_key)
            if cached_data:
                logger.info(f"Using cached data for {cache_key}")
                return {
                    "research_report": cached_data,
                    "config": {
                        "sport": sport,
                        "event_type": event_type,
                        "event_id": event_id,
                        "cache_key": cache_key,
                        "from_cache": True
                    }
                }

        # Set up configuration for the workflow
        config = {
            "sport": sport,
            "event_type": event_type,
            "event_id": event_id,
            "cache_key": cache_key,
            "from_cache": False,
            "tried_fallback": False,
            "sources": get_sources_for_sport(sport)
        }

        return {"config": config}

    except Exception as e:
        logger.error(f"Error initializing research: {e}", exc_info=True)
        return {"error_info": f"Research initialization failed: {str(e)}"}

def collect_data(state: ResearchState) -> Dict[str, Any]:
    """
    Collect data from sources.

    Args:
        state: Current state

    Returns:
        Updated state with collected data
    """
    logger.info("Collecting data from sources")

    try:
        config = state.get("config", {})
        sport = config.get("sport", "f1")
        event_type = config.get("event_type", "latest")
        event_id = config.get("event_id")
        sources = config.get("sources", [])

        # Check if this is a fallback attempt
        is_fallback = "tried_fallback" in config and not config["tried_fallback"]
        if is_fallback:
            logger.info("Using fallback data collection")
            config["tried_fallback"] = True

            # Use mock data for fallback
            collected_data = web_scraper.get_mock_data(sport, event_type)

            return {
                "collected_data": collected_data,
                "config": config
            }

        # Regular data collection
        import asyncio
        collected_data = asyncio.run(web_scraper.scrape_sources(sources, sport, event_type, event_id))

        return {
            "collected_data": collected_data,
            "config": config
        }

    except Exception as e:
        logger.error(f"Error collecting data: {e}", exc_info=True)
        return {"error_info": f"Data collection failed: {str(e)}"}

def collect_youtube_transcripts(state: ResearchState) -> Dict[str, Any]:
    """
    Collect YouTube video transcripts related to the research topic.

    Args:
        state: Current state

    Returns:
        Updated state with YouTube transcript data
    """
    logger.info("Collecting YouTube transcripts")

    try:
        config = state.get("config", {})
        sport = config.get("sport", "f1")
        event_type = config.get("event_type", "latest")
        event_id = config.get("event_id")

        # Create search query based on sport and event
        search_query = f"{sport} {event_type}"
        if event_id:
            search_query += f" {event_id}"

        # Add additional context for better search results
        if event_type == "race":
            search_query += " highlights interview podcast"
        elif event_type == "qualifying":
            search_query += " qualifying highlights analysis"
        elif event_type == "practice":
            search_query += " practice session analysis"
        else:
            search_query += " latest news analysis"

        logger.info(f"YouTube search query: {search_query}")

        # Check if this is a mock/test environment
        is_mock = config.get("tried_fallback", False)

        # Make sure the YouTube transcript tool is initialized
        if youtube_transcript_tool is None:
            logger.warning("YouTube transcript tool not initialized, initializing now")
            # Get the data directory from the config
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            output_dir = os.path.join(base_dir, "output")
            data_dir = os.path.join(output_dir, "data")
            os.makedirs(data_dir, exist_ok=True)

            from ..tools.youtube_transcript_tool import YouTubeTranscriptTool
            youtube_transcript_tool = YouTubeTranscriptTool(data_dir)

        if is_mock:
            # Use mock data for testing
            youtube_data = youtube_transcript_tool.get_mock_transcripts(sport, event_type)
            logger.info(f"Using mock YouTube transcript data")
        else:
            # Get real YouTube transcripts
            youtube_data = youtube_transcript_tool.search_and_get_transcripts(search_query, sport)
            logger.info(f"Found {len(youtube_data)} YouTube videos with transcripts")

        # Add to state
        return {
            "youtube_data": youtube_data,
            "config": config
        }

    except Exception as e:
        logger.error(f"Error collecting YouTube transcripts: {e}", exc_info=True)
        # Don't fail the whole workflow if YouTube collection fails
        return {
            "youtube_data": [],
            "config": state.get("config", {})
        }

def process_data(state: ResearchState) -> Dict[str, Any]:
    """
    Process collected data.

    Args:
        state: Current state

    Returns:
        Updated state with processed data
    """
    logger.info("Processing collected data")

    try:
        collected_data = state.get("collected_data", [])
        youtube_data = state.get("youtube_data", [])
        config = state.get("config", {})
        sport = config.get("sport", "f1")
        event_type = config.get("event_type", "latest")

        # Process the web data
        processed_data = data_processor.process_data(collected_data, sport, event_type)

        # Add YouTube data to processed data
        if youtube_data:
            logger.info(f"Adding {len(youtube_data)} YouTube videos to processed data")

            # Create a YouTube section in the processed data
            if "sections" not in processed_data:
                processed_data["sections"] = []

            youtube_section = {
                "title": "YouTube Content",
                "source": "YouTube",
                "content_type": "video_transcripts",
                "items": []
            }

            # Process each YouTube video
            for video in youtube_data:
                # Extract key information
                video_item = {
                    "title": video.get("title", "Untitled Video"),
                    "url": video.get("url", ""),
                    "channel": video.get("channel", "Unknown Channel"),
                    "transcript": video.get("transcript", ""),
                    "published_at": video.get("published_at", ""),
                    "video_id": video.get("video_id", "")
                }
                youtube_section["items"].append(video_item)

            # Add the YouTube section to processed data
            processed_data["sections"].append(youtube_section)

        return {"processed_data": processed_data}

    except Exception as e:
        logger.error(f"Error processing data: {e}", exc_info=True)
        return {"error_info": f"Data processing failed: {str(e)}"}

def extract_entities(state: ResearchState) -> Dict[str, Any]:
    """
    Extract entities from processed data.

    Args:
        state: Current state

    Returns:
        Updated state with extracted entities
    """
    logger.info("Extracting entities from processed data")

    try:
        processed_data = state.get("processed_data", {})
        config = state.get("config", {})
        sport = config.get("sport", "f1")

        # Extract entities
        articles = processed_data.get("articles", [])
        entities = entity_extractor.extract_entities(articles, sport)

        # Update entity memory
        entity_memory.update_entities(entities, sport)

        # Categorize topics
        topics = entity_extractor.categorize_topics(articles)

        # Combine entities and topics
        entity_data = {
            "entities": entities,
            "topics": topics
        }

        return {"entities": entity_data}

    except Exception as e:
        logger.error(f"Error extracting entities: {e}", exc_info=True)
        return {"error_info": f"Entity extraction failed: {str(e)}"}

def analyze_trends(state: ResearchState) -> Dict[str, Any]:
    """
    Analyze trends in the data.

    Args:
        state: Current state

    Returns:
        Updated state with trend analysis
    """
    logger.info("Analyzing trends in the data")

    try:
        processed_data = state.get("processed_data", {})
        entities = state.get("entities", {})
        config = state.get("config", {})
        sport = config.get("sport", "f1")

        # Identify key stories
        key_stories = identify_key_stories(processed_data, entities)

        # Identify trends
        trends = identify_trends(processed_data, entities, sport)

        # Update research memory
        for story in key_stories:
            research_memory.add_key_story(sport, story)

        for trend in trends:
            research_memory.add_trend(sport, trend)

        # Combine trends and key stories
        trend_data = {
            "key_stories": key_stories,
            "trends": trends
        }

        return {"trends": trend_data}

    except Exception as e:
        logger.error(f"Error analyzing trends: {e}", exc_info=True)
        return {"error_info": f"Trend analysis failed: {str(e)}"}

def generate_report(state: ResearchState) -> Dict[str, Any]:
    """
    Generate the final research report.

    Args:
        state: Current state

    Returns:
        Updated state with research report
    """
    logger.info("Generating research report")

    try:
        processed_data = state.get("processed_data", {})
        entities = state.get("entities", {})
        trends = state.get("trends", {})
        config = state.get("config", {})
        sport = config.get("sport", "f1")
        event_type = config.get("event_type", "latest")
        event_id = config.get("event_id")
        cache_key = config.get("cache_key")

        # If we have no processed data (due to fallback failure), create minimal report
        if not processed_data:
            report = {
                "sport": sport,
                "event_type": event_type,
                "event_id": event_id,
                "generated_at": datetime.now().isoformat(),
                "status": "limited",
                "message": "Limited data available",
                "articles": [],
                "entities": {},
                "trends": [],
                "key_stories": []
            }
        else:
            # Create comprehensive report
            report = {
                "sport": sport,
                "event_type": event_type,
                "event_id": event_id,
                "generated_at": datetime.now().isoformat(),
                "status": "complete",
                "article_count": processed_data.get("article_count", 0),
                "articles": processed_data.get("articles", []),
                "entities": entities.get("entities", {}),
                "topics": entities.get("topics", {}),
                "trends": trends.get("trends", []),
                "key_stories": trends.get("key_stories", []),
                "metadata": processed_data.get("metadata", {})
            }

            # Add race-specific data if available
            if "race_data" in processed_data:
                report["race_data"] = processed_data["race_data"]

        # Update cache
        if cache_key:
            cache_memory.set(cache_key, report)

        # If this is an identified event, store in research memory
        if event_id:
            research_memory.add_event_data(sport, event_type, event_id, report)

        return {"research_report": report}

    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        return {"error_info": f"Report generation failed: {str(e)}"}

# Helper functions

def get_sources_for_sport(sport: str) -> List[str]:
    """
    Get the list of sources for a sport.

    Args:
        sport: Sport type

    Returns:
        List of source URLs
    """
    sources = {
        "f1": [
            "https://www.formula1.com/",
            "https://www.autosport.com/f1/",
            "https://www.motorsport.com/f1/",
            "https://www.espn.com/f1/",
            "https://www.skysports.com/f1",
            "https://www.bbc.com/sport/formula1",
            "https://www.racefans.net/"
        ],
        "motogp": [
            "https://www.motogp.com/",
            "https://www.autosport.com/motogp/",
            "https://www.motorsport.com/motogp/",
            "https://www.crash.net/motogp",
            "https://www.gpone.com/",
            "https://www.motorcyclenews.com/sport/motogp/"
        ]
    }

    return sources.get(sport, [])

def identify_key_stories(processed_data: Dict[str, Any], entities: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Identify key stories from the processed data.

    Args:
        processed_data: Processed data
        entities: Extracted entities

    Returns:
        List of key stories
    """
    key_stories = []

    # Get articles and topics
    articles = processed_data.get("articles", [])
    topics = entities.get("topics", {})

    # Identify race results stories
    for idx in topics.get("race_results", [])[:2]:
        if idx < len(articles):
            key_stories.append({
                "type": "race_results",
                "title": articles[idx].get("title", ""),
                "summary": articles[idx].get("summary", ""),
                "url": articles[idx].get("url", ""),
                "source": articles[idx].get("source", "")
            })

    # Identify controversy stories
    for idx in topics.get("controversy", [])[:2]:
        if idx < len(articles):
            key_stories.append({
                "type": "controversy",
                "title": articles[idx].get("title", ""),
                "summary": articles[idx].get("summary", ""),
                "url": articles[idx].get("url", ""),
                "source": articles[idx].get("source", "")
            })

    # Identify technical stories
    for idx in topics.get("technical", [])[:1]:
        if idx < len(articles):
            key_stories.append({
                "type": "technical",
                "title": articles[idx].get("title", ""),
                "summary": articles[idx].get("summary", ""),
                "url": articles[idx].get("url", ""),
                "source": articles[idx].get("source", "")
            })

    return key_stories

def identify_trends(processed_data: Dict[str, Any], entities: Dict[str, Any], sport: str) -> List[Dict[str, Any]]:
    """
    Identify trends from the processed data.

    Args:
        processed_data: Processed data
        entities: Extracted entities
        sport: Sport type

    Returns:
        List of trends
    """
    trends = []

    # Get entity data
    entity_data = entities.get("entities", {})

    # Identify driver/rider trends
    people = entity_data.get("people", [])
    if people:
        # Get the most mentioned people
        top_people = people[:3]

        for person in top_people:
            trends.append({
                "type": "person_trend",
                "name": person.get("name", ""),
                "mention_count": person.get("count", 0),
                "sport": sport
            })

    # Identify team trends
    teams = entity_data.get("teams", [])
    if teams:
        # Get the most mentioned teams
        top_teams = teams[:2]

        for team in top_teams:
            trends.append({
                "type": "team_trend",
                "name": team.get("name", ""),
                "mention_count": team.get("count", 0),
                "sport": sport
            })

    # Identify track trends
    tracks = entity_data.get("tracks", [])
    if tracks:
        # Get the most mentioned tracks
        top_tracks = tracks[:1]

        for track in top_tracks:
            trends.append({
                "type": "track_trend",
                "name": track.get("name", ""),
                "mention_count": track.get("count", 0),
                "sport": sport
            })

    return trends
