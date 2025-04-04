"""
State definition for the Content Planning Agent workflow.
"""

from typing import TypedDict, Dict, Any, List, Optional

class PlanningState(TypedDict):
    """
    Represents the state of the content planning workflow.
    Keys are updated as the graph progresses.
    """
    # Input data for the workflow run
    input_data: Dict[str, Any]
    
    # Intermediate state data
    config: Optional[Dict[str, Any]] = None
    research_data: Optional[Dict[str, Any]] = None
    episode_format: Optional[Dict[str, Any]] = None
    adjusted_sections: Optional[List[Dict[str, Any]]] = None
    detailed_sections: Optional[List[Dict[str, Any]]] = None
    
    # Final output
    content_plan: Optional[Dict[str, Any]] = None
    
    # Error tracking
    error_info: Optional[str] = None
