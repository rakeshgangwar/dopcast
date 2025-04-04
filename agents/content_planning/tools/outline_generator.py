"""
Outline generator tool for the Content Planning Agent.
Provides enhanced outline generation capabilities.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class OutlineGeneratorTool:
    """
    Enhanced outline generator tool for creating podcast episode outlines.
    """
    
    def __init__(self, content_dir: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the outline generator tool.
        
        Args:
            content_dir: Directory to store content outlines
            config: Configuration parameters
        """
        self.logger = logging.getLogger("dopcast.content_planning.outline_generator")
        self.content_dir = content_dir
        self.config = config or {}
        
        # Ensure outlines directory exists
        os.makedirs(os.path.join(self.content_dir, "outlines"), exist_ok=True)
    
    def generate_episode_title(self, sport: str, event_type: str, 
                             entities: Dict[str, List[str]], episode_type: str) -> str:
        """
        Generate an engaging episode title.
        
        Args:
            sport: Sport type
            event_type: Type of event
            entities: Key entities from research
            episode_type: Type of episode
            
        Returns:
            Episode title
        """
        # In a real implementation, this would use an LLM to generate creative titles
        # based on the content and key moments
        
        # Placeholder implementation with templates
        if episode_type == "race_review":
            if sport == "f1":
                track = entities.get("tracks", ["the track"])[0] if entities.get("tracks") else "the track"
                return f"F1 Race Review: Drama and Action at {track}"
            elif sport == "motogp":
                track = entities.get("tracks", ["the circuit"])[0] if entities.get("tracks") else "the circuit"
                return f"MotoGP Race Review: Thrills and Spills at {track}"
        
        elif episode_type == "news_update":
            return f"{sport.upper()} News Roundup: Latest Updates and Breaking Stories"
        
        elif episode_type == "technical_deep_dive":
            return f"{sport.upper()} Tech Talk: Understanding the Latest Innovations"
        
        # Default title if no template matches
        return f"{sport.upper()} {episode_type.replace('_', ' ').title()}: Latest Analysis and Insights"
    
    def generate_episode_description(self, sport: str, event_type: str,
                                   entities: Dict[str, List[str]], episode_type: str) -> str:
        """
        Generate an informative episode description.
        
        Args:
            sport: Sport type
            event_type: Type of event
            entities: Key entities from research
            episode_type: Type of episode
            
        Returns:
            Episode description
        """
        # In a real implementation, this would use an LLM to generate descriptions
        # based on the content and key moments
        
        # Placeholder implementation with templates
        if episode_type == "race_review":
            drivers = ", ".join(entities.get("drivers", [])[:3]) if entities.get("drivers") else "the drivers"
            return (f"Join us as we break down all the action from the latest {sport.upper()} race. "
                    f"We'll analyze the performances of {drivers} and discuss the implications "
                    f"for the championship.")
        
        elif episode_type == "news_update":
            return (f"Stay up to date with the latest {sport.upper()} news and developments. "
                    f"We cover the most important stories and what they mean for teams and drivers.")
        
        elif episode_type == "technical_deep_dive":
            return (f"Dive into the technical world of {sport.upper()}. We explain complex concepts "
                    f"in an accessible way and explore how technology shapes the sport.")
        
        # Default description if no template matches
        return (f"The latest {sport.upper()} analysis and insights. Our expert hosts break down "
                f"recent events and provide in-depth coverage of the sport.")
    
    def extract_references(self, articles: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Extract references from research articles.
        
        Args:
            articles: List of research articles
            
        Returns:
            List of reference information
        """
        references = []
        
        for article in articles:
            if "title" in article and "url" in article:
                reference = {
                    "title": article["title"],
                    "source": article.get("source", "Unknown source"),
                    "url": article["url"]
                }
                references.append(reference)
        
        return references
    
    def create_outline(self, research_data: Dict[str, Any], episode_type: str,
                     episode_format: Dict[str, Any], detailed_sections: List[Dict[str, Any]],
                     technical_level: str, host_count: int) -> Dict[str, Any]:
        """
        Create a complete episode outline.
        
        Args:
            research_data: Research data
            episode_type: Type of episode
            episode_format: Format specification
            detailed_sections: Detailed sections with talking points
            technical_level: Level of technical detail
            host_count: Number of hosts
            
        Returns:
            Complete episode outline
        """
        sport = research_data.get("sport", "unknown")
        event_type = research_data.get("event_type", "unknown")
        articles = research_data.get("articles", [])
        entities = research_data.get("key_entities", {})
        
        # Generate title and description
        episode_title = self.generate_episode_title(sport, event_type, entities, episode_type)
        episode_description = self.generate_episode_description(sport, event_type, entities, episode_type)
        
        # Calculate total duration
        total_duration = sum(section["duration"] for section in detailed_sections)
        
        # Create the complete outline
        outline = {
            "title": episode_title,
            "description": episode_description,
            "sport": sport,
            "episode_type": episode_type,
            "duration": total_duration,
            "technical_level": technical_level,
            "host_count": host_count,
            "created_at": datetime.now().isoformat(),
            "sections": detailed_sections,
            "key_entities": entities,
            "references": self.extract_references(articles)
        }
        
        return outline
    
    def save_outline(self, outline: Dict[str, Any]) -> str:
        """
        Save the outline to disk.
        
        Args:
            outline: Episode outline
            
        Returns:
            Path to the saved outline file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sport = outline.get("sport", "unknown")
        episode_type = outline.get("episode_type", "unknown")
        
        filename = f"{sport}_{episode_type}_{timestamp}.json"
        filepath = os.path.join(self.content_dir, "outlines", filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(outline, f, indent=2)
        
        self.logger.info(f"Saved outline to {filepath}")
        
        return filepath
