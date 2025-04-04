"""
State definition for the Research Agent workflow.
"""

from typing import TypedDict, Dict, Any, List, Optional

class ResearchState(TypedDict):
    """
    Represents the state of the research workflow.
    Keys are updated as the graph progresses.
    """
    # Input data for the workflow run
    input_data: Dict[str, Any]

    # Configuration
    config: Optional[Dict[str, Any]] = None

    # Intermediate state data
    exa_results: Optional[Dict[str, Any]] = None
    youtube_results: Optional[Dict[str, Any]] = None
    firecrawl_results: Optional[Dict[str, Any]] = None
    comprehensive_summary: Optional[Dict[str, Any]] = None

    # Final output
    research_report: Optional[Dict[str, Any]] = None

    # Error tracking
    error_info: Optional[str] = None
