"""
LangGraph implementation for the Content Planning Agent.
Defines the content planning workflow as a directed graph.
"""

import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from .state import PlanningState
from .nodes import (
    initialize_planning,
    prepare_research_data,
    select_episode_format,
    adjust_sections,
    create_detailed_sections,
    generate_content_plan
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_planning_graph() -> StateGraph:
    """
    Create the content planning workflow graph.
    
    Returns:
        Compiled StateGraph
    """
    # Initialize the StateGraph builder
    graph_builder = StateGraph(PlanningState)
    
    # Add nodes to the graph
    graph_builder.add_node("initialize_planning", initialize_planning)
    graph_builder.add_node("prepare_research_data", prepare_research_data)
    graph_builder.add_node("select_episode_format", select_episode_format)
    graph_builder.add_node("adjust_sections", adjust_sections)
    graph_builder.add_node("create_detailed_sections", create_detailed_sections)
    graph_builder.add_node("generate_content_plan", generate_content_plan)
    
    logger.info("Added nodes to the planning graph builder")
    
    # Set the entry point
    graph_builder.set_entry_point("initialize_planning")
    
    # Define the edges
    graph_builder.add_edge("initialize_planning", "prepare_research_data")
    graph_builder.add_edge("prepare_research_data", "select_episode_format")
    graph_builder.add_edge("select_episode_format", "adjust_sections")
    graph_builder.add_edge("adjust_sections", "create_detailed_sections")
    graph_builder.add_edge("create_detailed_sections", "generate_content_plan")
    graph_builder.add_edge("generate_content_plan", END)
    
    logger.info("Defined edges in the planning graph")
    
    # Compile the graph
    graph = graph_builder.compile()
    logger.info("Compiled the planning LangGraph")
    
    return graph
