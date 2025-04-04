"""
Research memory component for the Research Agent.
Provides long-term storage and retrieval of research information.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd

class ResearchMemory:
    """
    Research memory for tracking and retrieving historical research information.
    """
    
    def __init__(self, memory_dir: str):
        """
        Initialize the research memory.
        
        Args:
            memory_dir: Directory to store research memory files
        """
        self.logger = logging.getLogger("dopcast.research.research_memory")
        self.memory_dir = memory_dir
        self.memory = {
            "f1": {
                "events": {},
                "trends": [],
                "key_stories": []
            },
            "motogp": {
                "events": {},
                "trends": [],
                "key_stories": []
            }
        }
        
        # Ensure memory directory exists
        os.makedirs(self.memory_dir, exist_ok=True)
        
        # Load existing research memory
        self._load_memory()
    
    def _load_memory(self):
        """Load research memory from disk."""
        memory_file = os.path.join(self.memory_dir, "research_memory.json")
        
        if os.path.exists(memory_file):
            try:
                with open(memory_file, "r", encoding="utf-8") as f:
                    self.memory = json.load(f)
                
                self.logger.info(f"Loaded research memory from disk")
            except Exception as e:
                self.logger.error(f"Error loading research memory: {e}")
                # Keep default memory structure
    
    def _save_memory(self):
        """Save research memory to disk."""
        memory_file = os.path.join(self.memory_dir, "research_memory.json")
        
        try:
            with open(memory_file, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, indent=2)
            
            self.logger.info(f"Saved research memory to disk")
        except Exception as e:
            self.logger.error(f"Error saving research memory: {e}")
    
    def add_event_data(self, sport: str, event_type: str, event_id: str, data: Dict[str, Any]) -> None:
        """
        Add event data to research memory.
        
        Args:
            sport: Sport type
            event_type: Type of event
            event_id: Event identifier
            data: Event data
        """
        if sport not in self.memory:
            self.memory[sport] = {
                "events": {},
                "trends": [],
                "key_stories": []
            }
        
        # Create event key
        event_key = f"{event_id}_{event_type}"
        
        # Add event data
        self.memory[sport]["events"][event_key] = {
            "event_id": event_id,
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        # Save updated memory
        self._save_memory()
    
    def get_event_data(self, sport: str, event_type: str, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get event data from research memory.
        
        Args:
            sport: Sport type
            event_type: Type of event
            event_id: Event identifier
            
        Returns:
            Event data or None if not found
        """
        if sport not in self.memory:
            return None
        
        event_key = f"{event_id}_{event_type}"
        
        if event_key not in self.memory[sport]["events"]:
            return None
        
        return self.memory[sport]["events"][event_key]["data"]
    
    def add_trend(self, sport: str, trend: Dict[str, Any]) -> None:
        """
        Add a trend to research memory.
        
        Args:
            sport: Sport type
            trend: Trend information
        """
        if sport not in self.memory:
            self.memory[sport] = {
                "events": {},
                "trends": [],
                "key_stories": []
            }
        
        # Add timestamp to trend
        trend["timestamp"] = datetime.now().isoformat()
        
        # Add trend to memory
        self.memory[sport]["trends"].append(trend)
        
        # Keep only the 20 most recent trends
        self.memory[sport]["trends"] = self.memory[sport]["trends"][-20:]
        
        # Save updated memory
        self._save_memory()
    
    def get_trends(self, sport: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get trends from research memory.
        
        Args:
            sport: Sport type
            limit: Maximum number of trends to return
            
        Returns:
            List of trends
        """
        if sport not in self.memory:
            return []
        
        # Return the most recent trends
        return self.memory[sport]["trends"][-limit:]
    
    def add_key_story(self, sport: str, story: Dict[str, Any]) -> None:
        """
        Add a key story to research memory.
        
        Args:
            sport: Sport type
            story: Story information
        """
        if sport not in self.memory:
            self.memory[sport] = {
                "events": {},
                "trends": [],
                "key_stories": []
            }
        
        # Add timestamp to story
        story["timestamp"] = datetime.now().isoformat()
        
        # Add story to memory
        self.memory[sport]["key_stories"].append(story)
        
        # Keep only the 50 most recent key stories
        self.memory[sport]["key_stories"] = self.memory[sport]["key_stories"][-50:]
        
        # Save updated memory
        self._save_memory()
    
    def get_key_stories(self, sport: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get key stories from research memory.
        
        Args:
            sport: Sport type
            limit: Maximum number of stories to return
            
        Returns:
            List of key stories
        """
        if sport not in self.memory:
            return []
        
        # Return the most recent key stories
        return self.memory[sport]["key_stories"][-limit:]
    
    def get_historical_context(self, sport: str, entity_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get historical context for a sport or entity.
        
        Args:
            sport: Sport type
            entity_name: Optional entity name to filter by
            
        Returns:
            Historical context information
        """
        if sport not in self.memory:
            return {
                "events": [],
                "trends": [],
                "key_stories": []
            }
        
        # Get all events
        events = list(self.memory[sport]["events"].values())
        
        # Get trends and key stories
        trends = self.memory[sport]["trends"]
        key_stories = self.memory[sport]["key_stories"]
        
        # Filter by entity if provided
        if entity_name:
            # Filter events that mention the entity
            events = [
                event for event in events
                if entity_name in json.dumps(event["data"])
            ]
            
            # Filter trends that mention the entity
            trends = [
                trend for trend in trends
                if entity_name in json.dumps(trend)
            ]
            
            # Filter key stories that mention the entity
            key_stories = [
                story for story in key_stories
                if entity_name in json.dumps(story)
            ]
        
        return {
            "events": events[-10:],  # Last 10 events
            "trends": trends[-5:],   # Last 5 trends
            "key_stories": key_stories[-5:]  # Last 5 key stories
        }
