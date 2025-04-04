"""
Workflow components for the DopCast Voice Synthesis Agent.
This package contains the LangGraph workflow for the voice synthesis agent.
"""

from .state import SynthesisState
from .synthesis_graph import create_synthesis_graph
from .nodes import (
    initialize_synthesis,
    prepare_script,
    map_voices,
    generate_section_audio,
    combine_audio,
    finalize_audio
)

__all__ = [
    "SynthesisState",
    "create_synthesis_graph",
    "initialize_synthesis",
    "prepare_script",
    "map_voices",
    "generate_section_audio",
    "combine_audio",
    "finalize_audio"
]
