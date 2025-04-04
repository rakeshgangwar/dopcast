"""
State definition for the Voice Synthesis Agent workflow.
"""

from typing import TypedDict, Dict, Any, List, Optional

class SynthesisState(TypedDict):
    """
    Represents the state of the voice synthesis workflow.
    Keys are updated as the graph progresses.
    """
    # Input data for the workflow run
    input_data: Dict[str, Any]
    
    # Intermediate state data
    config: Optional[Dict[str, Any]] = None
    script: Optional[Dict[str, Any]] = None
    voice_mapping: Optional[Dict[str, Dict[str, Any]]] = None
    section_audio: Optional[List[Dict[str, Any]]] = None
    
    # Final output
    audio_metadata: Optional[Dict[str, Any]] = None
    
    # Error tracking
    error_info: Optional[str] = None
