"""
Workflow components for the DopCast Research Agent.
This package contains the LangGraph workflow for the research agent.
"""

from .state import ResearchState
from .research_graph import create_research_graph
from .nodes import (
    initialize_research,
    collect_data,
    process_data,
    extract_entities,
    analyze_trends,
    generate_report
)

__all__ = [
    "create_research_graph",
    "ResearchState",
    "initialize_research",
    "collect_data",
    "process_data",
    "extract_entities",
    "analyze_trends",
    "generate_report"
]
