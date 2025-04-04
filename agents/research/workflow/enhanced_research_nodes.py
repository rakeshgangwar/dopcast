"""
Enhanced nodes for the Research Agent workflow.
"""

import logging
import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..tools.enhanced_exa_search_tool import EnhancedExaSearchTool
from ..tools.enhanced_youtube_transcript_tool import EnhancedYouTubeTranscriptTool
from ..tools.enhanced_firecrawl_tool import EnhancedFirecrawlTool
from ..tools.research_summarizer_tool import ResearchSummarizerTool
from .state import ResearchState

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize tools
exa_search_tool = EnhancedExaSearchTool()
youtube_transcript_tool = EnhancedYouTubeTranscriptTool()
firecrawl_tool = EnhancedFirecrawlTool()
research_summarizer_tool = ResearchSummarizerTool()

async def initialize_research(state: ResearchState) -> Dict[str, Any]:
    """
    Initialize the research process.
    
    Args:
        state: Current state
        
    Returns:
        Updated state
    """
    try:
        logger.info("Initializing research process")
        
        # Extract input data
        input_data = state["input_data"]
        sport = input_data.get("sport", "f1")
        event_type = input_data.get("event_type", "race")
        event_id = input_data.get("event_id")
        force_refresh = input_data.get("force_refresh", False)
        
        # Set up configuration
        config = {
            "sport": sport,
            "event_type": event_type,
            "event_id": event_id,
            "force_refresh": force_refresh,
            "started_at": datetime.now().isoformat()
        }
        
        # Create output directories
        os.makedirs(os.path.join("output", "research"), exist_ok=True)
        
        logger.info(f"Research initialized for {sport} {event_type}")
        
        return {"config": config}
    
    except Exception as e:
        logger.error(f"Error initializing research: {e}", exc_info=True)
        return {"error_info": f"Research initialization failed: {str(e)}"}

async def collect_web_data(state: ResearchState) -> Dict[str, Any]:
    """
    Collect data from web sources using Exa search.
    
    Args:
        state: Current state
        
    Returns:
        Updated state with web search results
    """
    try:
        logger.info("Collecting web data")
        
        # Check for errors
        if "error_info" in state and state["error_info"]:
            return {}
        
        # Extract configuration
        config = state["config"]
        sport = config["sport"]
        event_type = config["event_type"]
        event_id = config["event_id"]
        
        # Generate search query based on sport and event type
        base_query = f"{event_type}"
        if event_id:
            base_query += f" {event_id}"
        
        # Perform multiple searches with different queries
        exa_results = await exa_search_tool.search_with_multiple_queries(
            base_query=base_query,
            sport=sport,
            event_type=event_type,
            event_id=event_id
        )
        
        logger.info(f"Collected {len(exa_results.get('results', []))} web search results")
        
        return {"exa_results": exa_results}
    
    except Exception as e:
        logger.error(f"Error collecting web data: {e}", exc_info=True)
        return {"error_info": f"Web data collection failed: {str(e)}"}

async def collect_youtube_data(state: ResearchState) -> Dict[str, Any]:
    """
    Collect data from YouTube videos.
    
    Args:
        state: Current state
        
    Returns:
        Updated state with YouTube transcript results
    """
    try:
        logger.info("Collecting YouTube data")
        
        # Check for errors
        if "error_info" in state and state["error_info"]:
            return {}
        
        # Extract configuration
        config = state["config"]
        sport = config["sport"]
        event_type = config["event_type"]
        event_id = config["event_id"]
        
        # Generate search query based on sport and event type
        query = f"{event_type}"
        if event_id:
            query += f" {event_id}"
        
        # Search for YouTube videos and extract transcripts
        youtube_results = await youtube_transcript_tool.search_and_extract_transcripts(
            query=query,
            sport=sport
        )
        
        logger.info(f"Collected {len(youtube_results.get('transcripts', []))} YouTube transcripts")
        
        return {"youtube_results": youtube_results}
    
    except Exception as e:
        logger.error(f"Error collecting YouTube data: {e}", exc_info=True)
        return {"error_info": f"YouTube data collection failed: {str(e)}"}

