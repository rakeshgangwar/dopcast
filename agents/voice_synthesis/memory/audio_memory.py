"""
Audio memory component for the Voice Synthesis Agent.
Provides storage and retrieval of generated audio.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class AudioMemory:
    """
    Memory for storing and retrieving generated audio.
    """
    
    def __init__(self, audio_dir: str):
        """
        Initialize the audio memory.
        
        Args:
            audio_dir: Directory to store audio data
        """
        self.logger = logging.getLogger("dopcast.voice_synthesis.audio_memory")
        self.audio_dir = audio_dir
        self.index_file = os.path.join(audio_dir, "audio_index.json")
        self.audio_index = {}
        
        # Ensure audio directory exists
        os.makedirs(audio_dir, exist_ok=True)
        
        # Load existing index
        self._load_index()
    
    def _load_index(self):
        """Load the audio index from disk."""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    self.audio_index = json.load(f)
                
                self.logger.info(f"Loaded audio index with {len(self.audio_index)} entries")
            except Exception as e:
                self.logger.error(f"Error loading audio index: {e}")
                self.audio_index = {}
    
    def _save_index(self):
        """Save the audio index to disk."""
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self.audio_index, f, indent=2)
            
            self.logger.info(f"Saved audio index with {len(self.audio_index)} entries")
        except Exception as e:
            self.logger.error(f"Error saving audio index: {e}")
    
    def add_audio(self, audio_metadata: Dict[str, Any]) -> str:
        """
        Add audio metadata to memory.
        
        Args:
            audio_metadata: Audio metadata
            
        Returns:
            Audio ID
        """
        # Generate a unique ID for the audio
        audio_id = f"{audio_metadata.get('title', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Add to index
        self.audio_index[audio_id] = {
            "id": audio_id,
            "title": audio_metadata.get("title", "Untitled Episode"),
            "created_at": datetime.now().isoformat(),
            "duration": audio_metadata.get("total_duration", 0),
            "main_file": audio_metadata.get("main_file", ""),
            "segment_count": len(audio_metadata.get("segment_files", []))
        }
        
        # Save index
        self._save_index()
        
        return audio_id
    
    def get_audio(self, audio_id: str) -> Optional[Dict[str, Any]]:
        """
        Get audio metadata from memory.
        
        Args:
            audio_id: Audio ID
            
        Returns:
            Audio metadata or None if not found
        """
        if audio_id not in self.audio_index:
            return None
        
        return self.audio_index[audio_id]
    
    def get_recent_audio(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent audio metadata.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of audio metadata
        """
        # Sort by created_at (newest first)
        sorted_audio = sorted(
            self.audio_index.values(),
            key=lambda x: x["created_at"],
            reverse=True
        )
        
        return sorted_audio[:limit]
