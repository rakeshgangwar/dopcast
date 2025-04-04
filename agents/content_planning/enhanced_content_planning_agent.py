"""
Enhanced Content Planning Agent implementation using LangGraph.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from agents.base_agent import BaseAgent
from .workflow.state import PlanningState
from .workflow.planning_graph import create_planning_graph
from langgraph.checkpoint.memory import MemorySaver

class EnhancedContentPlanningAgent(BaseAgent):
    """
    Enhanced Content Planning Agent using LangGraph for workflow orchestration.
    Provides improved content planning and outline generation capabilities.
    """
    
    def __init__(self, name: str = "enhanced_content_planning", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the enhanced content planning agent.
        
        Args:
            name: Agent identifier
            config: Configuration parameters
        """
        super().__init__(name, config)
        
        # Create the planning graph
        self.checkpointer = MemorySaver()
        self.graph = create_planning_graph()
        
        # Initialize active runs tracking
        self.active_runs = {}
        
        self.logger.info("Enhanced Content Planning Agent initialized with LangGraph")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process content planning requests using the LangGraph workflow.
        
        Args:
            input_data: Input data containing:
                - research_data: Data from the research agent
                - episode_type: Type of episode to create
                - custom_parameters: Any custom parameters for this episode
        
        Returns:
            Content plan with sections and talking points
        """
        self.logger.info(f"Processing content planning request: {input_data.get('episode_type', 'unknown')}")
        
        # Generate a unique run ID
        run_id = str(uuid.uuid4())
        self.logger.info(f"Generated run_id: {run_id}")
        
        # Prepare the initial state for the graph
        initial_state: PlanningState = {"input_data": input_data}
        
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
                self.logger.error(f"Content planning workflow error: {final_state['error_info']}")
                self.active_runs[run_id]["status"] = "error"
                self.active_runs[run_id]["error"] = final_state["error_info"]
                return {"error": final_state["error_info"]}
            
            # Get the content plan
            content_plan = final_state.get("content_plan", {})
            
            # Update run status
            self.active_runs[run_id]["status"] = "completed"
            self.active_runs[run_id]["completed_at"] = datetime.now().isoformat()
            
            return content_plan
        
        except Exception as e:
            self.logger.error(f"Error executing content planning workflow: {e}", exc_info=True)
            self.active_runs[run_id]["status"] = "error"
            self.active_runs[run_id]["error"] = str(e)
            return {"error": f"Content planning workflow execution failed: {str(e)}"}
    
    async def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """
        Get the status of a content planning run.
        
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
        List all content planning runs.
        
        Returns:
            Dictionary of run IDs and their status information
        """
        return self.active_runs