async def collect_targeted_web_data(state: ResearchState) -> Dict[str, Any]:
    """
    Collect data from targeted web sources using Firecrawl.
    
    Args:
        state: Current state
        
    Returns:
        Updated state with targeted web crawl results
    """
    try:
        logger.info("Collecting targeted web data")
        
        # Check for errors
        if "error_info" in state and state["error_info"]:
            return {}
        
        # Extract configuration
        config = state["config"]
        sport = config["sport"]
        event_type = config["event_type"]
        
        # Extract URLs from Exa search results
        exa_results = state.get("exa_results", {})
        urls = [result.get("url") for result in exa_results.get("results", []) if result.get("url")]
        
        # Crawl targeted URLs
        firecrawl_results = await firecrawl_tool.crawl_targeted_urls(
            urls=urls,
            sport=sport,
            event_type=event_type
        )
        
        logger.info(f"Collected {len(firecrawl_results.get('results', []))} targeted web articles")
        
        return {"firecrawl_results": firecrawl_results}
    
    except Exception as e:
        logger.error(f"Error collecting targeted web data: {e}", exc_info=True)
        return {"error_info": f"Targeted web data collection failed: {str(e)}"}

async def process_research_data(state: ResearchState) -> Dict[str, Any]:
    """
    Process and analyze all collected research data.
    
    Args:
        state: Current state
        
    Returns:
        Updated state with processed research data
    """
    try:
        logger.info("Processing research data")
        
        # Check for errors
        if "error_info" in state and state["error_info"]:
            return {}
        
        # Extract configuration and results
        config = state["config"]
        sport = config["sport"]
        event_type = config["event_type"]
        event_id = config["event_id"]
        
        exa_results = state.get("exa_results", {})
        youtube_results = state.get("youtube_results", {})
        firecrawl_results = state.get("firecrawl_results", {})
        
        # Generate topic from event type and ID
        topic = f"{event_type}"
        if event_id:
            topic += f" {event_id}"
        
        # Create comprehensive summary
        comprehensive_summary = await research_summarizer_tool.create_comprehensive_summary(
            exa_results=exa_results,
            youtube_results=youtube_results,
            firecrawl_results=firecrawl_results,
            topic=topic,
            sport=sport,
            event_type=event_type
        )
        
        logger.info("Processed research data and created comprehensive summary")
        
        return {"comprehensive_summary": comprehensive_summary}
    
    except Exception as e:
        logger.error(f"Error processing research data: {e}", exc_info=True)
        return {"error_info": f"Research data processing failed: {str(e)}"}

async def generate_research_report(state: ResearchState) -> Dict[str, Any]:
    """
    Generate the final research report.
    
    Args:
        state: Current state
        
    Returns:
        Updated state with research report
    """
    try:
        logger.info("Generating research report")
        
        # Check for errors
        if "error_info" in state and state["error_info"]:
            return {}
        
        # Extract configuration and results
        config = state["config"]
        sport = config["sport"]
        event_type = config["event_type"]
        event_id = config["event_id"]
        
        exa_results = state.get("exa_results", {})
        youtube_results = state.get("youtube_results", {})
        firecrawl_results = state.get("firecrawl_results", {})
        comprehensive_summary = state.get("comprehensive_summary", {})
        
        # Create the research report
        research_report = {
            "sport": sport,
            "event_type": event_type,
            "event_id": event_id,
            "research_date": datetime.now().isoformat(),
            "sources": {
                "web_search": {
                    "count": len(exa_results.get("results", [])),
                    "query_count": exa_results.get("query_count", 0),
                    "results_file": exa_results.get("results_file"),
                    "summary_file": exa_results.get("summary_file")
                },
                "youtube": {
                    "count": len(youtube_results.get("transcripts", [])),
                    "video_count": youtube_results.get("video_count", 0),
                    "transcripts_file": youtube_results.get("transcripts_file"),
                    "summary_file": youtube_results.get("summary_file")
                },
                "web_articles": {
                    "count": len(firecrawl_results.get("results", [])),
                    "url_count": firecrawl_results.get("url_count", 0),
                    "results_file": firecrawl_results.get("results_file"),
                    "summary_file": firecrawl_results.get("summary_file")
                }
            },
            "comprehensive_summary": {
                "summary_file": comprehensive_summary.get("summary_file"),
                "pdf_file": comprehensive_summary.get("pdf_file"),
                "json_file": comprehensive_summary.get("json_file")
            },
            "key_findings": comprehensive_summary.get("key_findings", {})
        }
        
        logger.info("Generated research report")
        
        return {"research_report": research_report}
    
    except Exception as e:
        logger.error(f"Error generating research report: {e}", exc_info=True)
        return {"error_info": f"Research report generation failed: {str(e)}"}
