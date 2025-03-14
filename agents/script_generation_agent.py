import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from agents.base_agent import BaseAgent

class ScriptGenerationAgent(BaseAgent):
    """
    Agent responsible for writing natural, engaging podcast scripts.
    Converts content outlines into conversational dialogue.
    """
    
    def __init__(self, name: str = "script_generation", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the script generation agent.
        
        Args:
            name: Agent identifier
            config: Configuration parameters
        """
        default_config = {
            "host_personalities": [
                {
                    "name": "Alex",
                    "role": "lead_host",
                    "style": "enthusiastic",
                    "expertise": "general",
                    "catchphrases": ["Absolutely incredible!", "Let's dive into this.", "What a moment that was!"]
                },
                {
                    "name": "Sam",
                    "role": "technical_expert",
                    "style": "analytical",
                    "expertise": "technical",
                    "catchphrases": ["If we look at the data...", "Technically speaking...", "The numbers tell us..."]
                }
            ],
            "script_style": "conversational",
            "include_sound_effects": True,
            "include_transitions": True,
            "humor_level": "moderate"  # none, light, moderate, heavy
        }
        
        # Merge default config with provided config
        merged_config = default_config.copy()
        if config:
            for key, value in config.items():
                if isinstance(value, dict) and key in merged_config and isinstance(merged_config[key], dict):
                    merged_config[key].update(value)
                else:
                    merged_config[key] = value
        
        super().__init__(name, merged_config)
        
        # Initialize content storage
        self.content_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "content")
        os.makedirs(os.path.join(self.content_dir, "scripts"), exist_ok=True)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process content outline and generate a podcast script.
        
        Args:
            input_data: Input data containing:
                - content_outline: Outline from the content planning agent
                - custom_parameters: Any custom parameters for this script
        
        Returns:
            Complete podcast script with dialogue and production notes
        """
        content_outline = input_data.get("content_outline", {})
        custom_parameters = input_data.get("custom_parameters", {})
        
        # Validate input data
        if not content_outline:
            self.logger.error("No content outline provided")
            return {"error": "No content outline provided"}
        
        # Apply any custom parameters
        script_style = custom_parameters.get("script_style", self.config["script_style"])
        humor_level = custom_parameters.get("humor_level", self.config["humor_level"])
        
        # Generate the script
        script = self._generate_script(content_outline, script_style, humor_level)
        
        # Save the script
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sport = content_outline.get("sport", "unknown")
        episode_type = content_outline.get("episode_type", "unknown")
        filename = f"{sport}_{episode_type}_{timestamp}.json"
        with open(os.path.join(self.content_dir, "scripts", filename), "w") as f:
            json.dump(script, f, indent=2)
        
        return script
    
    def _generate_script(self, content_outline: Dict[str, Any], 
                        script_style: str, humor_level: str) -> Dict[str, Any]:
        """
        Generate a complete podcast script from the content outline.
        
        Args:
            content_outline: Content outline from planning agent
            script_style: Style of the script
            humor_level: Level of humor to include
            
        Returns:
            Complete podcast script
        """
        title = content_outline.get("title", "Untitled Episode")
        description = content_outline.get("description", "")
        sections = content_outline.get("sections", [])
        host_count = content_outline.get("host_count", len(self.config["host_personalities"]))
        
        # Ensure we have enough host personalities
        host_personalities = self.config["host_personalities"][:host_count]
        if len(host_personalities) < host_count:
            # Create generic hosts if needed
            for i in range(len(host_personalities), host_count):
                host_personalities.append({
                    "name": f"Host {i+1}",
                    "role": "co_host",
                    "style": "neutral",
                    "expertise": "general",
                    "catchphrases": []
                })
        
        # Create script sections
        script_sections = []
        for section in sections:
            script_section = self._generate_section_script(
                section, host_personalities, script_style, humor_level
            )
            script_sections.append(script_section)
        
        # Add intro and outro if not already included
        if not any(s.get("name") == "intro" for s in script_sections):
            intro = self._generate_intro_script(title, description, host_personalities)
            script_sections.insert(0, intro)
        
        if not any(s.get("name") == "outro" for s in script_sections):
            outro = self._generate_outro_script(host_personalities)
            script_sections.append(outro)
        
        # Assemble the complete script
        script = {
            "title": title,
            "description": description,
            "hosts": [host["name"] for host in host_personalities],
            "created_at": datetime.now().isoformat(),
            "script_style": script_style,
            "humor_level": humor_level,
            "sections": script_sections,
            "total_duration": sum(section.get("duration", 0) for section in script_sections),
            "word_count": sum(section.get("word_count", 0) for section in script_sections)
        }
        
        return script
    
    def _generate_section_script(self, section: Dict[str, Any], 
                               host_personalities: List[Dict[str, Any]],
                               script_style: str, humor_level: str) -> Dict[str, Any]:
        """
        Generate script for a single section.
        
        Args:
            section: Section from content outline
            host_personalities: List of host personality definitions
            script_style: Style of the script
            humor_level: Level of humor to include
            
        Returns:
            Script for the section
        """
        section_name = section.get("name", "unnamed_section")
        talking_points = section.get("talking_points", [])
        duration = section.get("duration", 60)  # Default 60 seconds
        
        # In a real implementation, this would use an LLM to generate
        # natural dialogue based on the talking points and host personalities
        
        # Placeholder implementation with templates
        dialogue_lines = []
        sound_effects = []
        
        # Add section transition if enabled
        if self.config["include_transitions"] and section_name != "intro":
            dialogue_lines.append({
                "speaker": "TRANSITION",
                "text": f"[Transition to {section_name.replace('_', ' ').title()} section]"
            })
            sound_effects.append({
                "type": "transition",
                "description": "Short transition sound",
                "position": len(dialogue_lines) - 1
            })
        
        # Generate dialogue for each talking point
        for i, point in enumerate(talking_points):
            point_content = point.get("content", "")
            host_index = point.get("host", i % len(host_personalities))
            host = host_personalities[host_index]
            
            # Convert talking point to natural dialogue
            dialogue = self._talking_point_to_dialogue(
                point_content, host, script_style, humor_level
            )
            
            dialogue_lines.append({
                "speaker": host["name"],
                "text": dialogue
            })
            
            # Add interaction between hosts if not the last point
            if i < len(talking_points) - 1 and script_style == "conversational":
                next_host_index = talking_points[i+1].get("host", (i+1) % len(host_personalities))
                if next_host_index != host_index:
                    # Add a brief response or handoff
                    next_host = host_personalities[next_host_index]
                    handoff = self._generate_handoff(host, next_host, point_content)
                    
                    dialogue_lines.append({
                        "speaker": next_host["name"],
                        "text": handoff
                    })
        
        # Add sound effects if enabled
        if self.config["include_sound_effects"]:
            # Add section-specific sound effects
            if section_name == "key_moments" and len(dialogue_lines) > 2:
                sound_effects.append({
                    "type": "highlight",
                    "description": "Race highlight sound clip",
                    "position": 2  # After the first talking point
                })
            
            if section_name == "race_summary" and len(dialogue_lines) > 1:
                sound_effects.append({
                    "type": "ambient",
                    "description": "Crowd and track ambient noise",
                    "position": 1
                })
        
        # Estimate word count (for timing purposes)
        word_count = sum(len(line["text"].split()) for line in dialogue_lines)
        
        # Create section script
        script_section = {
            "name": section_name,
            "duration": duration,
            "dialogue": dialogue_lines,
            "sound_effects": sound_effects,
            "word_count": word_count
        }
        
        return script_section
    
    def _talking_point_to_dialogue(self, point: str, host: Dict[str, Any],
                                 script_style: str, humor_level: str) -> str:
        """
        Convert a talking point into natural dialogue for a specific host.
        
        Args:
            point: Talking point content
            host: Host personality definition
            script_style: Style of the script
            humor_level: Level of humor to include
            
        Returns:
            Natural dialogue text
        """
        # In a real implementation, this would use an LLM to generate
        # dialogue that matches the host's personality and style
        
        # Placeholder implementation with templates
        host_style = host.get("style", "neutral")
        catchphrases = host.get("catchphrases", [])
        
        # Start with the basic point
        dialogue = point
        
        # Add style-specific elements
        if host_style == "enthusiastic":
            dialogue = f"Wow! {dialogue} This is really fascinating!"
        elif host_style == "analytical":
            dialogue = f"When we analyze {dialogue}, we can see some interesting patterns."
        elif host_style == "neutral":
            dialogue = f"Let's talk about {dialogue}."
        
        # Add a catchphrase if available and probability hits
        if catchphrases and len(catchphrases) > 0 and humor_level != "none":
            import random
            if random.random() < 0.3:  # 30% chance to add catchphrase
                catchphrase = random.choice(catchphrases)
                dialogue = f"{catchphrase} {dialogue}"
        
        # Add humor if requested
        if humor_level == "moderate" or humor_level == "heavy":
            dialogue += " And hey, isn't that what we all love about this sport?"
        
        if humor_level == "heavy":
            dialogue += " I mean, where else would you see such drama every weekend?"
        
        return dialogue
    
    def _generate_handoff(self, current_host: Dict[str, Any], 
                        next_host: Dict[str, Any], point_content: str) -> str:
        """
        Generate a natural handoff between hosts.
        
        Args:
            current_host: Current speaking host
            next_host: Next speaking host
            point_content: Content of the current talking point
            
        Returns:
            Handoff dialogue
        """
        # In a real implementation, this would use an LLM to generate
        # natural handoffs between hosts
        
        # Placeholder implementation with templates
        handoffs = [
            f"That's right, and I'd add that...",
            f"Interesting point! I was also thinking...",
            f"I see what you mean. From my perspective...",
            f"Building on that...",
            f"That's a good point. I'd also like to mention..."
        ]
        
        import random
        return random.choice(handoffs)
    
    def _generate_intro_script(self, title: str, description: str,
                             host_personalities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate script for the episode introduction.
        
        Args:
            title: Episode title
            description: Episode description
            host_personalities: List of host personality definitions
            
        Returns:
            Script for the intro section
        """
        # In a real implementation, this would use an LLM to generate
        # a natural introduction based on the episode content
        
        # Placeholder implementation with templates
        dialogue_lines = [
            {
                "speaker": "INTRO",
                "text": "[Theme music plays]"
            }
        ]
        
        # Add host introductions
        primary_host = host_personalities[0]
        dialogue_lines.append({
            "speaker": primary_host["name"],
            "text": f"Welcome to DopCast! I'm {primary_host['name']}, and today we're discussing {title}."
        })
        
        if len(host_personalities) > 1:
            co_hosts = ", ".join([h["name"] for h in host_personalities[1:]])
            dialogue_lines.append({
                "speaker": primary_host["name"],
                "text": f"Joining me as always is {co_hosts}. Great to have you here!"
            })
            
            # Add a response from one co-host
            dialogue_lines.append({
                "speaker": host_personalities[1]["name"],
                "text": f"Great to be here! We've got an exciting episode lined up today."
            })
        
        # Add episode description
        dialogue_lines.append({
            "speaker": primary_host["name"],
            "text": f"In today's episode: {description}"
        })
        
        # Add sound effects
        sound_effects = [
            {
                "type": "intro",
                "description": "Theme music",
                "position": 0
            }
        ]
        
        return {
            "name": "intro",
            "duration": 60,  # Default intro duration
            "dialogue": dialogue_lines,
            "sound_effects": sound_effects,
            "word_count": sum(len(line["text"].split()) for line in dialogue_lines)
        }
    
    def _generate_outro_script(self, host_personalities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate script for the episode conclusion.
        
        Args:
            host_personalities: List of host personality definitions
            
        Returns:
            Script for the outro section
        """
        # In a real implementation, this would use an LLM to generate
        # a natural conclusion based on the episode content
        
        # Placeholder implementation with templates
        primary_host = host_personalities[0]
        
        dialogue_lines = [
            {
                "speaker": primary_host["name"],
                "text": "Well, that brings us to the end of today's episode. Thanks for listening!"
            }
        ]
        
        if len(host_personalities) > 1:
            co_host = host_personalities[1]
            dialogue_lines.append({
                "speaker": co_host["name"],
                "text": "It's been a great discussion. Join us next time for more insights and analysis."
            })
        
        dialogue_lines.append({
            "speaker": primary_host["name"],
            "text": "Don't forget to subscribe and leave us a review. Until next time, goodbye!"
        })
        
        dialogue_lines.append({
            "speaker": "OUTRO",
            "text": "[Outro music plays and fades]"
        })
        
        # Add sound effects
        sound_effects = [
            {
                "type": "outro",
                "description": "Outro music",
                "position": len(dialogue_lines) - 1
            }
        ]
        
        return {
            "name": "outro",
            "duration": 30,  # Default outro duration
            "dialogue": dialogue_lines,
            "sound_effects": sound_effects,
            "word_count": sum(len(line["text"].split()) for line in dialogue_lines)
        }
