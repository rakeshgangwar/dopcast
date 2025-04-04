"""
Enhanced LangGraph implementation for the Research Agent.
Defines the research workflow as a directed graph.
"""

import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from .state import ResearchState
from .enhanced_research_nodes import (
    initialize_research,
    collect_web_data,
    collect_youtube_data,
    collect_targeted_web_data,
    process_research_data,
    generate_research_report
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_enhanced_research_graph() -> StateGraph:
    """
    Create the enhanced research workflow graph.
    
    Returns:
        Compiled StateGraph
    """
    # Initialize the StateGraph builder
    graph_builder = StateGraph(ResearchState)
    
    # Add nodes to the graph
    graph_builder.add_node("initialize_research", initialize_research)
    graph_builder.add_node("collect_web_data", collect_web_data)
    graph_builder.add_node("collect_youtube_data", collect_youtube_data)
    graph_builder.add_node("collect_targeted_web_data", collect_targeted_web_data)
    graph_builder.add_node("process_research_data", process_research_data)
    graph_builder.add_node("generate_research_report", generate_research_report)
    
    logger.info("Added nodes to the enhanced research graph builder")
    
    # Set the entry point
    graph_builder.set_entry_point("initialize_research")
    
    # Define the edges
    graph_builder.add_edge("initialize_research", "collect_web_data")
    graph_builder.add_edge("collect_web_data", "collect_youtube_data")
    graph_builder.add_edge("collect_youtube_data", "collect_targeted_web_data")
    graph_builder.add_edge("collect_targeted_web_data", "process_research_data")
    graph_builder.add_edge("process_research_data", "generate_research_report")
    graph_builder.add_edge("generate_research_report", END)
    
    logger.info("Defined edges in the enhanced research graph")
    
    # Compile the graph
    graph = graph_builder.compile()
    logger.info("Compiled the enhanced research LangGraph")
    
    return graph
