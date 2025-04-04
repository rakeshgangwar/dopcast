"""
Enhanced Voice Synthesis Agent implementation using LangGraph.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from agents.base_agent import BaseAgent
from .workflow.state import SynthesisState
from .workflow.synthesis_graph import create_synthesis_graph
from langgraph.checkpoint.memory import MemorySaver

class EnhancedVoiceSynthesisAgent(BaseAgent):
    """
    Enhanced Voice Synthesis Agent using LangGraph for workflow orchestration.
    Provides improved voice synthesis capabilities with emotion detection and audio processing.
    """
    
    def __init__(self, name: str = "enhanced_voice_synthesis", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the enhanced voice synthesis agent.
        
        Args:
            name: Agent identifier
            config: Configuration parameters
        """
        super().__init__(name, config)
        
        # Create the synthesis graph
        self.checkpointer = MemorySaver()
        self.graph = create_synthesis_graph()
        
        # Initialize active runs tracking
        self.active_runs = {}
        
        self.logger.info("Enhanced Voice Synthesis Agent initialized with LangGraph")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process script and generate audio.
        
        Args:
            input_data: Input data containing:
                - script: Script from the script generation agent
                - custom_parameters: Any custom parameters for this synthesis
        
        Returns:
            Audio metadata with file paths and durations
        """
        self.logger.info(f"Processing voice synthesis request for: {input_data.get('script', {}).get('title', 'Untitled Episode')}")
        
        # Generate a unique run ID
        run_id = str(uuid.uuid4())
        self.logger.info(f"Generated run_id: {run_id}")
        
        # Prepare the initial state for the graph
        initial_state: SynthesisState = {"input_data": input_data}
        
        # Configuration for the graph run
        config = {"configurable": {"thread_id": run_id}}
        
        # Track the active run
        start_time = datetime.now().isoformat()
        self.active_runs[run_id] = {
            "started_at": start_time,
            "status": "running",
            "input": input_data
        }
        
        try:
            # Execute the graph
            final_state = await self.graph.ainvoke(initial_state, config=config)
            
            # Check for errors
            if "error_info" in final_state and final_state["error_info"]:
                self.logger.error(f"Voice synthesis workflow error: {final_state['error_info']}")
                self.active_runs[run_id]["status"] = "error"
                self.active_runs[run_id]["error"] = final_state["error_info"]
                return {"error": final_state["error_info"]}
            
            # Get the audio metadata
            audio_metadata = final_state.get("audio_metadata", {})
            
            # Update run status
            self.active_runs[run_id]["status"] = "completed"
            self.active_runs[run_id]["completed_at"] = datetime.now().isoformat()
            
            return audio_metadata
        
        except Exception as e:
            self.logger.error(f"Error executing voice synthesis workflow: {e}", exc_info=True)
            self.active_runs[run_id]["status"] = "error"
            self.active_runs[run_id]["error"] = str(e)
            return {"error": f"Voice synthesis workflow execution failed: {str(e)}"}
    
    async def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """
        Get the status of a voice synthesis run.
        
        Args:
            run_id: Run identifier
            
        Returns:
            Run status information
        """
        if run_id not in self.active_runs:
            return {"error": f"Run ID {run_id} not found"}
        
        return self.active_runs[run_id]
    
    async def list_runs(self) -> Dict[str, Dict[str, Any]]:
        """
        List all voice synthesis runs.
        
        Returns:
            Dictionary of run IDs and their status information
        """
        return self.active_runs
