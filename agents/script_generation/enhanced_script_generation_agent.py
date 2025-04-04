"""
Enhanced Script Generation Agent implementation using LangGraph.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from agents.base_agent import BaseAgent
from .workflow.state import ScriptState
from .workflow.enhanced_script_graph import create_enhanced_script_graph
from langgraph.checkpoint.memory import MemorySaver

class EnhancedScriptGenerationAgent(BaseAgent):
    """
    Enhanced Script Generation Agent using LangGraph for workflow orchestration.
    Provides improved script generation capabilities with natural dialogue and formatting.
    """

    def __init__(self, name: str = "enhanced_script_generation", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the enhanced script generation agent.

        Args:
            name: Agent identifier
            config: Configuration parameters
        """
        super().__init__(name, config)

        # Create the script graph
        self.checkpointer = MemorySaver()
        self.graph = create_enhanced_script_graph()

        # Initialize active runs tracking
        self.active_runs = {}

        self.logger.info("Enhanced Script Generation Agent initialized with LangGraph")

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process content outline and generate a podcast script.

        Args:
            input_data: Input data containing:
                - content_outline: Outline from the content planning agent
                - custom_parameters: Any custom parameters for this script

        Returns:
            Complete podcast script with dialogue and production notes
        """
        self.logger.info(f"Processing script generation request for: {input_data.get('content_outline', {}).get('title', 'Untitled Episode')}")

        # Generate a unique run ID
        run_id = str(uuid.uuid4())
        self.logger.info(f"Generated run_id: {run_id}")

        # Prepare the initial state for the graph
        initial_state: ScriptState = {"input_data": input_data}

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
                self.logger.error(f"Script generation workflow error: {final_state['error_info']}")
                self.active_runs[run_id]["status"] = "error"
                self.active_runs[run_id]["error"] = final_state["error_info"]
                return {"error": final_state["error_info"]}

            # Get the script
            script = final_state.get("script", {})

            # Update run status
            self.active_runs[run_id]["status"] = "completed"
            self.active_runs[run_id]["completed_at"] = datetime.now().isoformat()

            return script

        except Exception as e:
            self.logger.error(f"Error executing script generation workflow: {e}", exc_info=True)
            self.active_runs[run_id]["status"] = "error"
            self.active_runs[run_id]["error"] = str(e)
            return {"error": f"Script generation workflow execution failed: {str(e)}"}

    async def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """
        Get the status of a script generation run.

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
        List all script generation runs.

        Returns:
            Dictionary of run IDs and their status information
        """
        return self.active_runs
