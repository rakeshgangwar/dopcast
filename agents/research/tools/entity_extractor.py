"""
Entity extractor tool for the Research Agent.
Provides enhanced entity extraction capabilities using NLP techniques.
"""

import logging
from typing import Dict, Any, List, Optional
import re
from collections import Counter

class EntityExtractorTool:
    """
    Enhanced entity extractor tool with NLP capabilities.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the entity extractor tool.
        
        Args:
            config: Configuration parameters
        """
        self.logger = logging.getLogger("dopcast.research.entity_extractor")
        self.config = config or {}
        
        # Initialize entity dictionaries
        self._initialize_entity_dictionaries()
    
    def _initialize_entity_dictionaries(self):
        """Initialize dictionaries of known entities for each sport."""
        # F1 entities
        self.f1_drivers = [
            "Hamilton", "Verstappen", "Leclerc", "Norris", "Russell", "Sainz",
            "Perez", "Alonso", "Stroll", "Ocon", "Gasly", "Tsunoda", "Albon",
            "Bottas", "Zhou", "Magnussen", "Hulkenberg", "Lawson", "Sargeant",
            "Piastri", "Lewis Hamilton", "Max Verstappen", "Charles Leclerc",
            "Lando Norris", "George Russell", "Carlos Sainz", "Sergio Perez"
        ]
        
        self.f1_teams = [
            "Mercedes", "Red Bull", "Ferrari", "McLaren", "Aston Martin",
            "Alpine", "AlphaTauri", "Williams", "Alfa Romeo", "Haas",
            "Mercedes-AMG", "Red Bull Racing", "Scuderia Ferrari", "McLaren F1",
            "Aston Martin F1", "Alpine F1", "RB", "Williams Racing"
        ]
        
        self.f1_tracks = [
            "Silverstone", "Monza", "Spa", "Monaco", "Catalunya", "Imola",
            "Bahrain", "Jeddah", "Melbourne", "Suzuka", "Singapore", "COTA",
            "Mexico City", "Interlagos", "Las Vegas", "Zandvoort", "Baku",
            "Miami", "Montreal", "Budapest", "Spielberg", "Lusail", "Yas Marina"
        ]
        
        # MotoGP entities
        self.motogp_riders = [
            "Marquez", "Bagnaia", "Quartararo", "Binder", "Martin", "Espargaro",
            "Vinales", "Morbidelli", "Zarco", "Miller", "Oliveira", "Rins",
            "Bastianini", "Marini", "Fernandez", "Nakagami", "Marc Marquez",
            "Francesco Bagnaia", "Fabio Quartararo", "Brad Binder", "Jorge Martin"
        ]
        
        self.motogp_teams = [
            "Ducati", "Yamaha", "Honda", "KTM", "Aprilia", "Suzuki",
            "Ducati Lenovo", "Monster Energy Yamaha", "Repsol Honda",
            "Red Bull KTM", "Aprilia Racing", "Pramac Racing", "Gresini Racing",
            "LCR Honda", "Tech3 KTM", "VR46 Racing"
        ]
        
        self.motogp_tracks = [
            "Losail", "Mandalika", "Termas de Rio Hondo", "COTA", "Portimao",
            "Jerez", "Le Mans", "Mugello", "Catalunya", "Sachsenring", "Assen",
            "Silverstone", "Red Bull Ring", "Aragon", "Misano", "Motegi",
            "Phillip Island", "Sepang", "Valencia"
        ]
        
        # Common event types
        self.event_types = [
            "race", "qualifying", "practice", "sprint", "test", "championship",
            "grand prix", "free practice", "warm-up", "press conference"
        ]
    
    def extract_entities(self, articles: List[Dict[str, Any]], sport: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract key entities from articles.
        
        Args:
            articles: List of article data
            sport: Sport type
            
        Returns:
            Dictionary of entity types and their mentions with frequency and context
        """
        self.logger.info(f"Extracting entities from {len(articles)} articles for {sport}")
        
        # Initialize entity containers
        entities = {
            "people": [],  # drivers/riders
            "teams": [],
            "tracks": [],
            "events": []
        }
        
        # Select the appropriate entity lists based on sport
        if sport == "f1":
            people_list = self.f1_drivers
            teams_list = self.f1_teams
            tracks_list = self.f1_tracks
        elif sport == "motogp":
            people_list = self.motogp_riders
            teams_list = self.motogp_teams
            tracks_list = self.motogp_tracks
        else:
            self.logger.warning(f"Unknown sport: {sport}, using generic entity extraction")
            people_list = self.f1_drivers + self.motogp_riders
            teams_list = self.f1_teams + self.motogp_teams
            tracks_list = self.f1_tracks + self.motogp_tracks
        
        # Process each article
        for article in articles:
            text = f"{article.get('title', '')} {article.get('summary', '')}"
            
            # Extract people
            for person in people_list:
                if person in text:
                    context = self._get_entity_context(text, person)
                    entities["people"].append({
                        "name": person,
                        "article_id": article.get("url", ""),
                        "context": context
                    })
            
            # Extract teams
            for team in teams_list:
                if team in text:
                    context = self._get_entity_context(text, team)
                    entities["teams"].append({
                        "name": team,
                        "article_id": article.get("url", ""),
                        "context": context
                    })
            
            # Extract tracks
            for track in tracks_list:
                if track in text:
                    context = self._get_entity_context(text, track)
                    entities["tracks"].append({
                        "name": track,
                        "article_id": article.get("url", ""),
                        "context": context
                    })
            
            # Extract events
            for event in self.event_types:
                if event.lower() in text.lower():
                    context = self._get_entity_context(text, event, case_sensitive=False)
                    entities["events"].append({
                        "name": event,
                        "article_id": article.get("url", ""),
                        "context": context
                    })
        
        # Aggregate and count entities
        aggregated_entities = self._aggregate_entities(entities)
        
        return aggregated_entities
    
    def _get_entity_context(self, text: str, entity: str, case_sensitive: bool = True, context_size: int = 100) -> str:
        """
        Get the context around an entity mention.
        
        Args:
            text: The text to search in
            entity: The entity to find
            case_sensitive: Whether to use case-sensitive matching
            context_size: Number of characters to include in context
            
        Returns:
            Context string
        """
        if not case_sensitive:
            pattern = re.compile(re.escape(entity), re.IGNORECASE)
            match = pattern.search(text)
        else:
            match = text.find(entity)
            match = match if match >= 0 else None
        
        if match is None:
            return ""
        
        if isinstance(match, re.Match):
            start_pos = match.start()
            end_pos = match.end()
        else:
            start_pos = match
            end_pos = start_pos + len(entity)
        
        # Get context around the entity
        start = max(0, start_pos - context_size // 2)
        end = min(len(text), end_pos + context_size // 2)
        
        # Adjust to not cut words
        while start > 0 and text[start] != ' ':
            start -= 1
        
        while end < len(text) - 1 and text[end] != ' ':
            end += 1
        
        context = text[start:end].strip()
        
        # Highlight the entity in the context
        if case_sensitive:
            highlighted = context.replace(entity, f"**{entity}**")
        else:
            pattern = re.compile(f"({re.escape(entity)})", re.IGNORECASE)
            highlighted = pattern.sub(r"**\1**", context)
        
        return highlighted
    
    def _aggregate_entities(self, entities: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Aggregate entities and count frequencies.
        
        Args:
            entities: Dictionary of entity types and their mentions
            
        Returns:
            Aggregated entities with frequency counts
        """
        aggregated = {}
        
        for entity_type, mentions in entities.items():
            # Count entity frequencies
            entity_counter = Counter([mention["name"] for mention in mentions])
            
            # Create aggregated list
            aggregated[entity_type] = [
                {
                    "name": entity,
                    "count": count,
                    "mentions": [
                        mention for mention in mentions
                        if mention["name"] == entity
                    ]
                }
                for entity, count in entity_counter.most_common()
            ]
        
        return aggregated
    
    def categorize_topics(self, articles: List[Dict[str, Any]]) -> Dict[str, List[int]]:
        """
        Categorize articles by topic.
        
        Args:
            articles: List of article data
            
        Returns:
            Dictionary of topics and article indices
        """
        topics = {
            "race_results": [],
            "technical": [],
            "driver_news": [],
            "team_news": [],
            "controversy": [],
            "preview": []
        }
        
        topic_keywords = {
            "race_results": ["win", "podium", "finished", "results", "standings", "victory", "champion"],
            "technical": ["upgrade", "engine", "aerodynamic", "technical", "development", "design", "performance"],
            "driver_news": ["signed", "contract", "moving", "driver", "career", "future", "transfer"],
            "team_news": ["team", "announce", "sponsor", "partnership", "collaboration", "deal"],
            "controversy": ["penalty", "crash", "controversy", "stewards", "investigation", "incident", "dispute"],
            "preview": ["preview", "upcoming", "weekend", "prepare", "ready", "anticipate", "expect"]
        }
        
        for i, article in enumerate(articles):
            text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
            
            for topic, keywords in topic_keywords.items():
                for keyword in keywords:
                    if keyword in text and i not in topics[topic]:
                        topics[topic].append(i)
                        break
        
        return topics
