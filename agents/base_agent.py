import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseAgent(ABC):
    """
    Base class for all DopCast AI agents.
    Provides common functionality and enforces the agent interface.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base agent.
        
        Args:
            name: Unique identifier for the agent
            config: Configuration parameters for the agent
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"dopcast.agent.{name}")
        self.logger.setLevel(logging.INFO)
        
        # Initialize agent state
        self.state = {
            "status": "initialized",
            "last_run": None,
            "metrics": {}
        }
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data and produce output.
        Must be implemented by all agent subclasses.
        
        Args:
            input_data: Input data for the agent to process
            
        Returns:
            Processed output data
        """
        pass
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the agent with input data and handle logging and errors.
        
        Args:
            input_data: Input data for the agent to process
            
        Returns:
            Processed output data
        """
        self.logger.info(f"Agent {self.name} starting processing")
        self.state["status"] = "running"
        
        try:
            result = await self.process(input_data)
            self.state["status"] = "completed"
            self.logger.info(f"Agent {self.name} completed processing")
            return result
        except Exception as e:
            self.state["status"] = "error"
            self.logger.error(f"Agent {self.name} encountered an error: {str(e)}")
            raise
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the agent.
        
        Returns:
            Current agent state
        """
        return self.state
    
    def update_config(self, config_updates: Dict[str, Any]) -> None:
        """
        Update the agent's configuration.
        
        Args:
            config_updates: Configuration parameters to update
        """
        self.config.update(config_updates)
        self.logger.info(f"Agent {self.name} configuration updated")
