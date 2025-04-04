"""
State definition for the Audio Production Agent workflow.
"""

from typing import TypedDict, Dict, Any, List, Optional

class ProductionState(TypedDict):
    """
    Represents the state of the audio production workflow.
    Keys are updated as the graph progresses.
    """
    # Input data for the workflow run
    input_data: Dict[str, Any]
    
    # Intermediate state data
    config: Optional[Dict[str, Any]] = None
    audio_metadata: Optional[Dict[str, Any]] = None
    processed_segments: Optional[List[Dict[str, Any]]] = None
    mixed_audio: Optional[Dict[str, Any]] = None
    
    # Final output
    production_metadata: Optional[Dict[str, Any]] = None
    
    # Error tracking
    error_info: Optional[str] = None
