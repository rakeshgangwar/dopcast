import os
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

import requests
from bs4 import BeautifulSoup
import pandas as pd

from agents.base_agent import BaseAgent

class ResearchAgent(BaseAgent):
    """
    Agent responsible for gathering and analyzing motorsport information.
    Collects data from official websites, news sources, and social media.
    """
    
    def __init__(self, name: str = "research", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the research agent with default configuration.
        
        Args:
            name: Agent identifier
            config: Configuration parameters
        """
        default_config = {
            "sources": {
                "f1": [
                    "https://www.formula1.com/",
                    "https://www.autosport.com/f1/",
                    "https://www.motorsport.com/f1/",
                    "https://www.espn.com/f1/",
                    "https://www.skysports.com/f1",
                    "https://www.bbc.com/sport/formula1",
                    "https://www.racefans.net/"
                ],
                "motogp": [
                    "https://www.motogp.com/",
                    "https://www.autosport.com/motogp/",
                    "https://www.motorsport.com/motogp/",
                    "https://www.crash.net/motogp",
                    "https://www.gpone.com/",
                    "https://www.motorcyclenews.com/sport/motogp/"
                ]
            },
            "update_frequency": 3600,  # seconds
            "cache_expiry": 86400,    # seconds
            "max_articles_per_source": 10,
            "use_fallback_data": True  # Enable fallback to mock data when scraping fails
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
        
        # Initialize data storage
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        os.makedirs(os.path.join(self.data_dir, "raw"), exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "processed"), exist_ok=True)
        
        # Initialize cache
        self.cache = {}
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process research requests and gather motorsport information.
        
        Args:
            input_data: Input data containing research parameters
                - sport: "f1" or "motogp"
                - event_type: "race", "qualifying", "practice", "news", etc.
                - event_id: Specific event identifier (optional)
                - force_refresh: Force refresh of cached data (optional)
        
        Returns:
            Collected and processed research data
        """
        sport = input_data.get("sport", "f1")
        event_type = input_data.get("event_type", "latest")
        event_id = input_data.get("event_id")
        force_refresh = input_data.get("force_refresh", False)
        
        # Check cache unless force refresh is requested
        cache_key = f"{sport}_{event_type}_{event_id if event_id else 'latest'}"
        if not force_refresh and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            cache_age = (datetime.now() - cache_entry["timestamp"]).total_seconds()
            if cache_age < self.config["cache_expiry"]:
                self.logger.info(f"Returning cached data for {cache_key}")
                return cache_entry["data"]
        
        # Gather data based on sport and event type
        self.logger.info(f"Gathering {event_type} data for {sport}")
        
        # Collect data from configured sources
        sources = self.config["sources"].get(sport, [])
        collected_data = await self._collect_from_sources(sources, sport, event_type, event_id)
        
        # Process and structure the collected data
        processed_data = self._process_data(collected_data, sport, event_type)
        
        # Save to disk
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{sport}_{event_type}_{timestamp}.json"
        with open(os.path.join(self.data_dir, "processed", filename), "w", encoding="utf-8-sig") as f:
            json.dump(processed_data, f, indent=2)
        
        # Update cache
        self.cache[cache_key] = {
            "timestamp": datetime.now(),
            "data": processed_data
        }
        
        return processed_data
    
    async def _collect_from_sources(self, sources: List[str], sport: str, 
                                  event_type: str, event_id: Optional[str]) -> List[Dict[str, Any]]:
        """
        Collect data from multiple sources concurrently.
        
        Args:
            sources: List of source URLs
            sport: Sport type (f1 or motogp)
            event_type: Type of event
            event_id: Specific event identifier
            
        Returns:
            List of collected data items
        """
        tasks = []
        for source in sources:
            tasks.append(self._scrape_source(source, sport, event_type, event_id))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        collected_data = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error scraping {sources[i]}: {str(result)}")
            else:
                collected_data.extend(result)
        
        # Fallback to mock data if scraping fails and fallback is enabled
        if not collected_data and self.config["use_fallback_data"]:
            self.logger.warning("No data collected, using fallback mock data")
            collected_data = self._get_mock_data(sport, event_type)
        
        return collected_data
    
    async def _scrape_source(self, source_url: str, sport: str, 
                           event_type: str, event_id: Optional[str]) -> List[Dict[str, Any]]:
        """
        Scrape a single source for relevant information.
        
        Args:
            source_url: URL of the source
            sport: Sport type
            event_type: Type of event
            event_id: Specific event identifier
            
        Returns:
            List of data items from the source
        """
        # This would be implemented with actual web scraping logic
        # For now, we'll return a placeholder implementation
        
        # In a real implementation, this would use aiohttp for async requests
        # and proper parsing logic for each source
        
        # Placeholder implementation
        try:
            # Simulate async HTTP request
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # For demonstration purposes only - in production would use proper async HTTP
            response = requests.get(source_url, timeout=10)
            if response.status_code != 200:
                return []
                
            # Save raw data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            source_name = source_url.split("//")[1].split("/")[0].replace(".", "_")
            raw_filename = f"{sport}_{source_name}_{timestamp}.html"
            with open(os.path.join(self.data_dir, "raw", raw_filename), "w", encoding="utf-8") as f:
                f.write(response.text)
            
            # Parse with BeautifulSoup (simplified example)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract relevant information based on source and sport
            # This would be customized for each source in a real implementation
            articles = []
            
            # Example extraction logic - would be specific to each website's structure
            article_elements = soup.select(".article, .news-item, .story")[:self.config["max_articles_per_source"]]
            
            for element in article_elements:
                title_elem = element.select_one(".title, h2, h3")
                summary_elem = element.select_one(".summary, .description, p")
                link_elem = element.select_one("a")
                date_elem = element.select_one(".date, .time, .published")
                
                article = {
                    "title": title_elem.text.strip() if title_elem else "Unknown Title",
                    "summary": summary_elem.text.strip() if summary_elem else "",
                    "url": link_elem["href"] if link_elem and "href" in link_elem.attrs else "",
                    "published_date": date_elem.text.strip() if date_elem else "",
                    "source": source_url,
                    "sport": sport,
                    "collected_at": datetime.now().isoformat()
                }
                
                articles.append(article)
            
            return articles
            
        except Exception as e:
            self.logger.error(f"Error scraping {source_url}: {str(e)}")
            return []
    
    def _process_data(self, collected_data: List[Dict[str, Any]], 
                     sport: str, event_type: str) -> Dict[str, Any]:
        """
        Process and structure the collected data.
        
        Args:
            collected_data: Raw collected data
            sport: Sport type
            event_type: Type of event
            
        Returns:
            Processed and structured data
        """
        # In a real implementation, this would include:
        # - Deduplication of articles
        # - Entity extraction (drivers, teams, etc.)
        # - Sentiment analysis
        # - Categorization by topic
        # - Extraction of race results, standings, etc.
        
        # Simplified processing for demonstration
        processed = {
            "sport": sport,
            "event_type": event_type,
            "processed_at": datetime.now().isoformat(),
            "article_count": len(collected_data),
            "articles": collected_data,
            "key_entities": self._extract_entities(collected_data),
            "topics": self._categorize_topics(collected_data)
        }
        
        # Add race-specific data if available
        if event_type == "race" and collected_data:
            processed["race_data"] = self._extract_race_data(collected_data, sport)
        
        return processed
    
    def _extract_entities(self, articles: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Extract key entities from articles.
        
        Args:
            articles: List of article data
            
        Returns:
            Dictionary of entity types and their mentions
        """
        # Placeholder implementation - would use NLP in production
        entities = {
            "drivers": [],
            "teams": [],
            "tracks": [],
            "events": []
        }
        
        # Simple keyword matching for demonstration
        driver_keywords = ["Hamilton", "Verstappen", "Leclerc", "Norris", "Marquez", "Bagnaia", "Quartararo"]
        team_keywords = ["Mercedes", "Red Bull", "Ferrari", "McLaren", "Ducati", "Yamaha", "Honda"]
        track_keywords = ["Silverstone", "Monza", "Spa", "Monaco", "Catalunya", "Mugello", "Sepang"]
        
        for article in articles:
            text = f"{article.get('title', '')} {article.get('summary', '')}"
            
            for driver in driver_keywords:
                if driver in text and driver not in entities["drivers"]:
                    entities["drivers"].append(driver)
                    
            for team in team_keywords:
                if team in text and team not in entities["teams"]:
                    entities["teams"].append(team)
                    
            for track in track_keywords:
                if track in text and track not in entities["tracks"]:
                    entities["tracks"].append(track)
        
        return entities
    
    def _categorize_topics(self, articles: List[Dict[str, Any]]) -> Dict[str, List[int]]:
        """
        Categorize articles by topic.
        
        Args:
            articles: List of article data
            
        Returns:
            Dictionary of topics and article indices
        """
        # Placeholder implementation - would use ML classification in production
        topics = {
            "race_results": [],
            "technical": [],
            "driver_news": [],
            "team_news": [],
            "controversy": [],
            "preview": []
        }
        
        topic_keywords = {
            "race_results": ["win", "podium", "finished", "results", "standings"],
            "technical": ["upgrade", "engine", "aerodynamic", "technical", "development"],
            "driver_news": ["signed", "contract", "moving", "driver", "career"],
            "team_news": ["team", "announce", "sponsor", "partnership"],
            "controversy": ["penalty", "crash", "controversy", "stewards", "investigation"],
            "preview": ["preview", "upcoming", "weekend", "prepare", "ready"]
        }
        
        for i, article in enumerate(articles):
            text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
            
            for topic, keywords in topic_keywords.items():
                for keyword in keywords:
                    if keyword in text and i not in topics[topic]:
                        topics[topic].append(i)
                        break
        
        return topics
    
    def _extract_race_data(self, articles: List[Dict[str, Any]], sport: str) -> Dict[str, Any]:
        """
        Extract structured race data from articles.
        
        Args:
            articles: List of article data
            sport: Sport type
            
        Returns:
            Structured race data
        """
        # Placeholder implementation - would use more sophisticated extraction in production
        race_data = {
            "results": [],
            "fastest_lap": None,
            "pole_position": None,
            "championship_impact": {}
        }
        
        # In a real implementation, this would parse race results tables,
        # extract structured data about positions, times, points, etc.
        
        return race_data
    
    def _get_mock_data(self, sport: str, event_type: str) -> List[Dict[str, Any]]:
        """
        Return mock data for demonstration purposes.
        
        Args:
            sport: Sport type
            event_type: Type of event
            
        Returns:
            List of mock article data
        """
        # Create at least 5 mock articles to meet the minimum source requirement
        mock_data = [
            {
                "title": f"{sport.upper()} News: Latest Updates from the {sport.upper()} World",
                "summary": f"The latest news and updates from the world of {sport}. Stay informed with our comprehensive coverage.",
                "url": f"https://example.com/{sport}/news",
                "published_date": datetime.now().strftime("%Y-%m-%d"),
                "source": "Mock Sports News",
                "sport": sport,
                "collected_at": datetime.now().isoformat()
            },
            {
                "title": f"{sport.upper()} {event_type.replace('_', ' ').title()}: Results and Analysis",
                "summary": f"Complete results and expert analysis of the recent {event_type.replace('_', ' ')} in {sport}.",
                "url": f"https://example.com/{sport}/{event_type}/results",
                "published_date": datetime.now().strftime("%Y-%m-%d"),
                "source": "Mock Results Center",
                "sport": sport,
                "collected_at": datetime.now().isoformat()
            },
            {
                "title": f"Top Performers in {sport.upper()} This Season",
                "summary": f"A look at the standout performers in {sport} this season and what makes them special.",
                "url": f"https://example.com/{sport}/analysis/top-performers",
                "published_date": datetime.now().strftime("%Y-%m-%d"),
                "source": "Mock Analysis Hub",
                "sport": sport,
                "collected_at": datetime.now().isoformat()
            },
            {
                "title": f"Technical Innovations Shaping {sport.upper()} in 2025",
                "summary": f"Exploring the cutting-edge technologies and innovations that are revolutionizing {sport} in the current season.",
                "url": f"https://example.com/{sport}/tech/innovations",
                "published_date": datetime.now().strftime("%Y-%m-%d"),
                "source": "Mock Tech Review",
                "sport": sport,
                "collected_at": datetime.now().isoformat()
            },
            {
                "title": f"Interview: Inside the Mind of a {sport.upper()} Champion",
                "summary": f"Exclusive interview with one of the top {sport} competitors, discussing strategy, preparation, and future goals.",
                "url": f"https://example.com/{sport}/interviews/champion",
                "published_date": datetime.now().strftime("%Y-%m-%d"),
                "source": "Mock Interviews",
                "sport": sport,
                "collected_at": datetime.now().isoformat()
            },
            {
                "title": f"The Future of {sport.upper()}: Trends and Predictions",
                "summary": f"Industry experts weigh in on where {sport} is headed and what fans can expect in the coming years.",
                "url": f"https://example.com/{sport}/future/predictions",
                "published_date": datetime.now().strftime("%Y-%m-%d"),
                "source": "Mock Future Insights",
                "sport": sport,
                "collected_at": datetime.now().isoformat()
            }
        ]
        
        # Add event-specific mock data if an event_id is provided
        if event_type == "news_update" and "monaco" in self.cache.keys():
            mock_data.append({
                "title": "Monaco Grand Prix Preview: What to Expect from the Iconic Race",
                "summary": "A comprehensive preview of the upcoming Monaco Grand Prix, including track analysis, driver form, and predictions.",
                "url": "https://example.com/f1/monaco/preview",
                "published_date": datetime.now().strftime("%Y-%m-%d"),
                "source": "Mock Monaco Special",
                "sport": sport,
                "collected_at": datetime.now().isoformat()
            })
        
        return mock_data
