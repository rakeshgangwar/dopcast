"""
Enhanced Research Agent implementation using LangGraph.
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from agents.base_agent import BaseAgent
from .workflow.state import ResearchState
from .workflow.research_graph import create_research_graph
from langgraph.checkpoint.memory import MemorySaver

class EnhancedResearchAgent(BaseAgent):
    """
    Enhanced Research Agent using LangGraph for workflow orchestration.
    Provides improved data collection, processing, and analysis capabilities.
    """

    def __init__(self, name: str = "enhanced_research", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the enhanced research agent.

        Args:
            name: Agent identifier
            config: Configuration parameters
        """
        super().__init__(name, config)

        # Create the research graph
        self.checkpointer = MemorySaver()
        self.graph = create_research_graph()

        # Initialize active runs tracking
        self.active_runs = {}

        self.logger.info("Enhanced Research Agent initialized with LangGraph")

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process research requests using the LangGraph workflow.

        Args:
            input_data: Input data containing research parameters
                - sport: "f1" or "motogp"
                - event_type: "race", "qualifying", "practice", "news", etc.
                - event_id: Specific event identifier (optional)
                - force_refresh: Force refresh of cached data (optional)

        Returns:
            Research report with collected and processed data
        """
        self.logger.info(f"Processing research request: {input_data}")

        # Generate a unique run ID
        run_id = str(uuid.uuid4())
        self.logger.info(f"Generated run_id: {run_id}")

        # Prepare the initial state for the graph
        initial_state: ResearchState = {"input_data": input_data}

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
                self.logger.error(f"Research workflow error: {final_state['error_info']}")
                self.active_runs[run_id]["status"] = "error"
                self.active_runs[run_id]["error"] = final_state["error_info"]
                return {"error": final_state["error_info"]}

            # Get the research report
            research_report = final_state.get("research_report", {})

            # Update run status
            self.active_runs[run_id]["status"] = "completed"
            self.active_runs[run_id]["completed_at"] = datetime.now().isoformat()

            return research_report

        except Exception as e:
            self.logger.error(f"Error executing research workflow: {e}", exc_info=True)
            self.active_runs[run_id]["status"] = "error"
            self.active_runs[run_id]["error"] = str(e)
            return {"error": f"Research workflow execution failed: {str(e)}"}

    async def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """
        Get the status of a research run.

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
        List all research runs.

        Returns:
            Dictionary of run IDs and their status information
        """
        return self.active_runs

    async def cancel_run(self, run_id: str) -> Dict[str, Any]:
        """
        Cancel a running research workflow.

        Args:
            run_id: Run identifier

        Returns:
            Status information
        """
        if run_id not in self.active_runs:
            return {"error": f"Run ID {run_id} not found"}

        if self.active_runs[run_id]["status"] != "running":
            return {"error": f"Run ID {run_id} is not running"}

        # Cancel the run (not fully supported in LangGraph yet)
        self.active_runs[run_id]["status"] = "cancelled"
        self.active_runs[run_id]["cancelled_at"] = datetime.now().isoformat()

        return {"status": "cancelled", "run_id": run_id}
