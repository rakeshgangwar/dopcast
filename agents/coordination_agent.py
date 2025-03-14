import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from agents.base_agent import BaseAgent
from agents.research_agent import ResearchAgent
from agents.content_planning_agent import ContentPlanningAgent
from agents.script_generation_agent import ScriptGenerationAgent
from agents.voice_synthesis_agent import VoiceSynthesisAgent
from agents.audio_production_agent import AudioProductionAgent

class CoordinationAgent(BaseAgent):
    """
    Agent responsible for orchestrating the entire workflow and ensuring quality.
    Manages the pipeline from research to publication.
    """
    
    def __init__(self, name: str = "coordination", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the coordination agent.
        
        Args:
            name: Agent identifier
            config: Configuration parameters
        """
        default_config = {
            "pipeline_steps": [
                "research",
                "content_planning",
                "script_generation",
                "voice_synthesis",
                "audio_production"
            ],
            "trigger_events": {
                "f1_race": {
                    "schedule": "sunday+6h",  # 6 hours after Sunday race
                    "episode_type": "race_review"
                },
                "motogp_race": {
                    "schedule": "sunday+6h",  # 6 hours after Sunday race
                    "episode_type": "race_review"
                },
                "f1_qualifying": {
                    "schedule": "saturday+4h",  # 4 hours after Saturday qualifying
                    "episode_type": "qualifying_analysis"
                },
                "weekly_news": {
                    "schedule": "thursday",  # Weekly news update
                    "episode_type": "news_update"
                }
            },
            "quality_thresholds": {
                "min_research_sources": 5,
                "min_script_word_count": 1500,
                "max_audio_silence": 2.0  # seconds
            },
            "notification_channels": [
                "email",
                "slack"
            ],
            "retry_attempts": 3
        }
        
        # Merge default config with provided config
        merged_config = default_config.copy()
        if config:
            for key, value in config.items():
                if isinstance(value, dict) and key in merged_config and isinstance(merged_config[key], dict):
                    merged_config[key].update(value)
                else:
                    merged_config[key] = value
        
        super().__init__(name, merged_config)
        
        # Initialize agents
        self.agents = {}
        
        # Initialize run history
        self.run_history_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "runs")
        os.makedirs(self.run_history_dir, exist_ok=True)
    
    def initialize_agents(self):
        """
        Initialize all the agents in the pipeline.
        """
        self.agents = {
            "research": ResearchAgent(),
            "content_planning": ContentPlanningAgent(),
            "script_generation": ScriptGenerationAgent(),
            "voice_synthesis": VoiceSynthesisAgent(),
            "audio_production": AudioProductionAgent()
        }
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a podcast generation request.
        
        Args:
            input_data: Input data containing:
                - trigger: Trigger event type
                - sport: Sport type (f1 or motogp)
                - event_id: Specific event identifier (optional)
                - custom_parameters: Any custom parameters for the pipeline
        
        Returns:
            Information about the generated podcast
        """
        trigger = input_data.get("trigger", "manual")
        sport = input_data.get("sport", "f1")
        event_id = input_data.get("event_id")
        custom_parameters = input_data.get("custom_parameters", {})
        
        # Initialize agents if not already done
        if not self.agents:
            self.initialize_agents()
        
        # Determine episode type based on trigger
        episode_type = None
        if trigger != "manual":
            trigger_config = self.config["trigger_events"].get(f"{sport}_{trigger}")
            if trigger_config:
                episode_type = trigger_config.get("episode_type")
        
        if not episode_type:
            episode_type = custom_parameters.get("episode_type", "race_review")
        
        # Create run ID and record
        run_id = f"{sport}_{episode_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        run_record = {
            "run_id": run_id,
            "trigger": trigger,
            "sport": sport,
            "event_id": event_id,
            "episode_type": episode_type,
            "custom_parameters": custom_parameters,
            "started_at": datetime.now().isoformat(),
            "status": "running",
            "steps": []
        }
        
        try:
            # Execute the pipeline
            result = await self._execute_pipeline(
                run_id, sport, episode_type, event_id, custom_parameters
            )
            
            # Update run record with success
            run_record["status"] = "completed"
            run_record["completed_at"] = datetime.now().isoformat()
            run_record["result"] = result
            
            # Save the run record
            self._save_run_record(run_record)
            
            return {
                "run_id": run_id,
                "status": "completed",
                "podcast": result
            }
            
        except Exception as e:
            # Update run record with failure
            run_record["status"] = "failed"
            run_record["error"] = str(e)
            run_record["completed_at"] = datetime.now().isoformat()
            
            # Save the run record
            self._save_run_record(run_record)
            
            self.logger.error(f"Pipeline execution failed: {str(e)}")
            return {
                "run_id": run_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def _execute_pipeline(self, run_id: str, sport: str, episode_type: str,
                             event_id: Optional[str], custom_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete podcast generation pipeline.
        
        Args:
            run_id: Unique identifier for this run
            sport: Sport type
            episode_type: Type of episode to create
            event_id: Specific event identifier
            custom_parameters: Custom parameters for the pipeline
            
        Returns:
            Information about the generated podcast
        """
        pipeline_data = {}
        step_results = {}
        
        # Execute each step in the pipeline
        for step in self.config["pipeline_steps"]:
            self.logger.info(f"Executing pipeline step: {step}")
            
            # Prepare input for this step
            step_input = self._prepare_step_input(
                step, sport, episode_type, event_id, custom_parameters, step_results
            )
            
            # Execute the step with retry logic
            agent = self.agents.get(step)
            if not agent:
                raise ValueError(f"Agent not found for step: {step}")
            
            retry_count = 0
            while retry_count < self.config["retry_attempts"]:
                try:
                    result = await agent.run(step_input)
                    
                    # Validate the result
                    self._validate_step_result(step, result)
                    
                    # Store the result
                    step_results[step] = result
                    pipeline_data[step] = {
                        "status": "completed",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    retry_count += 1
                    self.logger.warning(f"Step {step} failed (attempt {retry_count}): {str(e)}")
                    
                    if retry_count >= self.config["retry_attempts"]:
                        pipeline_data[step] = {
                            "status": "failed",
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        }
                        raise Exception(f"Step {step} failed after {retry_count} attempts: {str(e)}")
                    
                    # Wait before retrying
                    await asyncio.sleep(2 ** retry_count)  # Exponential backoff
        
        # Compile final result
        final_result = {
            "run_id": run_id,
            "sport": sport,
            "episode_type": episode_type,
            "title": step_results.get("script_generation", {}).get("title", "Untitled Episode"),
            "description": step_results.get("script_generation", {}).get("description", ""),
            "audio_files": step_results.get("audio_production", {}).get("output_files", []),
            "duration": step_results.get("audio_production", {}).get("duration", 0),
            "created_at": datetime.now().isoformat(),
            "pipeline_data": pipeline_data
        }
        
        return final_result
    
    def _prepare_step_input(self, step: str, sport: str, episode_type: str,
                          event_id: Optional[str], custom_parameters: Dict[str, Any],
                          previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare input data for a pipeline step.
        
        Args:
            step: Pipeline step name
            sport: Sport type
            episode_type: Type of episode
            event_id: Specific event identifier
            custom_parameters: Custom parameters
            previous_results: Results from previous steps
            
        Returns:
            Input data for the step
        """
        # Common parameters
        step_params = custom_parameters.get(step, {})
        
        # Step-specific input preparation
        if step == "research":
            return {
                "sport": sport,
                "event_type": episode_type.replace("_review", "").replace("_analysis", ""),
                "event_id": event_id,
                "force_refresh": step_params.get("force_refresh", False)
            }
        
        elif step == "content_planning":
            return {
                "research_data": previous_results.get("research", {}),
                "episode_type": episode_type,
                "custom_parameters": step_params
            }
        
        elif step == "script_generation":
            return {
                "content_outline": previous_results.get("content_planning", {}),
                "custom_parameters": step_params
            }
        
        elif step == "voice_synthesis":
            return {
                "script": previous_results.get("script_generation", {}),
                "custom_parameters": step_params
            }
        
        elif step == "audio_production":
            return {
                "audio_metadata": previous_results.get("voice_synthesis", {}),
                "script": previous_results.get("script_generation", {}),
                "custom_parameters": step_params
            }
        
        # Default empty input if step not recognized
        return {}
    
    def _validate_step_result(self, step: str, result: Dict[str, Any]) -> None:
        """
        Validate the result of a pipeline step.
        
        Args:
            step: Pipeline step name
            result: Step result to validate
            
        Raises:
            ValueError: If validation fails
        """
        # Check for error in result
        if "error" in result:
            raise ValueError(f"Step {step} returned error: {result['error']}")
        
        # Step-specific validation
        if step == "research":
            # Validate research data
            articles = result.get("articles", [])
            if len(articles) < self.config["quality_thresholds"]["min_research_sources"]:
                raise ValueError(f"Insufficient research sources: {len(articles)} < {self.config['quality_thresholds']['min_research_sources']}")
        
        elif step == "script_generation":
            # Validate script
            word_count = result.get("word_count", 0)
            if word_count < self.config["quality_thresholds"]["min_script_word_count"]:
                raise ValueError(f"Script too short: {word_count} words < {self.config['quality_thresholds']['min_script_word_count']}")
    
    def _save_run_record(self, run_record: Dict[str, Any]) -> None:
        """
        Save the run record to disk.
        
        Args:
            run_record: Run record to save
        """
        run_id = run_record["run_id"]
        filename = f"{run_id}.json"
        filepath = os.path.join(self.run_history_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(run_record, f, indent=2)
        
        self.logger.info(f"Saved run record to {filepath}")
    
    async def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """
        Get the status of a specific run.
        
        Args:
            run_id: Run identifier
            
        Returns:
            Run status information
        """
        filename = f"{run_id}.json"
        filepath = os.path.join(self.run_history_dir, filename)
        
        if not os.path.exists(filepath):
            return {"error": f"Run not found: {run_id}"}
        
        with open(filepath, "r") as f:
            run_record = json.load(f)
        
        return run_record
    
    async def list_runs(self, limit: int = 10, sport: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List recent runs, optionally filtered by sport.
        
        Args:
            limit: Maximum number of runs to return
            sport: Filter by sport
            
        Returns:
            List of run summaries
        """
        runs = []
        
        # List all run files
        run_files = os.listdir(self.run_history_dir)
        run_files.sort(reverse=True)  # Most recent first
        
        # Load and filter runs
        count = 0
        for filename in run_files:
            if not filename.endswith(".json"):
                continue
                
            filepath = os.path.join(self.run_history_dir, filename)
            
            with open(filepath, "r") as f:
                run_record = json.load(f)
            
            # Filter by sport if specified
            if sport and run_record.get("sport") != sport:
                continue
            
            # Add summary to list
            runs.append({
                "run_id": run_record.get("run_id"),
                "sport": run_record.get("sport"),
                "episode_type": run_record.get("episode_type"),
                "status": run_record.get("status"),
                "started_at": run_record.get("started_at"),
                "completed_at": run_record.get("completed_at")
            })
            
            count += 1
            if count >= limit:
                break
        
        return runs
