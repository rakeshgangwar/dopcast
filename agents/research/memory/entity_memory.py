"""
Entity memory component for the Research Agent.
Provides persistent storage and retrieval of entity information.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class EntityMemory:
    """
    Entity memory for tracking and retrieving information about entities.
    """
    
    def __init__(self, memory_dir: str):
        """
        Initialize the entity memory.
        
        Args:
            memory_dir: Directory to store entity memory files
        """
        self.logger = logging.getLogger("dopcast.research.entity_memory")
        self.memory_dir = memory_dir
        self.entities = {
            "people": {},  # drivers/riders
            "teams": {},
            "tracks": {},
            "events": {}
        }
        
        # Ensure memory directory exists
        os.makedirs(self.memory_dir, exist_ok=True)
        
        # Load existing entity memory
        self._load_memory()
    
    def _load_memory(self):
        """Load entity memory from disk."""
        memory_file = os.path.join(self.memory_dir, "entity_memory.json")
        
        if os.path.exists(memory_file):
            try:
                with open(memory_file, "r", encoding="utf-8") as f:
                    self.entities = json.load(f)
                
                self.logger.info(f"Loaded entity memory from disk")
            except Exception as e:
                self.logger.error(f"Error loading entity memory: {e}")
                self.entities = {
                    "people": {},
                    "teams": {},
                    "tracks": {},
                    "events": {}
                }
    
    def _save_memory(self):
        """Save entity memory to disk."""
        memory_file = os.path.join(self.memory_dir, "entity_memory.json")
        
        try:
            with open(memory_file, "w", encoding="utf-8") as f:
                json.dump(self.entities, f, indent=2)
            
            self.logger.info(f"Saved entity memory to disk")
        except Exception as e:
            self.logger.error(f"Error saving entity memory: {e}")
    
    def update_entities(self, new_entities: Dict[str, List[Dict[str, Any]]], sport: str) -> None:
        """
        Update entity memory with new entity information.
        
        Args:
            new_entities: Dictionary of entity types and their mentions
            sport: Sport type
        """
        timestamp = datetime.now().isoformat()
        
        for entity_type, entities_list in new_entities.items():
            for entity_info in entities_list:
                entity_name = entity_info["name"]
                
                # Initialize entity if not exists
                if entity_name not in self.entities[entity_type]:
                    self.entities[entity_type][entity_name] = {
                        "name": entity_name,
                        "sports": [],
                        "first_seen": timestamp,
                        "last_seen": timestamp,
                        "mention_count": 0,
                        "recent_mentions": []
                    }
                
                entity_data = self.entities[entity_type][entity_name]
                
                # Update entity data
                entity_data["last_seen"] = timestamp
                entity_data["mention_count"] += entity_info["count"]
                
                # Add sport if not already present
                if sport not in entity_data["sports"]:
                    entity_data["sports"].append(sport)
                
                # Add recent mentions (limited to 5)
                for mention in entity_info.get("mentions", [])[:5]:
                    entity_data["recent_mentions"].append({
                        "timestamp": timestamp,
                        "context": mention.get("context", ""),
                        "article_id": mention.get("article_id", "")
                    })
                
                # Keep only the 10 most recent mentions
                entity_data["recent_mentions"] = entity_data["recent_mentions"][-10:]
        
        # Save updated memory
        self._save_memory()
    
    def get_entity(self, entity_type: str, entity_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific entity.
        
        Args:
            entity_type: Type of entity (people, teams, tracks, events)
            entity_name: Name of the entity
            
        Returns:
            Entity information or None if not found
        """
        if entity_type not in self.entities or entity_name not in self.entities[entity_type]:
            return None
        
        return self.entities[entity_type][entity_name]
    
    def get_entities_by_sport(self, entity_type: str, sport: str) -> List[Dict[str, Any]]:
        """
        Get all entities of a specific type for a sport.
        
        Args:
            entity_type: Type of entity (people, teams, tracks, events)
            sport: Sport type
            
        Returns:
            List of entity information
        """
        if entity_type not in self.entities:
            return []
        
        return [
            entity_data for entity_data in self.entities[entity_type].values()
            if sport in entity_data["sports"]
        ]
    
    def get_top_entities(self, entity_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the top entities of a specific type by mention count.
        
        Args:
            entity_type: Type of entity (people, teams, tracks, events)
            limit: Maximum number of entities to return
            
        Returns:
            List of top entity information
        """
        if entity_type not in self.entities:
            return []
        
        # Sort entities by mention count
        sorted_entities = sorted(
            self.entities[entity_type].values(),
            key=lambda x: x["mention_count"],
            reverse=True
        )
        
        return sorted_entities[:limit]
