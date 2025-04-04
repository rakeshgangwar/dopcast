"""
Voice memory component for the Voice Synthesis Agent.
Provides storage and retrieval of voice profiles.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class VoiceMemory:
    """
    Memory for storing and retrieving voice profiles.
    """
    
    def __init__(self, audio_dir: str):
        """
        Initialize the voice memory.
        
        Args:
            audio_dir: Directory to store voice data
        """
        self.logger = logging.getLogger("dopcast.voice_synthesis.voice_memory")
        self.audio_dir = audio_dir
        self.voices_dir = os.path.join(audio_dir, "voices")
        self.index_file = os.path.join(audio_dir, "voice_index.json")
        self.voice_index = {}
        
        # Ensure voices directory exists
        os.makedirs(self.voices_dir, exist_ok=True)
        
        # Load existing index
        self._load_index()
        
        # Initialize default voices
        self._initialize_default_voices()
    
    def _load_index(self):
        """Load the voice index from disk."""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    self.voice_index = json.load(f)
                
                self.logger.info(f"Loaded voice index with {len(self.voice_index)} entries")
            except Exception as e:
                self.logger.error(f"Error loading voice index: {e}")
                self.voice_index = {}
    
    def _save_index(self):
        """Save the voice index to disk."""
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self.voice_index, f, indent=2)
            
            self.logger.info(f"Saved voice index with {len(self.voice_index)} entries")
        except Exception as e:
            self.logger.error(f"Error saving voice index: {e}")
    
    def _initialize_default_voices(self):
        """Initialize default voice profiles."""
        default_voices = [
            {
                "name": "Mukesh",
                "voice_id": "en",
                "gender": "male",
                "speaking_rate": 1.0,
                "pitch": 0.0,
                "volume": 1.0
            },
            {
                "name": "Rakesh",
                "voice_id": "en",
                "gender": "male",
                "speaking_rate": 1.1,
                "pitch": -1.0,
                "volume": 1.0
            }
        ]
        
        # Add default voices if they don't exist
        for voice in default_voices:
            if voice["name"] not in self.voice_index:
                # Save voice to file
                filepath = os.path.join(self.voices_dir, f"{voice['name'].lower()}.json")
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(voice, f, indent=2)
                
                # Add to index
                self.voice_index[voice["name"]] = {
                    "name": voice["name"],
                    "voice_id": voice["voice_id"],
                    "gender": voice["gender"],
                    "created_at": datetime.now().isoformat(),
                    "is_default": True,
                    "filepath": filepath
                }
        
        # Save index if we added any voices
        if len(self.voice_index) > 0:
            self._save_index()
    
    def get_voice(self, voice_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a voice profile from memory.
        
        Args:
            voice_name: Voice name
            
        Returns:
            Voice profile or None if not found
        """
        if voice_name not in self.voice_index:
            return None
        
        index_entry = self.voice_index[voice_name]
        filepath = index_entry["filepath"]
        
        if not os.path.exists(filepath):
            self.logger.warning(f"Voice file not found: {filepath}")
            return None
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                voice = json.load(f)
            
            return voice
        except Exception as e:
            self.logger.error(f"Error loading voice: {e}")
            return None
    
    def get_all_voices(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all voice profiles.
        
        Returns:
            Dictionary of voice names and their index entries
        """
        return self.voice_index
    
    def add_voice(self, voice: Dict[str, Any]) -> str:
        """
        Add a voice profile to memory.
        
        Args:
            voice: Voice profile
            
        Returns:
            Voice name
        """
        voice_name = voice["name"]
        
        # Generate filepath
        filepath = os.path.join(self.voices_dir, f"{voice_name.lower()}.json")
        
        # Save voice to file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(voice, f, indent=2)
        
        # Add to index
        self.voice_index[voice_name] = {
            "name": voice_name,
            "voice_id": voice.get("voice_id", "en"),
            "gender": voice.get("gender", "neutral"),
            "created_at": datetime.now().isoformat(),
            "is_default": False,
            "filepath": filepath
        }
        
        # Save index
        self._save_index()
        
        return voice_name
