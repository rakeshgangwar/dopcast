import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from agents.coordination_agent import CoordinationAgent

class PodcastWorkflow:
    """
    Manages the podcast generation workflow, handling scheduling, execution,
    and status tracking for podcast creation.
    """
    
    def __init__(self):
        """
        Initialize the podcast workflow manager.
        """
        self.logger = logging.getLogger("dopcast.workflow")
        self.coordination_agent = CoordinationAgent()
        self.coordination_agent.initialize_agents()
        self.active_runs = {}
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
        
        # Start the pipeline asynchronously
        task = asyncio.create_task(self.coordination_agent.process(input_data))
        run_id = f"{sport}_{trigger}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Track the active run
        self.active_runs[run_id] = {
            "task": task,
            "started_at": datetime.now().isoformat(),
            "status": "running",
            "input": input_data
        }
        
        # Wait for the result
        try:
            result = await task
            self.active_runs[run_id]["status"] = "completed"
            self.active_runs[run_id]["completed_at"] = datetime.now().isoformat()
            self.active_runs[run_id]["result"] = result
            return result
        except Exception as e:
            self.logger.error(f"Podcast generation failed: {str(e)}")
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
        # Check active runs first
        if run_id in self.active_runs:
            return {
                "run_id": run_id,
                "status": self.active_runs[run_id]["status"],
                "started_at": self.active_runs[run_id]["started_at"],
                "completed_at": self.active_runs[run_id].get("completed_at")
            }
        
        # Check completed runs in coordination agent
        return await self.coordination_agent.get_run_status(run_id)
    
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
        
        # Get completed runs from coordination agent
        completed_runs = await self.coordination_agent.list_runs(limit, sport)
        
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
