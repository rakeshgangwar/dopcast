"""
Enhanced Audio Production Agent implementation using LangGraph.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from agents.base_agent import BaseAgent
from .workflow.state import ProductionState
from .workflow.production_graph import create_production_graph
from langgraph.checkpoint.memory import MemorySaver

class EnhancedAudioProductionAgent(BaseAgent):
    """
    Enhanced Audio Production Agent using LangGraph for workflow orchestration.
    Provides improved audio production capabilities with mixing, mastering, and metadata generation.
    """
    
    def __init__(self, name: str = "enhanced_audio_production", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the enhanced audio production agent.
        
        Args:
            name: Agent identifier
            config: Configuration parameters
        """
        super().__init__(name, config)
        
        # Create the production graph
        self.checkpointer = MemorySaver()
        self.graph = create_production_graph()
        
        # Initialize active runs tracking
        self.active_runs = {}
        
        self.logger.info("Enhanced Audio Production Agent initialized with LangGraph")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process audio metadata and produce final podcast episode.
        
        Args:
            input_data: Input data containing:
                - audio_metadata: Audio metadata from voice synthesis
                - custom_parameters: Any custom parameters for this production
        
        Returns:
            Production metadata with file paths and publishing information
        """
        self.logger.info(f"Processing audio production request for: {input_data.get('audio_metadata', {}).get('title', 'Untitled Episode')}")
        
        # Generate a unique run ID
        run_id = str(uuid.uuid4())
        self.logger.info(f"Generated run_id: {run_id}")
        
        # Prepare the initial state for the graph
        initial_state: ProductionState = {"input_data": input_data}
        
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
                self.logger.error(f"Audio production workflow error: {final_state['error_info']}")
                self.active_runs[run_id]["status"] = "error"
                self.active_runs[run_id]["error"] = final_state["error_info"]
                return {"error": final_state["error_info"]}
            
            # Get the production metadata
            production_metadata = final_state.get("production_metadata", {})
            
            # Update run status
            self.active_runs[run_id]["status"] = "completed"
            self.active_runs[run_id]["completed_at"] = datetime.now().isoformat()
            
            return production_metadata
        
        except Exception as e:
            self.logger.error(f"Error executing audio production workflow: {e}", exc_info=True)
            self.active_runs[run_id]["status"] = "error"
            self.active_runs[run_id]["error"] = str(e)
            return {"error": f"Audio production workflow execution failed: {str(e)}"}
    
    async def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """
        Get the status of an audio production run.
        
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
        List all audio production runs.
        
        Returns:
            Dictionary of run IDs and their status information
        """
        return self.active_runs
