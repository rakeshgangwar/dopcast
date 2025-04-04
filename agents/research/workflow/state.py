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
    
    # Intermediate state data
    config: Optional[Dict[str, Any]] = None
    collected_data: Optional[List[Dict[str, Any]]] = None
    processed_data: Optional[Dict[str, Any]] = None
    entities: Optional[Dict[str, Any]] = None
    trends: Optional[Dict[str, Any]] = None
    
    # Final output
    research_report: Optional[Dict[str, Any]] = None
    
    # Error tracking
    error_info: Optional[str] = None
