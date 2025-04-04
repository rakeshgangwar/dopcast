"""
Sound effect manager tool for the Script Generation Agent.
Provides enhanced sound effect management capabilities.
"""

import logging
import random
from typing import Dict, Any, List, Optional

class SoundEffectManagerTool:
    """
    Enhanced sound effect manager tool for adding sound effects to scripts.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the sound effect manager tool.
        
        Args:
            config: Configuration parameters
        """
        self.logger = logging.getLogger("dopcast.script_generation.sound_effect_manager")
        self.config = config or {}
        
        # Default sound effect library
        self.default_effects = {
            "intro": ["Theme music", "Opening jingle", "Energetic intro music"],
            "outro": ["Closing theme", "Fade-out music", "Gentle outro melody"],
            "transition": ["Quick transition sound", "Swoosh effect", "Short musical bridge"],
            "highlight": ["Dramatic impact", "Tension builder", "Attention-grabbing sound"],
            "race": ["Engine revving", "Race start sounds", "Crowd cheering at race"],
            "crash": ["Impact sound", "Dramatic crash effect", "Tires screeching"],
            "ambient": ["Pit lane ambience", "Crowd murmur", "Track atmosphere"]
        }
    
    def add_section_sound_effects(self, section: Dict[str, Any], 
                                include_sound_effects: bool) -> List[Dict[str, Any]]:
        """
        Add appropriate sound effects to a script section.
        
        Args:
            section: Script section
            include_sound_effects: Whether to include sound effects
            
        Returns:
            List of sound effects
        """
        if not include_sound_effects:
            return []
        
        section_name = section.get("name", "unnamed_section")
        dialogue = section.get("dialogue", [])
        sound_effects = []
        
        # Add section-specific sound effects
        if section_name == "intro":
            sound_effects.append({
                "type": "intro",
                "description": random.choice(self.default_effects["intro"]),
                "position": 0
            })
        
        elif section_name == "outro":
            sound_effects.append({
                "type": "outro",
                "description": random.choice(self.default_effects["outro"]),
                "position": len(dialogue) - 1 if dialogue else 0
            })
        
        elif section_name == "key_moments" and len(dialogue) > 2:
            sound_effects.append({
                "type": "highlight",
                "description": random.choice(self.default_effects["highlight"]),
                "position": 2  # After the first talking point
            })
        
        elif section_name == "race_summary" and len(dialogue) > 1:
            sound_effects.append({
                "type": "ambient",
                "description": random.choice(self.default_effects["ambient"]),
                "position": 1
            })
        
        # Add transitions between hosts if there are multiple speakers
        speakers = [line.get("speaker") for line in dialogue if line.get("speaker") not in ["INTRO", "OUTRO", "TRANSITION"]]
        unique_speakers = set(speakers)
        
        if len(unique_speakers) > 1 and len(dialogue) > 4:
            # Find a good position for a transition effect (around the middle)
            mid_position = len(dialogue) // 2
            for i in range(mid_position - 1, mid_position + 2):
                if 0 <= i < len(dialogue) - 1:
                    if dialogue[i].get("speaker") != dialogue[i+1].get("speaker"):
                        sound_effects.append({
                            "type": "transition",
                            "description": random.choice(self.default_effects["transition"]),
                            "position": i
                        })
                        break
        
        return sound_effects
    
    def add_transition_effect(self, section_name: str) -> Dict[str, Any]:
        """
        Add a transition effect for a section.
        
        Args:
            section_name: Name of the section
            
        Returns:
            Transition effect
        """
        return {
            "speaker": "TRANSITION",
            "text": f"[Transition to {section_name.replace('_', ' ').title()} section]"
        }
    
    def get_effect_description(self, effect_type: str) -> str:
        """
        Get a description for a sound effect type.
        
        Args:
            effect_type: Type of sound effect
            
        Returns:
            Description of the sound effect
        """
        if effect_type in self.default_effects:
            return random.choice(self.default_effects[effect_type])
        else:
            return f"{effect_type.capitalize()} sound effect"
