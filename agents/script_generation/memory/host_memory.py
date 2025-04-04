"""
Host memory component for the Script Generation Agent.
Provides storage and retrieval of host personalities.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class HostMemory:
    """
    Memory for storing and retrieving host personalities.
    """
    
    def __init__(self, content_dir: str):
        """
        Initialize the host memory.
        
        Args:
            content_dir: Directory to store host data
        """
        self.logger = logging.getLogger("dopcast.script_generation.host_memory")
        self.content_dir = content_dir
        self.hosts_dir = os.path.join(content_dir, "hosts")
        self.index_file = os.path.join(content_dir, "host_index.json")
        self.host_index = {}
        
        # Ensure hosts directory exists
        os.makedirs(self.hosts_dir, exist_ok=True)
        
        # Load existing index
        self._load_index()
        
        # Initialize default hosts
        self._initialize_default_hosts()
    
    def _load_index(self):
        """Load the host index from disk."""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    self.host_index = json.load(f)
                
                self.logger.info(f"Loaded host index with {len(self.host_index)} entries")
            except Exception as e:
                self.logger.error(f"Error loading host index: {e}")
                self.host_index = {}
    
    def _save_index(self):
        """Save the host index to disk."""
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self.host_index, f, indent=2)
            
            self.logger.info(f"Saved host index with {len(self.host_index)} entries")
        except Exception as e:
            self.logger.error(f"Error saving host index: {e}")
    
    def _initialize_default_hosts(self):
        """Initialize default host personalities."""
        default_hosts = [
            {
                "name": "Mukesh",
                "role": "lead_host",
                "style": "enthusiastic",
                "expertise": "general",
                "catchphrases": ["Absolutely incredible!", "Let's dive into this.", "What a moment that was!"]
            },
            {
                "name": "Rakesh",
                "role": "technical_expert",
                "style": "analytical",
                "expertise": "technical",
                "catchphrases": ["If we look at the data...", "Technically speaking...", "The numbers tell us..."]
            }
        ]
        
        # Add default hosts if they don't exist
        for host in default_hosts:
            if host["name"] not in self.host_index:
                # Save host to file
                filepath = os.path.join(self.hosts_dir, f"{host['name'].lower()}.json")
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(host, f, indent=2)
                
                # Add to index
                self.host_index[host["name"]] = {
                    "name": host["name"],
                    "role": host["role"],
                    "style": host["style"],
                    "created_at": datetime.now().isoformat(),
                    "is_default": True,
                    "filepath": filepath
                }
        
        # Save index if we added any hosts
        if len(self.host_index) > 0:
            self._save_index()
    
    def get_host(self, host_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a host personality from memory.
        
        Args:
            host_name: Host name
            
        Returns:
            Host personality or None if not found
        """
        if host_name not in self.host_index:
            return None
        
        index_entry = self.host_index[host_name]
        filepath = index_entry["filepath"]
        
        if not os.path.exists(filepath):
            self.logger.warning(f"Host file not found: {filepath}")
            return None
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                host = json.load(f)
            
            return host
        except Exception as e:
            self.logger.error(f"Error loading host: {e}")
            return None
    
    def get_all_hosts(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all host personalities.
        
        Returns:
            Dictionary of host names and their index entries
        """
        return self.host_index
    
    def add_host(self, host: Dict[str, Any]) -> str:
        """
        Add a host personality to memory.
        
        Args:
            host: Host personality
            
        Returns:
            Host name
        """
        host_name = host["name"]
        
        # Generate filepath
        filepath = os.path.join(self.hosts_dir, f"{host_name.lower()}.json")
        
        # Save host to file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(host, f, indent=2)
        
        # Add to index
        self.host_index[host_name] = {
            "name": host_name,
            "role": host.get("role", "co_host"),
            "style": host.get("style", "neutral"),
            "created_at": datetime.now().isoformat(),
            "is_default": False,
            "filepath": filepath
        }
        
        # Save index
        self._save_index()
        
        return host_name
    
    def get_hosts_by_role(self, role: str) -> List[Dict[str, Any]]:
        """
        Get host personalities by role.
        
        Args:
            role: Host role
            
        Returns:
            List of host personalities
        """
        hosts = []
        
        for host_name, index_entry in self.host_index.items():
            if index_entry["role"] == role:
                host = self.get_host(host_name)
                if host:
                    hosts.append(host)
        
        return hosts
