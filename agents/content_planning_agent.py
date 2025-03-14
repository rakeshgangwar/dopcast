import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from agents.base_agent import BaseAgent

class ContentPlanningAgent(BaseAgent):
    """
    Agent responsible for structuring podcast episodes and creating content outlines.
    Takes research data and transforms it into structured episode plans.
    """
    
    def __init__(self, name: str = "content_planning", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the content planning agent.
        
        Args:
            name: Agent identifier
            config: Configuration parameters
        """
        default_config = {
            "episode_formats": {
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
            },
            "host_count": 2,
            "content_tone": "conversational",
            "technical_level": "mixed",  # basic, mixed, or advanced
            "target_audience": "general_fans"
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
        os.makedirs(os.path.join(self.content_dir, "outlines"), exist_ok=True)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process research data and create a podcast episode outline.
        
        Args:
            input_data: Input data containing:
                - research_data: Data from the research agent
                - episode_type: Type of episode to create
                - custom_parameters: Any custom parameters for this episode
        
        Returns:
            Episode outline with sections and talking points
        """
        research_data = input_data.get("research_data", {})
        episode_type = input_data.get("episode_type", "race_review")
        custom_parameters = input_data.get("custom_parameters", {})
        
        # Validate input data
        if not research_data:
            self.logger.error("No research data provided")
            return {"error": "No research data provided"}
        
        # Get episode format
        if episode_type not in self.config["episode_formats"]:
            self.logger.warning(f"Unknown episode type: {episode_type}, defaulting to race_review")
            episode_type = "race_review"
        
        episode_format = self.config["episode_formats"][episode_type]
        
        # Apply any custom parameters
        episode_duration = custom_parameters.get("duration", episode_format["total_duration"])
        technical_level = custom_parameters.get("technical_level", self.config["technical_level"])
        
        # Create the episode outline
        outline = self._create_outline(research_data, episode_type, episode_format, 
                                     episode_duration, technical_level)
        
        # Save the outline
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sport = research_data.get("sport", "unknown")
        filename = f"{sport}_{episode_type}_{timestamp}.json"
        with open(os.path.join(self.content_dir, "outlines", filename), "w") as f:
            json.dump(outline, f, indent=2)
        
        return outline
    
    def _create_outline(self, research_data: Dict[str, Any], episode_type: str,
                       episode_format: Dict[str, Any], episode_duration: int,
                       technical_level: str) -> Dict[str, Any]:
        """
        Create a detailed episode outline based on research data and format.
        
        Args:
            research_data: Data from the research agent
            episode_type: Type of episode
            episode_format: Format specification for the episode
            episode_duration: Target duration in seconds
            technical_level: Level of technical detail
            
        Returns:
            Complete episode outline
        """
        sport = research_data.get("sport", "unknown")
        event_type = research_data.get("event_type", "unknown")
        articles = research_data.get("articles", [])
        entities = research_data.get("key_entities", {})
        topics = research_data.get("topics", {})
        
        # Create episode metadata
        episode_title = self._generate_episode_title(sport, event_type, entities, episode_type)
        episode_description = self._generate_episode_description(sport, event_type, entities, episode_type)
        
        # Adjust section durations if needed
        sections = self._adjust_section_durations(episode_format["sections"], episode_duration)
        
        # Create detailed sections with talking points
        detailed_sections = []
        for section in sections:
            section_data = self._create_section(section, research_data, technical_level)
            detailed_sections.append(section_data)
        
        # Assemble the complete outline
        outline = {
            "title": episode_title,
            "description": episode_description,
            "sport": sport,
            "episode_type": episode_type,
            "duration": episode_duration,
            "technical_level": technical_level,
            "host_count": self.config["host_count"],
            "created_at": datetime.now().isoformat(),
            "sections": detailed_sections,
            "key_entities": entities,
            "references": self._extract_references(articles)
        }
        
        return outline
    
    def _generate_episode_title(self, sport: str, event_type: str, 
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
    
    def _generate_episode_description(self, sport: str, event_type: str,
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
    
    def _adjust_section_durations(self, sections: List[Dict[str, Any]], 
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
    
    def _create_section(self, section: Dict[str, Any], research_data: Dict[str, Any],
                       technical_level: str) -> Dict[str, Any]:
        """
        Create a detailed section with talking points.
        
        Args:
            section: Section specification
            research_data: Research data
            technical_level: Level of technical detail
            
        Returns:
            Detailed section with talking points
        """
        section_name = section["name"]
        section_duration = section["duration"]
        
        # In a real implementation, this would use an LLM to generate
        # talking points based on the research data and section type
        
        # Placeholder implementation with templates
        talking_points = self._generate_talking_points(section_name, research_data, technical_level)
        
        # Estimate time per talking point
        point_count = len(talking_points)
        time_per_point = section_duration // max(point_count, 1) if point_count > 0 else section_duration
        
        # Create host assignments
        host_assignments = self._assign_hosts(talking_points)
        
        # Create detailed section
        detailed_section = {
            "name": section_name,
            "duration": section_duration,
            "talking_points": [
                {
                    "content": point,
                    "duration": time_per_point,
                    "host": host
                } for point, host in zip(talking_points, host_assignments)
            ]
        }
        
        return detailed_section
    
    def _generate_talking_points(self, section_name: str, research_data: Dict[str, Any],
                               technical_level: str) -> List[str]:
        """
        Generate talking points for a section based on research data.
        
        Args:
            section_name: Name of the section
            research_data: Research data
            technical_level: Level of technical detail
            
        Returns:
            List of talking points
        """
        # In a real implementation, this would use an LLM to generate
        # specific talking points based on the research data
        
        # Placeholder implementation with templates
        sport = research_data.get("sport", "unknown")
        entities = research_data.get("key_entities", {})
        
        drivers = entities.get("drivers", [])
        teams = entities.get("teams", [])
        tracks = entities.get("tracks", [])
        
        # Default points if we don't have specific templates
        default_points = ["Discuss recent developments", "Analyze performance trends", "Share expert insights"]
        
        # Section-specific templates
        if section_name == "intro":
            return [
                f"Welcome to our {sport.upper()} podcast",
                "Introduce today's topics and format",
                "Brief mention of key stories we'll cover"
            ]
            
        elif section_name == "race_summary":
            points = ["Overview of race results and key moments"]
            if drivers:
                points.append(f"Highlight {drivers[0]}'s performance" if drivers else "Highlight winner's performance")
            if teams:
                points.append(f"Team performance overview for {teams[0]}" if teams else "Team performance overview")
            return points
            
        elif section_name == "key_moments":
            return [
                "Start of the race analysis",
                "Critical overtakes and battles",
                "Safety car/red flag incidents" if sport == "f1" else "Crash incidents and recoveries",
                "Final laps drama"
            ]
            
        elif section_name == "driver_performances":
            points = []
            for i, driver in enumerate(drivers[:3]):
                points.append(f"Analysis of {driver}'s race strategy and execution")
            if len(points) == 0:
                points = ["Analysis of top drivers' performances", "Standout drives from midfield", "Struggles and disappointments"]
            return points
            
        elif section_name == "team_strategies":
            points = []
            for i, team in enumerate(teams[:2]):
                points.append(f"Breakdown of {team}'s strategy decisions")
            if len(points) == 0:
                points = ["Top team strategy analysis", "Midfield strategy comparisons", "Strategy mistakes and successes"]
            return points
            
        elif section_name == "technical_insights":
            if technical_level == "basic":
                return ["Simple explanation of key technical factors", "How car/bike setup affected performance", "Visual aids for understanding technical concepts"]
            elif technical_level == "advanced":
                return ["Detailed aerodynamic analysis", "Power unit performance metrics", "Suspension and mechanical grip discussion", "Data analysis of key performance indicators"]
            else:  # mixed
                return ["Accessible technical analysis with some depth", "Explanation of how technical factors affected results", "Comparison of different technical approaches"]
            
        elif section_name == "championship_implications":
            return ["Updated championship standings", "Points gaps and mathematical scenarios", "Prediction for championship development"]
            
        elif section_name == "controversy_discussion":
            return ["Analysis of controversial incidents", "Stewards' decisions and penalties", "Team and driver reactions", "Historical context for similar situations"]
            
        elif section_name == "next_race_preview":
            next_track = "the next circuit" if not tracks else f"{tracks[0]}"
            return [f"Preview of {next_track}", "Expected competitive order", "Weather forecast and implications", "Key storylines to follow"]
            
        elif section_name == "outro":
            return ["Recap of main discussion points", "Teaser for next episode", "Thank listeners and sign off"]
            
        # Return default points if no specific template
        return default_points
    
    def _assign_hosts(self, talking_points: List[str]) -> List[int]:
        """
        Assign hosts to talking points for a conversational flow.
        
        Args:
            talking_points: List of talking points
            
        Returns:
            List of host assignments (0-indexed)
        """
        host_count = self.config["host_count"]
        assignments = []
        
        # Simple alternating assignment for a conversational feel
        current_host = 0
        for _ in talking_points:
            assignments.append(current_host)
            current_host = (current_host + 1) % host_count
        
        return assignments
    
    def _extract_references(self, articles: List[Dict[str, Any]]) -> List[Dict[str, str]]:
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
