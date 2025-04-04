"""
Template memory component for the Content Planning Agent.
Provides storage and retrieval of episode templates.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class TemplateMemory:
    """
    Memory for storing and retrieving episode templates.
    """
    
    def __init__(self, content_dir: str):
        """
        Initialize the template memory.
        
        Args:
            content_dir: Directory to store content templates
        """
        self.logger = logging.getLogger("dopcast.content_planning.template_memory")
        self.content_dir = content_dir
        self.templates_dir = os.path.join(content_dir, "templates")
        self.index_file = os.path.join(content_dir, "template_index.json")
        self.template_index = {}
        
        # Ensure templates directory exists
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Load existing index
        self._load_index()
        
        # Initialize default templates
        self._initialize_default_templates()
    
    def _load_index(self):
        """Load the template index from disk."""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    self.template_index = json.load(f)
                
                self.logger.info(f"Loaded template index with {len(self.template_index)} entries")
            except Exception as e:
                self.logger.error(f"Error loading template index: {e}")
                self.template_index = {}
    
    def _save_index(self):
        """Save the template index to disk."""
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self.template_index, f, indent=2)
            
            self.logger.info(f"Saved template index with {len(self.template_index)} entries")
        except Exception as e:
            self.logger.error(f"Error saving template index: {e}")
    
    def _initialize_default_templates(self):
        """Initialize default episode templates."""
        default_templates = {
            "race_review": {
                "sections": [
                    {"name": "intro", "duration": 60, "priority": "high"},
                    {"name": "race_summary", "duration": 180, "priority": "high"},
                    {"name": "key_moments", "duration": 240, "priority": "high"},
                    {"name": "driver_performances", "duration": 300, "priority": "medium"},
                    {"name": "team_strategies", "duration": 240, "priority": "medium"},
                    {"name": "technical_insights", "duration": 180, "priority": "low"},
                    {"name": "championship_implications", "duration": 120, "priority": "high"},
                    {"name": "controversy_discussion", "duration": 180, "priority": "conditional"},
                    {"name": "next_race_preview", "duration": 120, "priority": "medium"},
                    {"name": "outro", "duration": 60, "priority": "high"}
                ],
                "total_duration": 1800  # 30 minutes
            },
            "news_update": {
                "sections": [
                    {"name": "intro", "duration": 30, "priority": "high"},
                    {"name": "headlines", "duration": 120, "priority": "high"},
                    {"name": "detailed_stories", "duration": 300, "priority": "high"},
                    {"name": "analysis", "duration": 180, "priority": "medium"},
                    {"name": "outro", "duration": 30, "priority": "high"}
                ],
                "total_duration": 660  # 11 minutes
            },
            "technical_deep_dive": {
                "sections": [
                    {"name": "intro", "duration": 60, "priority": "high"},
                    {"name": "topic_introduction", "duration": 120, "priority": "high"},
                    {"name": "technical_explanation", "duration": 300, "priority": "high"},
                    {"name": "team_approaches", "duration": 240, "priority": "medium"},
                    {"name": "performance_impact", "duration": 180, "priority": "medium"},
                    {"name": "historical_context", "duration": 120, "priority": "low"},
                    {"name": "future_developments", "duration": 120, "priority": "medium"},
                    {"name": "outro", "duration": 60, "priority": "high"}
                ],
                "total_duration": 1200  # 20 minutes
            }
        }
        
        # Add default templates if they don't exist
        for template_id, template in default_templates.items():
            if template_id not in self.template_index:
                # Save template to file
                filepath = os.path.join(self.templates_dir, f"{template_id}.json")
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(template, f, indent=2)
                
                # Add to index
                self.template_index[template_id] = {
                    "id": template_id,
                    "name": template_id.replace("_", " ").title(),
                    "created_at": datetime.now().isoformat(),
                    "is_default": True,
                    "filepath": filepath
                }
        
        # Save index if we added any templates
        if len(self.template_index) > 0:
            self._save_index()
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a template from memory.
        
        Args:
            template_id: Template ID
            
        Returns:
            Episode template or None if not found
        """
        if template_id not in self.template_index:
            return None
        
        index_entry = self.template_index[template_id]
        filepath = index_entry["filepath"]
        
        if not os.path.exists(filepath):
            self.logger.warning(f"Template file not found: {filepath}")
            return None
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                template = json.load(f)
            
            return template
        except Exception as e:
            self.logger.error(f"Error loading template: {e}")
            return None
    
    def get_all_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all templates.
        
        Returns:
            Dictionary of template IDs and their index entries
        """
        return self.template_index
    
    def add_template(self, template_id: str, template: Dict[str, Any], 
                   name: Optional[str] = None) -> str:
        """
        Add a template to memory.
        
        Args:
            template_id: Template ID
            template: Episode template
            name: Template name (optional)
            
        Returns:
            Template ID
        """
        # Generate filepath
        filepath = os.path.join(self.templates_dir, f"{template_id}.json")
        
        # Save template to file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(template, f, indent=2)
        
        # Add to index
        self.template_index[template_id] = {
            "id": template_id,
            "name": name or template_id.replace("_", " ").title(),
            "created_at": datetime.now().isoformat(),
            "is_default": False,
            "filepath": filepath
        }
        
        # Save index
        self._save_index()
        
        return template_id
