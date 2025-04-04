"""
LangGraph implementation for the Research Agent.
Defines the research workflow as a directed graph.
"""

import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from .state import ResearchState
from .nodes import (
    initialize_research,
    collect_data,
    collect_youtube_transcripts,
    process_data,
    extract_entities,
    analyze_trends,
    generate_report
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def should_retry_collection(state: ResearchState) -> str:
    """
    Determine if data collection should be retried.

    Args:
        state: Current state

    Returns:
        Next node name
    """
    # Check if we have collected data
    if not state.get("collected_data") or len(state.get("collected_data", [])) == 0:
        # Check if we've already tried fallback
        if state.get("config", {}).get("tried_fallback"):
            # If we've already tried fallback and still have no data, move to report generation
            logger.warning("No data collected even after fallback, proceeding to report generation")
            return "generate_report"
        else:
            # Try fallback data
            logger.info("No data collected, trying fallback")
            return "collect_data_fallback"

    # We have data, proceed to processing
    return "process_data"

def create_research_graph() -> StateGraph:
    """
    Create the research workflow graph.

    Returns:
        Compiled StateGraph
    """
    # Initialize the StateGraph builder
    graph_builder = StateGraph(ResearchState)

    # Add nodes to the graph
    graph_builder.add_node("initialize_research", initialize_research)
    graph_builder.add_node("collect_data", collect_data)
    graph_builder.add_node("collect_data_fallback", collect_data)  # Same function, different context
    graph_builder.add_node("collect_youtube_transcripts", collect_youtube_transcripts)
    graph_builder.add_node("process_data", process_data)
    graph_builder.add_node("extract_entities", extract_entities)
    graph_builder.add_node("analyze_trends", analyze_trends)
    graph_builder.add_node("generate_report", generate_report)

    logger.info("Added nodes to the research graph builder")

    # Set the entry point
    graph_builder.set_entry_point("initialize_research")

    # Define the edges
    graph_builder.add_edge("initialize_research", "collect_data")

    # Conditional edge after data collection
    graph_builder.add_conditional_edges(
        "collect_data",
        should_retry_collection,
        {
            "collect_data_fallback": "collect_data_fallback",
            "process_data": "collect_youtube_transcripts",
            "generate_report": "generate_report"
        }
    )

    # Conditional edge after fallback collection
    graph_builder.add_conditional_edges(
        "collect_data_fallback",
        should_retry_collection,
        {
            "process_data": "collect_youtube_transcripts",
            "generate_report": "generate_report"
        }
    )

    # Add edge from YouTube transcript collection to data processing
    graph_builder.add_edge("collect_youtube_transcripts", "process_data")

    # Standard flow for the rest of the graph
    graph_builder.add_edge("process_data", "extract_entities")
    graph_builder.add_edge("extract_entities", "analyze_trends")
    graph_builder.add_edge("analyze_trends", "generate_report")
    graph_builder.add_edge("generate_report", END)

    logger.info("Defined edges in the research graph")

    # Compile the graph
    graph = graph_builder.compile()
    logger.info("Compiled the research LangGraph")

    return graph
