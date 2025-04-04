"""
Production memory component for the Audio Production Agent.
Provides storage and retrieval of production metadata.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class ProductionMemory:
    """
    Memory for storing and retrieving production metadata.
    """
    
    def __init__(self, production_dir: str):
        """
        Initialize the production memory.
        
        Args:
            production_dir: Directory to store production data
        """
        self.logger = logging.getLogger("dopcast.audio_production.production_memory")
        self.production_dir = production_dir
        self.index_file = os.path.join(production_dir, "production_index.json")
        self.production_index = {}
        
        # Ensure production directory exists
        os.makedirs(production_dir, exist_ok=True)
        
        # Load existing index
        self._load_index()
    
    def _load_index(self):
        """Load the production index from disk."""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    self.production_index = json.load(f)
                
                self.logger.info(f"Loaded production index with {len(self.production_index)} entries")
            except Exception as e:
                self.logger.error(f"Error loading production index: {e}")
                self.production_index = {}
    
    def _save_index(self):
        """Save the production index to disk."""
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self.production_index, f, indent=2)
            
            self.logger.info(f"Saved production index with {len(self.production_index)} entries")
        except Exception as e:
            self.logger.error(f"Error saving production index: {e}")
    
    def add_production(self, production_metadata: Dict[str, Any]) -> str:
        """
        Add production metadata to memory.
        
        Args:
            production_metadata: Production metadata
            
        Returns:
            Production ID
        """
        # Generate a unique ID for the production
        production_id = f"{production_metadata.get('title', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Save metadata to file
        metadata_filename = f"{production_id}.json"
        metadata_path = os.path.join(self.production_dir, metadata_filename)
        
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(production_metadata, f, indent=2)
        
        # Add to index
        self.production_index[production_id] = {
            "id": production_id,
            "title": production_metadata.get("title", "Untitled Episode"),
            "created_at": production_metadata.get("created_at", datetime.now().isoformat()),
            "duration": production_metadata.get("duration", 0),
            "file": production_metadata.get("file", {}).get("filename", ""),
            "metadata_path": metadata_path
        }
        
        # Save index
        self._save_index()
        
        return production_id
    
    def get_production(self, production_id: str) -> Optional[Dict[str, Any]]:
        """
        Get production metadata from memory.
        
        Args:
            production_id: Production ID
            
        Returns:
            Production metadata or None if not found
        """
        if production_id not in self.production_index:
            return None
        
        index_entry = self.production_index[production_id]
        metadata_path = index_entry["metadata_path"]
        
        if not os.path.exists(metadata_path):
            self.logger.warning(f"Production metadata file not found: {metadata_path}")
            return None
        
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                production_metadata = json.load(f)
            
            return production_metadata
        except Exception as e:
            self.logger.error(f"Error loading production metadata: {e}")
            return None
    
    def get_recent_productions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent production metadata.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of production metadata
        """
        # Sort by created_at (newest first)
        sorted_productions = sorted(
            self.production_index.values(),
            key=lambda x: x["created_at"],
            reverse=True
        )
        
        return sorted_productions[:limit]
