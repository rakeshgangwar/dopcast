"""
Script memory component for the Script Generation Agent.
Provides storage and retrieval of generated scripts.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class ScriptMemory:
    """
    Memory for storing and retrieving generated scripts.
    """
    
    def __init__(self, content_dir: str):
        """
        Initialize the script memory.
        
        Args:
            content_dir: Directory to store scripts
        """
        self.logger = logging.getLogger("dopcast.script_generation.script_memory")
        self.content_dir = content_dir
        self.scripts_dir = os.path.join(content_dir, "scripts")
        self.index_file = os.path.join(content_dir, "script_index.json")
        self.script_index = {}
        
        # Ensure scripts directory exists
        os.makedirs(self.scripts_dir, exist_ok=True)
        
        # Load existing index
        self._load_index()
    
    def _load_index(self):
        """Load the script index from disk."""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    self.script_index = json.load(f)
                
                self.logger.info(f"Loaded script index with {len(self.script_index)} entries")
            except Exception as e:
                self.logger.error(f"Error loading script index: {e}")
                self.script_index = {}
    
    def _save_index(self):
        """Save the script index to disk."""
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self.script_index, f, indent=2)
            
            self.logger.info(f"Saved script index with {len(self.script_index)} entries")
        except Exception as e:
            self.logger.error(f"Error saving script index: {e}")
    
    def add_script(self, script: Dict[str, Any], file_paths: Dict[str, str]) -> str:
        """
        Add a script to memory.
        
        Args:
            script: Complete podcast script
            file_paths: Paths to script files
            
        Returns:
            Script ID
        """
        # Generate a unique ID for the script
        script_id = f"{script.get('sport', 'unknown')}_{script.get('episode_type', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Add to index
        self.script_index[script_id] = {
            "id": script_id,
            "title": script.get("title", "Untitled Episode"),
            "description": script.get("description", ""),
            "created_at": script.get("created_at", datetime.now().isoformat()),
            "hosts": script.get("hosts", []),
            "duration": script.get("total_duration", 0),
            "word_count": script.get("word_count", 0),
            "file_paths": file_paths
        }
        
        # Save index
        self._save_index()
        
        return script_id
    
    def get_script(self, script_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a script from memory.
        
        Args:
            script_id: Script ID
            
        Returns:
            Script or None if not found
        """
        if script_id not in self.script_index:
            return None
        
        index_entry = self.script_index[script_id]
        json_path = os.path.join(self.content_dir, index_entry["file_paths"]["json"])
        
        if not os.path.exists(json_path):
            self.logger.warning(f"Script file not found: {json_path}")
            return None
        
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                script = json.load(f)
            
            return script
        except Exception as e:
            self.logger.error(f"Error loading script: {e}")
            return None
    
    def get_recent_scripts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent scripts.
        
        Args:
            limit: Maximum number of scripts to return
            
        Returns:
            List of script index entries
        """
        # Sort by created_at (newest first)
        sorted_scripts = sorted(
            self.script_index.values(),
            key=lambda x: x["created_at"],
            reverse=True
        )
        
        return sorted_scripts[:limit]
