"""
Outline memory component for the Content Planning Agent.
Provides storage and retrieval of episode outlines.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class OutlineMemory:
    """
    Memory for storing and retrieving episode outlines.
    """
    
    def __init__(self, content_dir: str):
        """
        Initialize the outline memory.
        
        Args:
            content_dir: Directory to store content outlines
        """
        self.logger = logging.getLogger("dopcast.content_planning.outline_memory")
        self.content_dir = content_dir
        self.outlines_dir = os.path.join(content_dir, "outlines")
        self.index_file = os.path.join(content_dir, "outline_index.json")
        self.outline_index = {}
        
        # Ensure outlines directory exists
        os.makedirs(self.outlines_dir, exist_ok=True)
        
        # Load existing index
        self._load_index()
    
    def _load_index(self):
        """Load the outline index from disk."""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    self.outline_index = json.load(f)
                
                self.logger.info(f"Loaded outline index with {len(self.outline_index)} entries")
            except Exception as e:
                self.logger.error(f"Error loading outline index: {e}")
                self.outline_index = {}
    
    def _save_index(self):
        """Save the outline index to disk."""
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self.outline_index, f, indent=2)
            
            self.logger.info(f"Saved outline index with {len(self.outline_index)} entries")
        except Exception as e:
            self.logger.error(f"Error saving outline index: {e}")
    
    def add_outline(self, outline: Dict[str, Any], filepath: str) -> str:
        """
        Add an outline to memory.
        
        Args:
            outline: Episode outline
            filepath: Path to the outline file
            
        Returns:
            Outline ID
        """
        # Generate a unique ID for the outline
        outline_id = f"{outline.get('sport', 'unknown')}_{outline.get('episode_type', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Add to index
        self.outline_index[outline_id] = {
            "id": outline_id,
            "sport": outline.get("sport", "unknown"),
            "episode_type": outline.get("episode_type", "unknown"),
            "title": outline.get("title", "Untitled"),
            "created_at": outline.get("created_at", datetime.now().isoformat()),
            "filepath": filepath
        }
        
        # Save index
        self._save_index()
        
        return outline_id
    
    def get_outline(self, outline_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an outline from memory.
        
        Args:
            outline_id: Outline ID
            
        Returns:
            Episode outline or None if not found
        """
        if outline_id not in self.outline_index:
            return None
        
        index_entry = self.outline_index[outline_id]
        filepath = index_entry["filepath"]
        
        if not os.path.exists(filepath):
            self.logger.warning(f"Outline file not found: {filepath}")
            return None
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                outline = json.load(f)
            
            return outline
        except Exception as e:
            self.logger.error(f"Error loading outline: {e}")
            return None
    
    def get_outlines_by_sport(self, sport: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get outlines for a specific sport.
        
        Args:
            sport: Sport type
            limit: Maximum number of outlines to return
            
        Returns:
            List of outline index entries
        """
        # Filter by sport and sort by created_at (newest first)
        sport_outlines = [
            entry for entry in self.outline_index.values()
            if entry["sport"] == sport
        ]
        
        # Sort by created_at (newest first)
        sorted_outlines = sorted(
            sport_outlines,
            key=lambda x: x["created_at"],
            reverse=True
        )
        
        return sorted_outlines[:limit]
    
    def get_outlines_by_episode_type(self, episode_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get outlines for a specific episode type.
        
        Args:
            episode_type: Episode type
            limit: Maximum number of outlines to return
            
        Returns:
            List of outline index entries
        """
        # Filter by episode_type and sort by created_at (newest first)
        type_outlines = [
            entry for entry in self.outline_index.values()
            if entry["episode_type"] == episode_type
        ]
        
        # Sort by created_at (newest first)
        sorted_outlines = sorted(
            type_outlines,
            key=lambda x: x["created_at"],
            reverse=True
        )
        
        return sorted_outlines[:limit]
    
    def get_recent_outlines(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent outlines.
        
        Args:
            limit: Maximum number of outlines to return
            
        Returns:
            List of outline index entries
        """
        # Sort by created_at (newest first)
        sorted_outlines = sorted(
            self.outline_index.values(),
            key=lambda x: x["created_at"],
            reverse=True
        )
        
        return sorted_outlines[:limit]
