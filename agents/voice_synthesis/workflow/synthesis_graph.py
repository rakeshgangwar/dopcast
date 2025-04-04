"""
LangGraph implementation for the Voice Synthesis Agent.
Defines the voice synthesis workflow as a directed graph.
"""

import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from .state import SynthesisState
from .nodes import (
    initialize_synthesis,
    prepare_script,
    map_voices,
    generate_section_audio,
    combine_audio,
    finalize_audio
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_synthesis_graph() -> StateGraph:
    """
    Create the voice synthesis workflow graph.
    
    Returns:
        Compiled StateGraph
    """
    # Initialize the StateGraph builder
    graph_builder = StateGraph(SynthesisState)
    
    # Add nodes to the graph
    graph_builder.add_node("initialize_synthesis", initialize_synthesis)
    graph_builder.add_node("prepare_script", prepare_script)
    graph_builder.add_node("map_voices", map_voices)
    graph_builder.add_node("generate_section_audio", generate_section_audio)
    graph_builder.add_node("combine_audio", combine_audio)
    graph_builder.add_node("finalize_audio", finalize_audio)
    
    logger.info("Added nodes to the voice synthesis graph builder")
    
    # Set the entry point
    graph_builder.set_entry_point("initialize_synthesis")
    
    # Define the edges
    graph_builder.add_edge("initialize_synthesis", "prepare_script")
    graph_builder.add_edge("prepare_script", "map_voices")
    graph_builder.add_edge("map_voices", "generate_section_audio")
    graph_builder.add_edge("generate_section_audio", "combine_audio")
    graph_builder.add_edge("combine_audio", "finalize_audio")
    graph_builder.add_edge("finalize_audio", END)
    
    logger.info("Defined edges in the voice synthesis graph")
    
    # Compile the graph
    graph = graph_builder.compile()
    logger.info("Compiled the voice synthesis LangGraph")
    
    return graph
