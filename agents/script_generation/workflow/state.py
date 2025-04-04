"""
State definition for the Script Generation Agent workflow.
"""

from typing import TypedDict, Dict, Any, List, Optional

class ScriptState(TypedDict):
    """
    Represents the state of the script generation workflow.
    Keys are updated as the graph progresses.
    """
    # Input data for the workflow run
    input_data: Dict[str, Any]

    # Intermediate state data
    config: Optional[Dict[str, Any]] = None
    content_outline: Optional[Dict[str, Any]] = None
    research_data: Optional[Dict[str, Any]] = None
    host_personalities: Optional[List[Dict[str, Any]]] = None
    script_sections: Optional[List[Dict[str, Any]]] = None

    # Final output
    script: Optional[Dict[str, Any]] = None

    # Error tracking
    error_info: Optional[str] = None
