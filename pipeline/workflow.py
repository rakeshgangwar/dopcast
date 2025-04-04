import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import the compiled graph and the state definition
from .graph import graph, DopCastState
# Import a checkpointer (using MemorySaver for simplicity initially)
from langgraph.checkpoint.memory import MemorySaver

class PodcastWorkflow:
    """
    Manages the podcast generation workflow using LangGraph, handling scheduling,
    execution, and status tracking.
    """

    def __init__(self):
        """
        Initialize the podcast workflow manager with LangGraph.
        """
        self.logger = logging.getLogger("dopcast.workflow")
        # The graph is already compiled with a checkpointer in graph.py if needed
        # If graph.py didn't compile with one, add it here:
        # self.checkpointer = MemorySaver()
        # self.graph = graph_builder.compile(checkpointer=self.checkpointer)
        self.graph = graph # Assuming graph.py compiled it
        self.active_runs = {} # Still useful for quick lookup of running tasks
        self.scheduled_runs = []
    
    async def generate_podcast(self, sport: str, trigger: str = "manual", 
                           event_id: Optional[str] = None,
                           custom_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a podcast for a specific sport and event.
        
        Args:
            sport: Sport type ("f1" or "motogp")
            trigger: Trigger event type
            event_id: Specific event identifier
            custom_parameters: Custom parameters for the pipeline
            
        Returns:
            Information about the generated podcast
        """
        self.logger.info(f"Starting podcast generation for {sport} (trigger: {trigger})")
        
        input_data = {
            "trigger": trigger,
            "sport": sport,
            "event_id": event_id,
            "custom_parameters": custom_parameters or {}
        }
        
        # Generate a unique run ID
        run_id = str(uuid.uuid4())
        self.logger.info(f"Generated run_id: {run_id}")

        # Prepare the initial state for the graph
        initial_state: DopCastState = {"initial_request": input_data}

        # Configuration for the graph run, including the thread_id for state tracking
        config = {"configurable": {"thread_id": run_id}}

        # Track the active run (optional, as checkpointer handles state)
        start_time = datetime.now().isoformat()
        self.active_runs[run_id] = {
            "started_at": start_time,
            "status": "running",
            "input": input_data,
            "task": None # We'll store the task if running fully async
        }

        # Execute the graph asynchronously
        try:
            # Use ainvoke for the final state or astream for intermediate steps
            # For simplicity, let's use ainvoke first
            final_state_dict = await self.graph.ainvoke(initial_state, config=config)
            final_state = DopCastState(**final_state_dict) # Convert dict back to TypedDict if needed

            self.logger.info(f"Graph execution completed for run_id: {run_id}")
            end_time = datetime.now().isoformat()

            if final_state.get("error_info"):
                self.logger.error(f"Podcast generation failed for run_id {run_id}: {final_state['error_info']}")
                self.active_runs[run_id]["status"] = "failed"
                self.active_runs[run_id]["error"] = final_state['error_info']
                self.active_runs[run_id]["completed_at"] = end_time
                # Remove from active runs? Or keep for history? Depends on checkpointer usage.
                # del self.active_runs[run_id]
                return {"error": final_state['error_info'], "run_id": run_id}
            else:
                # Extract the final podcast info
                podcast_result = final_state.get("final_podcast_info", {})
                self.active_runs[run_id]["status"] = "completed"
                self.active_runs[run_id]["completed_at"] = end_time
                self.active_runs[run_id]["result"] = podcast_result # Store final agent output
                # del self.active_runs[run_id]
                return {
                    "run_id": run_id,
                    "status": "completed",
                    "podcast": podcast_result
                }

        except Exception as e:
            self.logger.error(f"Podcast generation failed unexpectedly for run_id {run_id}: {str(e)}", exc_info=True)
            if run_id in self.active_runs:
                self.active_runs[run_id]["status"] = "failed"
                self.active_runs[run_id]["error"] = str(e)
                self.active_runs[run_id]["completed_at"] = datetime.now().isoformat()
            return {"error": str(e), "run_id": run_id}
    
    async def schedule_podcast(self, sport: str, trigger: str, 
                           schedule_time: datetime,
                           event_id: Optional[str] = None,
                           custom_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        Schedule a podcast for future generation.
        
        Args:
            sport: Sport type
            trigger: Trigger event type
            schedule_time: When to generate the podcast
            event_id: Specific event identifier
            custom_parameters: Custom parameters for the pipeline
            
        Returns:
            Information about the scheduled podcast
        """
        schedule_id = f"schedule_{sport}_{trigger}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        scheduled_run = {
            "id": schedule_id,
            "sport": sport,
            "trigger": trigger,
            "event_id": event_id,
            "schedule_time": schedule_time.isoformat(),
            "custom_parameters": custom_parameters or {},
            "status": "scheduled"
        }
        
        self.scheduled_runs.append(scheduled_run)
        self.logger.info(f"Scheduled podcast generation: {schedule_id} at {schedule_time}")
        
        return {
            "schedule_id": schedule_id,
            "status": "scheduled",
            "schedule_time": schedule_time.isoformat()
        }
    
    async def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """
        Get the status of a specific run.
        
        Args:
            run_id: Run identifier
            
        Returns:
            Run status information
        """
        # TODO: Implement robust status check using the graph's checkpointer
        # config = {"configurable": {"thread_id": run_id}}
        # try:
        #     state = await self.graph.aget_state(config=config)
        #     # Extract relevant status info from state.values
        #     return { ... }
        # except Exception as e: # Handle cases where the run_id is not found in checkpointer
        #     return {"error": f"Run not found or error retrieving status: {run_id}, {e}"}

        # Temporary fallback using active_runs memory
        if run_id in self.active_runs:
             run_data = self.active_runs[run_id]
             return {
                 "run_id": run_id,
                 "status": run_data["status"],
                 "started_at": run_data["started_at"],
                 "completed_at": run_data.get("completed_at"),
                 "error": run_data.get("error")
             }
        else:
             # If not in active memory, assume completed or unknown (needs checkpointer)
             return {"error": f"Run status for {run_id} not found in active memory. Checkpointer needed for history."}
    
    async def list_runs(self, limit: int = 10, sport: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List recent runs, optionally filtered by sport.
        
        Args:
            limit: Maximum number of runs to return
            sport: Filter by sport
            
        Returns:
            List of run summaries
        """
        # Get active runs
        active_runs_list = []
        for run_id, run_data in self.active_runs.items():
            if sport and run_data["input"]["sport"] != sport:
                continue
                
            active_runs_list.append({
                "run_id": run_id,
                "sport": run_data["input"]["sport"],
                "trigger": run_data["input"]["trigger"],
                "status": run_data["status"],
                "started_at": run_data["started_at"],
                "completed_at": run_data.get("completed_at")
            })
        
        # TODO: Implement listing using the graph's checkpointer
        # This is complex as it requires iterating through checkpointer history.
        # For now, we only list runs currently in active_runs memory.
        completed_runs = [] # Placeholder
        
        # Combine and sort by start time (most recent first)
        all_runs = active_runs_list + completed_runs
        all_runs.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        
        return all_runs[:limit]
    
    async def list_scheduled_runs(self, sport: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List scheduled runs, optionally filtered by sport.
        
        Args:
            sport: Filter by sport
            
        Returns:
            List of scheduled runs
        """
        if sport:
            return [run for run in self.scheduled_runs if run["sport"] == sport]
        return self.scheduled_runs
    
    async def cancel_scheduled_run(self, schedule_id: str) -> Dict[str, Any]:
        """
        Cancel a scheduled run.
        
        Args:
            schedule_id: Schedule identifier
            
        Returns:
            Status of the cancellation
        """
        for i, run in enumerate(self.scheduled_runs):
            if run["id"] == schedule_id:
                cancelled_run = self.scheduled_runs.pop(i)
                cancelled_run["status"] = "cancelled"
                self.logger.info(f"Cancelled scheduled run: {schedule_id}")
                return {
                    "schedule_id": schedule_id,
                    "status": "cancelled"
                }
        
        return {
            "error": f"Scheduled run not found: {schedule_id}"
        }
    
    async def check_scheduled_runs(self) -> None:
        """
        Check for scheduled runs that are due and execute them.
        This should be called periodically by a scheduler.
        """
        now = datetime.now()
        runs_to_execute = []
        
        # Find runs that are due
        for i, run in enumerate(self.scheduled_runs):
            schedule_time = datetime.fromisoformat(run["schedule_time"])
            if now >= schedule_time:
                runs_to_execute.append(run)
                self.scheduled_runs[i]["status"] = "executing"
        
        # Execute due runs
        for run in runs_to_execute:
            self.logger.info(f"Executing scheduled run: {run['id']}")
            
            # Remove from scheduled runs
            self.scheduled_runs = [r for r in self.scheduled_runs if r["id"] != run["id"]]
            
            # Execute the run
            asyncio.create_task(self.generate_podcast(
                sport=run["sport"],
                trigger=run["trigger"],
                event_id=run["event_id"],
                custom_parameters=run["custom_parameters"]
            ))
