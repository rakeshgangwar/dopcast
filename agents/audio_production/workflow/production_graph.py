"""
LangGraph implementation for the Audio Production Agent.
Defines the audio production workflow as a directed graph.
"""

import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from .state import ProductionState
from .nodes import (
    initialize_production,
    prepare_audio_metadata,
    enhance_audio,
    mix_audio,
    master_audio,
    generate_metadata
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_production_graph() -> StateGraph:
    """
    Create the audio production workflow graph.
    
    Returns:
        Compiled StateGraph
    """
    # Initialize the StateGraph builder
    graph_builder = StateGraph(ProductionState)
    
    # Add nodes to the graph
    graph_builder.add_node("initialize_production", initialize_production)
    graph_builder.add_node("prepare_audio_metadata", prepare_audio_metadata)
    graph_builder.add_node("enhance_audio", enhance_audio)
    graph_builder.add_node("mix_audio", mix_audio)
    graph_builder.add_node("master_audio", master_audio)
    graph_builder.add_node("generate_metadata", generate_metadata)
    
    logger.info("Added nodes to the audio production graph builder")
    
    # Set the entry point
    graph_builder.set_entry_point("initialize_production")
    
    # Define the edges
    graph_builder.add_edge("initialize_production", "prepare_audio_metadata")
    graph_builder.add_edge("prepare_audio_metadata", "enhance_audio")
    graph_builder.add_edge("enhance_audio", "mix_audio")
    graph_builder.add_edge("mix_audio", "master_audio")
    graph_builder.add_edge("master_audio", "generate_metadata")
    graph_builder.add_edge("generate_metadata", END)
    
    logger.info("Defined edges in the audio production graph")
    
    # Compile the graph
    graph = graph_builder.compile()
    logger.info("Compiled the audio production LangGraph")
    
    return graph
