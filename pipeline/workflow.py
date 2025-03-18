import asyncio
import logging
import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from agents.coordination_agent import CoordinationAgent
from utils.supabase_client import SupabaseClient

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
        self.supabase = SupabaseClient()
    
    async def _handle_task_completion(self, run_id: str, podcast_id: str, task: asyncio.Task) -> None:
        """
        Handle the completion of a podcast generation task.
        
        Args:
            run_id: The run identifier
            podcast_id: The podcast identifier
            task: The asyncio task
        """
        try:
            # Wait for the task to complete
            result = await task
            
            self.logger.info(f"Podcast generation task completed for {podcast_id}")
            self.active_runs[run_id]["status"] = "completed"
            self.active_runs[run_id]["completed_at"] = datetime.now().isoformat()
            self.active_runs[run_id]["result"] = result
            
            # Update podcast status in Supabase
            podcast_update = {
                "id": podcast_id,
                "status": "completed",
                "duration": result.get("duration", 0),
                "script_text": result.get("script_text", ""),
                "audio_url": result.get("audio_url", ""),
                "script_url": result.get("script_url", ""),
                "updated_at": datetime.now().isoformat()
            }
            
            update_success = self.supabase.store_podcast(podcast_update)
            if update_success:
                self.logger.info(f"Updated podcast status to completed in Supabase: {podcast_id}")
            else:
                self.logger.error(f"Failed to update podcast status in Supabase: {podcast_id}")
                
            log_success = self.supabase.log_podcast_generation(podcast_id, "workflow", "Completed podcast generation")
            if not log_success:
                self.logger.warning(f"Failed to log podcast completion for {podcast_id}")
            
        except Exception as e:
            self.logger.error(f"Podcast generation failed: {str(e)}", exc_info=True)
            
            if run_id in self.active_runs:
                self.active_runs[run_id]["status"] = "failed"
                self.active_runs[run_id]["error"] = str(e)
                self.active_runs[run_id]["completed_at"] = datetime.now().isoformat()
            
            # Update podcast status in Supabase
            try:
                podcast_update = {
                    "id": podcast_id,
                    "status": "failed",
                    "updated_at": datetime.now().isoformat()
                }
                update_success = self.supabase.store_podcast(podcast_update)
                if not update_success:
                    self.logger.error(f"Failed to update podcast status to failed in Supabase: {podcast_id}")
                    
                log_success = self.supabase.log_podcast_generation(
                    podcast_id, "workflow", f"Podcast generation failed: {str(e)}", "error"
                )
                if not log_success:
                    self.logger.warning(f"Failed to log podcast failure for {podcast_id}")
            except Exception as inner_e:
                self.logger.error(f"Error updating podcast status after failure: {str(inner_e)}")

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
        
        try:
            input_data = {
                "trigger": trigger,
                "sport": sport,
                "event_id": event_id,
                "custom_parameters": custom_parameters or {}
            }
            
            # Create a unique podcast ID
            podcast_id = str(uuid.uuid4())
            run_id = f"{sport}_{trigger}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Check Supabase connection before attempting to store data
            if not self.supabase.is_connected():
                self.logger.error("Cannot store podcast: Supabase connection is not available")
                return {"error": "Supabase connection not available", "podcast_id": podcast_id}
            
            # Check if tables exist before trying to insert
            if not self.supabase.check_tables_exist():
                self.logger.error("Cannot store podcast: Required tables don't exist in Supabase")
                return {"error": "Required Supabase tables don't exist", "podcast_id": podcast_id}
            
            # Store initial podcast data in Supabase
            self.logger.info(f"Preparing to store podcast data with ID: {podcast_id}")
            
            # Format input data for JSON serialization
            metadata = {
                "trigger": trigger,
                "sport": sport,
                "custom_parameters": custom_parameters or {}
            }
            
            # Only add event_id to metadata if it exists and is not None
            if event_id:
                metadata["event_id"] = event_id
            
            podcast_data = {
                "id": podcast_id,
                "title": f"{sport.upper()} Podcast - {event_id if event_id else 'Latest Update'}",
                "description": f"Podcast about {sport} {event_id if event_id else 'latest news'}",
                "sport": sport,
                "episode_type": custom_parameters.get("episode_type", "default") if custom_parameters else "default",
                "status": "generating",
                "metadata": metadata,  # Pass as object, not string
                "created_at": datetime.now().isoformat()
            }
            
            # Add event_id to podcast_data only if it exists and is not None
            if event_id:
                podcast_data["event_id"] = event_id
            
            self.logger.debug(f"Podcast data being stored: {podcast_data}")
            stored_podcast = self.supabase.store_podcast(podcast_data)
            
            if stored_podcast:
                self.logger.info(f"Created podcast entry in Supabase: {podcast_id}")
                log_success = self.supabase.log_podcast_generation(podcast_id, "workflow", "Started podcast generation")
                if not log_success:
                    self.logger.warning(f"Failed to create generation log entry for podcast {podcast_id}")
            else:
                self.logger.error("Failed to store podcast data in Supabase, will continue with generation anyway")
            
            # Add podcast_id to input data for the agent
            input_data["podcast_id"] = podcast_id
            
            # Start the pipeline asynchronously
            self.logger.info(f"Starting podcast generation task for podcast ID: {podcast_id}")
            task = asyncio.create_task(self.coordination_agent.process(input_data))
            
            # Set up completion handler
            completion_handler = asyncio.create_task(
                self._handle_task_completion(run_id, podcast_id, task)
            )
            
            # Track the active run
            self.active_runs[run_id] = {
                "task": task,
                "started_at": datetime.now().isoformat(),
                "status": "running",
                "input": input_data,
                "podcast_id": podcast_id,
                "completion_handler": completion_handler
            }
            
            # Return immediately since we're processing asynchronously
            return {
                "podcast_id": podcast_id,
                "run_id": run_id,
                "status": "processing"
            }
            
        except Exception as e:
            self.logger.error(f"Error starting podcast generation: {str(e)}", exc_info=True)
            return {"error": f"Failed to start podcast generation: {str(e)}"}
    
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
        try:
            schedule_id = f"schedule_{sport}_{trigger}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Check Supabase connection before attempting to store data
            if not self.supabase.is_connected():
                self.logger.error("Cannot schedule podcast: Supabase connection is not available")
                return {"error": "Supabase connection not available"}
            
            # Check if tables exist before trying to insert
            if not self.supabase.check_tables_exist():
                self.logger.error("Cannot schedule podcast: Required tables don't exist in Supabase")
                return {"error": "Required Supabase tables don't exist"}
            
            # Create a podcast entry with "scheduled" status
            podcast_id = str(uuid.uuid4())
            
            # Format metadata for JSON serialization
            metadata = {
                "schedule_id": schedule_id,
                "schedule_time": schedule_time.isoformat(),
                "trigger": trigger,
                "custom_parameters": custom_parameters or {}
            }
            
            podcast_data = {
                "id": podcast_id,
                "title": f"{sport.upper()} Podcast - {event_id if event_id else 'Scheduled Update'}",
                "description": f"Scheduled podcast about {sport} {event_id if event_id else 'latest news'}",
                "sport": sport,
                "episode_type": custom_parameters.get("episode_type", "default") if custom_parameters else "default",
                "status": "scheduled",
                "metadata": metadata,  # Pass as object, not string
                "created_at": datetime.now().isoformat()
            }
            
            # Add event_id to podcast_data only if it exists and is not None
            if event_id:
                podcast_data["event_id"] = event_id
            
            self.logger.debug(f"Scheduled podcast data being stored: {podcast_data}")
            stored_podcast = self.supabase.store_podcast(podcast_data)
            
            if stored_podcast:
                self.logger.info(f"Created scheduled podcast entry in Supabase: {podcast_id}")
                log_success = self.supabase.log_podcast_generation(
                    podcast_id, "workflow", 
                    f"Scheduled podcast generation for {schedule_time.isoformat()}"
                )
                if not log_success:
                    self.logger.warning(f"Failed to create generation log entry for scheduled podcast {podcast_id}")
            else:
                self.logger.error(f"Failed to store scheduled podcast data in Supabase")
                return {"error": "Failed to store scheduled podcast in database", "schedule_id": schedule_id}
            
            scheduled_run = {
                "id": schedule_id,
                "podcast_id": podcast_id,
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
                "podcast_id": podcast_id,
                "status": "scheduled",
                "schedule_time": schedule_time.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error scheduling podcast: {str(e)}", exc_info=True)
            return {"error": f"Failed to schedule podcast: {str(e)}"}
    
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
                "podcast_id": self.active_runs[run_id]["podcast_id"],
                "status": self.active_runs[run_id]["status"],
                "started_at": self.active_runs[run_id]["started_at"],
                "completed_at": self.active_runs[run_id].get("completed_at")
            }
        
        # Check completed runs in coordination agent
        return await self.coordination_agent.get_run_status(run_id)
    
    async def get_podcast(self, podcast_id: str) -> Dict[str, Any]:
        """
        Get podcast information from Supabase.
        
        Args:
            podcast_id: Podcast ID
            
        Returns:
            Podcast data
        """
        return self.supabase.get_podcast(podcast_id)
    
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
                "podcast_id": run_data.get("podcast_id"),
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
    
    async def list_podcasts(self, limit: int = 10, sport: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List podcasts from Supabase, optionally filtered by sport.
        
        Args:
            limit: Maximum number of podcasts to return
            sport: Filter by sport
            
        Returns:
            List of podcasts
        """
        return self.supabase.get_recent_podcasts(sport, limit)
    
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
                
                # Update podcast status in Supabase
                if "podcast_id" in cancelled_run:
                    podcast_update = {
                        "id": cancelled_run["podcast_id"],
                        "status": "cancelled",
                        "updated_at": datetime.now().isoformat()
                    }
                    self.supabase.store_podcast(podcast_update)
                    self.supabase.log_podcast_generation(
                        cancelled_run["podcast_id"], "workflow", 
                        f"Cancelled scheduled podcast generation: {schedule_id}"
                    )
                
                return {
                    "schedule_id": schedule_id,
                    "podcast_id": cancelled_run.get("podcast_id"),
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
                
                # Update podcast status in Supabase
                if "podcast_id" in run:
                    podcast_update = {
                        "id": run["podcast_id"],
                        "status": "generating",
                        "updated_at": datetime.now().isoformat()
                    }
                    self.supabase.store_podcast(podcast_update)
                    self.supabase.log_podcast_generation(
                        run["podcast_id"], "workflow", 
                        f"Starting execution of scheduled podcast generation: {run['id']}"
                    )
        
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
