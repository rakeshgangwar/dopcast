"""
Section planner tool for the Content Planning Agent.
Provides enhanced section planning capabilities.
"""

import logging
from typing import Dict, Any, List, Optional

class SectionPlannerTool:
    """
    Enhanced section planner tool for planning podcast episode sections.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the section planner tool.
        
        Args:
            config: Configuration parameters
        """
        self.logger = logging.getLogger("dopcast.content_planning.section_planner")
        self.config = config or {}
    
    def get_episode_format(self, episode_type: str, episode_formats: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get the episode format for a specific episode type.
        
        Args:
            episode_type: Type of episode
            episode_formats: Dictionary of available episode formats
            
        Returns:
            Episode format specification
        """
        if episode_type not in episode_formats:
            self.logger.warning(f"Unknown episode type: {episode_type}, defaulting to race_review")
            episode_type = "race_review"
        
        return episode_formats[episode_type]
    
    def adjust_section_durations(self, sections: List[Dict[str, Any]], 
                               target_duration: int) -> List[Dict[str, Any]]:
        """
        Adjust section durations to match target episode length.
        
        Args:
            sections: List of section specifications
            target_duration: Target duration in seconds
            
        Returns:
            Adjusted sections list
        """
        # Calculate current total duration
        current_total = sum(section["duration"] for section in sections)
        
        # If current duration matches target, no adjustment needed
        if current_total == target_duration:
            return sections
        
        # Create a copy to avoid modifying the original
        adjusted_sections = [section.copy() for section in sections]
        
        # Calculate scaling factor
        scale_factor = target_duration / current_total
        
        # Adjust durations proportionally, preserving high priority sections
        # First pass: adjust non-high priority sections
        high_priority_sections = [s for s in adjusted_sections if s["priority"] == "high"]
        other_sections = [s for s in adjusted_sections if s["priority"] != "high"]
        
        high_priority_duration = sum(section["duration"] for section in high_priority_sections)
        other_duration = sum(section["duration"] for section in other_sections)
        
        # If we have both high priority and other sections
        if high_priority_sections and other_sections:
            # Calculate how much to scale other sections
            remaining_duration = target_duration - high_priority_duration
            other_scale_factor = remaining_duration / other_duration
            
            # Apply scaling to other sections
            for section in other_sections:
                section["duration"] = int(section["duration"] * other_scale_factor)
        else:
            # If all sections are the same priority, scale everything
            for section in adjusted_sections:
                section["duration"] = int(section["duration"] * scale_factor)
        
        # Ensure minimum durations and fix rounding errors
        for section in adjusted_sections:
            section["duration"] = max(section["duration"], 30)  # Minimum 30 seconds per section
        
        # Final adjustment to exactly match target duration
        current_total = sum(section["duration"] for section in adjusted_sections)
        if current_total != target_duration:
            # Add or subtract the difference from the longest non-high priority section
            diff = target_duration - current_total
            if other_sections:
                longest_section = max(other_sections, key=lambda s: s["duration"])
                longest_section["duration"] += diff
            else:
                longest_section = max(adjusted_sections, key=lambda s: s["duration"])
                longest_section["duration"] += diff
        
        return adjusted_sections
    
    def filter_sections(self, sections: List[Dict[str, Any]], 
                      research_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Filter sections based on research data.
        
        Args:
            sections: List of section specifications
            research_data: Research data
            
        Returns:
            Filtered sections list
        """
        # Create a copy to avoid modifying the original
        filtered_sections = [section.copy() for section in sections]
        
        # Check for conditional sections
        conditional_sections = [s for s in filtered_sections if s["priority"] == "conditional"]
        
        for section in conditional_sections:
            # Determine if the section should be included
            include = self._should_include_section(section, research_data)
            
            if not include:
                filtered_sections.remove(section)
        
        return filtered_sections
    
    def _should_include_section(self, section: Dict[str, Any], 
                              research_data: Dict[str, Any]) -> bool:
        """
        Determine if a conditional section should be included.
        
        Args:
            section: Section specification
            research_data: Research data
            
        Returns:
            True if the section should be included, False otherwise
        """
        section_name = section["name"]
        
        # Check for specific conditions based on section name
        if section_name == "controversy_discussion":
            # Include if there are controversy topics in the research data
            topics = research_data.get("topics", {})
            return "controversy" in topics and len(topics.get("controversy", [])) > 0
        
        elif section_name == "technical_insights":
            # Include if there are technical topics in the research data
            topics = research_data.get("topics", {})
            return "technical" in topics and len(topics.get("technical", [])) > 0
        
        # Default to including the section
        return True
