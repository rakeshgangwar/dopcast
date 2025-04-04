"""
Exa Search tool for the Research Agent.
Provides enhanced search capabilities using the Exa API.
"""

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from langchain_exa import ExaSearchRetriever

class ExaSearchTool:
    """
    Enhanced search tool using Exa API for high-quality search results.
    """

    def __init__(self, data_dir: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Exa search tool.

        Args:
            data_dir: Directory to store search results
            config: Configuration parameters
        """
        self.logger = logging.getLogger("dopcast.research.exa_search")
        self.data_dir = data_dir
        self.config = config or {}

        # Get API key from config or environment
        self.api_key = self.config.get("exa_api_key", os.environ.get("EXA_API_KEY", ""))

        if not self.api_key:
            self.logger.warning("No Exa API key provided. Set EXA_API_KEY environment variable or pass in config.")
        else:
            self.logger.info("Exa API key found and will be used for searches")

        # Ensure search results directory exists
        self.results_dir = os.path.join(self.data_dir, "search_results")
        os.makedirs(self.results_dir, exist_ok=True)

        # Default parameters
        self.max_results = self.config.get("max_results", 10)
        self.use_highlights = self.config.get("use_highlights", True)
        self.num_highlights = self.config.get("num_highlights", 3)

    def search(self, query: str, sport: str, event_type: str = None,
             event_id: Optional[str] = None, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant information using Exa API.

        Args:
            query: Search query
            sport: Sport type for context
            event_type: Type of event (race, qualifying, etc.)
            event_id: Specific event identifier
            max_results: Maximum number of results to return

        Returns:
            List of search results
        """
        if not self.api_key:
            self.logger.error("Exa API key is required for search")
            return self.get_mock_results(query, sport, event_type)

        # Set max results
        if max_results is None:
            max_results = self.max_results

        # Enhance query with sport context
        enhanced_query = f"{sport} {query}"
        if event_type:
            enhanced_query += f" {event_type}"
        if event_id:
            enhanced_query += f" {event_id}"

        self.logger.info(f"Searching with Exa: {enhanced_query}")

        try:
            # Create the Exa retriever
            retriever = ExaSearchRetriever(
                api_key=self.api_key,
                k=max_results,
                highlights=self.use_highlights,
                num_highlights=self.num_highlights
            )

            # Perform the search
            results = retriever.get_relevant_documents(enhanced_query)

            # Process results
            processed_results = []
            for doc in results:
                result = {
                    "title": doc.metadata.get("title", "Untitled"),
                    "url": doc.metadata.get("url", ""),
                    "content": doc.page_content,
                    "summary": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                    "metadata": {
                        "published_date": doc.metadata.get("published_date", datetime.now().strftime("%Y-%m-%d")),
                        "source": doc.metadata.get("source", "Exa Search"),
                        "language": doc.metadata.get("language", "en")
                    },
                    "sport": sport,
                    "event_type": event_type,
                    "collected_at": datetime.now().isoformat()
                }

                # Add highlights if available
                if "highlights" in doc.metadata:
                    result["highlights"] = doc.metadata["highlights"]

                processed_results.append(result)

            # Save results to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"exa_search_{sport}_{timestamp}.json"
            filepath = os.path.join(self.results_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(processed_results, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Found {len(processed_results)} results for: {enhanced_query}")
            return processed_results

        except Exception as e:
            self.logger.error(f"Error searching with Exa: {str(e)}")
            return self.get_mock_results(query, sport, event_type)

    def get_mock_results(self, query: str, sport: str, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Return mock search results for testing purposes.

        Args:
            query: Search query
            sport: Sport type
            event_type: Type of event

        Returns:
            List of mock search results
        """
        self.logger.info(f"Generating mock search results for: {query}")

        # Create mock results
        mock_results = [
            {
                "title": f"{sport.upper()} News: Latest Updates on {query}",
                "url": f"https://example.com/{sport}/news/{query.replace(' ', '-')}",
                "content": f"The latest news and updates on {query} in the world of {sport}. This article covers recent developments and expert analysis. Our team of experts has been following the developments closely and provides comprehensive coverage of all the important events. The article includes interviews with key figures, statistical analysis, and predictions for future outcomes.",
                "summary": f"The latest news and updates on {query} in the world of {sport}. This article covers recent developments and expert analysis.",
                "metadata": {
                    "published_date": datetime.now().strftime("%Y-%m-%d"),
                    "source": "Mock Exa Search",
                    "language": "en"
                },
                "sport": sport,
                "event_type": event_type,
                "collected_at": datetime.now().isoformat()
            },
            {
                "title": f"Expert Analysis: {query} in {sport.upper()}",
                "url": f"https://example.com/{sport}/analysis/{query.replace(' ', '-')}",
                "content": f"An in-depth analysis of {query} by our expert team. We break down the key factors and provide insights into what it means for the future of {sport}. This comprehensive analysis includes historical context, current trends, and future projections. Our team has interviewed key stakeholders and analyzed performance data to provide the most accurate and insightful analysis available.",
                "summary": f"An in-depth analysis of {query} by our expert team. We break down the key factors and provide insights into what it means for the future of {sport}.",
                "metadata": {
                    "published_date": datetime.now().strftime("%Y-%m-%d"),
                    "source": "Mock Exa Search",
                    "language": "en"
                },
                "sport": sport,
                "event_type": event_type,
                "collected_at": datetime.now().isoformat()
            }
        ]

        return mock_results
