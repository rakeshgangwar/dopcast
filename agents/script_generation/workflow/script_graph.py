"""
LangGraph implementation for the Script Generation Agent.
Defines the script generation workflow as a directed graph.
"""

import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from .state import ScriptState
from .nodes import (
    initialize_script_generation,
    prepare_content_outline,
    prepare_host_personalities,
    generate_script_sections,
    assemble_script,
    format_script
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_script_graph() -> StateGraph:
    """
    Create the script generation workflow graph.
    
    Returns:
        Compiled StateGraph
    """
    # Initialize the StateGraph builder
    graph_builder = StateGraph(ScriptState)
    
    # Add nodes to the graph
    graph_builder.add_node("initialize_script_generation", initialize_script_generation)
    graph_builder.add_node("prepare_content_outline", prepare_content_outline)
    graph_builder.add_node("prepare_host_personalities", prepare_host_personalities)
    graph_builder.add_node("generate_script_sections", generate_script_sections)
    graph_builder.add_node("assemble_script", assemble_script)
    graph_builder.add_node("format_script", format_script)
    
    logger.info("Added nodes to the script generation graph builder")
    
    # Set the entry point
    graph_builder.set_entry_point("initialize_script_generation")
    
    # Define the edges
    graph_builder.add_edge("initialize_script_generation", "prepare_content_outline")
    graph_builder.add_edge("prepare_content_outline", "prepare_host_personalities")
    graph_builder.add_edge("prepare_host_personalities", "generate_script_sections")
    graph_builder.add_edge("generate_script_sections", "assemble_script")
    graph_builder.add_edge("assemble_script", "format_script")
    graph_builder.add_edge("format_script", END)
    
    logger.info("Defined edges in the script generation graph")
    
    # Compile the graph
    graph = graph_builder.compile()
    logger.info("Compiled the script generation LangGraph")
    
    return graph
