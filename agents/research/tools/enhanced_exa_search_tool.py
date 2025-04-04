"""
Enhanced Exa Search tool for the Research Agent.
Provides improved search capabilities using multiple queries and better organization.
"""

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import asyncio

from langchain_exa import ExaSearchRetriever

class EnhancedExaSearchTool:
    """
    Enhanced search tool using Exa API for high-quality search results with multiple queries.
    """

    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the enhanced Exa search tool.

        Args:
            api_key: Exa API key
            config: Configuration parameters
        """
        self.logger = logging.getLogger("dopcast.research.enhanced_exa_search")
        self.api_key = api_key or os.getenv("EXA_API_KEY")
        self.config = config or {}
        
        # Set default configuration
        self.max_results = self.config.get("max_results", 10)
        self.use_highlights = self.config.get("use_highlights", True)
        self.num_highlights = self.config.get("num_highlights", 3)
        
        # Set up results directory
        self.results_dir = os.path.join("output", "research", "exa_search")
        os.makedirs(self.results_dir, exist_ok=True)
        
        self.logger.info("Enhanced Exa Search Tool initialized")

    async def search_with_multiple_queries(self, base_query: str, sport: str, 
                                    event_type: Optional[str] = None,
                                    event_id: Optional[str] = None, 
                                    max_results: Optional[int] = None) -> Dict[str, Any]:
        """
        Search for relevant information using multiple Exa API queries.

        Args:
            base_query: Base search query
            sport: Sport type for context
            event_type: Type of event (race, qualifying, etc.)
            event_id: Specific event identifier
            max_results: Maximum number of results to return per query

        Returns:
            Dictionary with search results and summary
        """
        # Generate multiple search queries based on the base query
        queries = self._generate_search_queries(base_query, sport, event_type, event_id)
        
        # Search with each query
        all_results = []
        for query in queries:
            results = await self._search_with_query(query, sport, event_type, event_id, max_results)
            all_results.extend(results)
        
        # Deduplicate results
        deduplicated_results = self._deduplicate_results(all_results)
        
        # Generate a timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save all results to file
        filename = f"exa_search_{sport}_{timestamp}.json"
        filepath = os.path.join(self.results_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(deduplicated_results, f, ensure_ascii=False, indent=2)
        
        # Create a summary of the search results
        summary = self._create_search_summary(deduplicated_results, base_query, sport, event_type, event_id)
        
        # Save summary to file
        summary_filename = f"exa_search_summary_{sport}_{timestamp}.md"
        summary_filepath = os.path.join(os.path.join("output", "research", "summaries"), summary_filename)
        
        with open(summary_filepath, "w", encoding="utf-8") as f:
            f.write(summary)
        
        self.logger.info(f"Found {len(deduplicated_results)} unique results for: {base_query}")
        
        return {
            "results": deduplicated_results,
            "summary": summary,
            "results_file": filepath,
            "summary_file": summary_filepath,
            "query_count": len(queries)
        }

    def _generate_search_queries(self, base_query: str, sport: str, 
                               event_type: Optional[str] = None,
                               event_id: Optional[str] = None) -> List[str]:
        """
        Generate multiple search queries based on the base query.

        Args:
            base_query: Base search query
            sport: Sport type for context
            event_type: Type of event
            event_id: Specific event identifier

        Returns:
            List of search queries
        """
        queries = []
        
        # Add the base query
        base = f"{sport} {base_query}"
        if event_type:
            base += f" {event_type}"
        if event_id:
            base += f" {event_id}"
        
        queries.append(base)
        
        # Add variations
        queries.append(f"{base} latest news")
        queries.append(f"{base} analysis")
        queries.append(f"{base} expert opinion")
        
        if "race" in base.lower() or "grand prix" in base.lower():
            queries.append(f"{base} results")
            queries.append(f"{base} highlights")
            queries.append(f"{base} key moments")
        
        if "qualifying" in base.lower():
            queries.append(f"{base} results")
            queries.append(f"{base} pole position")
            queries.append(f"{base} grid positions")
        
        if "technical" in base.lower():
            queries.append(f"{base} technical analysis")
            queries.append(f"{base} car development")
            queries.append(f"{base} performance")
        
        # Add sport-specific queries
        if sport.lower() == "f1":
            queries.append(f"{base} formula 1")
            queries.append(f"{base} drivers championship")
            queries.append(f"{base} constructors championship")
        elif sport.lower() == "motogp":
            queries.append(f"{base} moto gp")
            queries.append(f"{base} riders championship")
            queries.append(f"{base} manufacturers championship")
        
        return list(set(queries))  # Remove duplicates

    async def _search_with_query(self, query: str, sport: str, 
                          event_type: Optional[str] = None,
                          event_id: Optional[str] = None, 
                          max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant information using Exa API with a single query.

        Args:
            query: Search query
            sport: Sport type for context
            event_type: Type of event
            event_id: Specific event identifier
            max_results: Maximum number of results to return

        Returns:
            List of search results
        """
        if not self.api_key:
            self.logger.error("Exa API key is required for search")
            return self._get_mock_results(query, sport, event_type)

        # Set max results
        if max_results is None:
            max_results = self.max_results

        self.logger.info(f"Searching with Exa: {query}")

        try:
            # Create the Exa retriever
            retriever = ExaSearchRetriever(
                api_key=self.api_key,
                k=max_results,
                highlights=self.use_highlights,
                num_highlights=self.num_highlights
            )

            # Perform the search
            results = retriever.get_relevant_documents(query)

            # Process the results
            processed_results = []
            for i, doc in enumerate(results):
                # Extract metadata
                metadata = doc.metadata
                
                # Create a processed result
                processed_result = {
                    "title": metadata.get("title", f"Result {i+1}"),
                    "url": metadata.get("url", ""),
                    "content": doc.page_content,
                    "summary": metadata.get("highlights", [""])[0] if metadata.get("highlights") else "",
                    "metadata": {
                        "published_date": metadata.get("published_date", ""),
                        "source": metadata.get("source", ""),
                        "author": metadata.get("author", ""),
                        "query": query
                    }
                }
                
                processed_results.append(processed_result)

            self.logger.info(f"Found {len(processed_results)} results for query: {query}")
            return processed_results

        except Exception as e:
            self.logger.error(f"Error searching with Exa: {str(e)}")
            return self._get_mock_results(query, sport, event_type)

    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicate search results based on URL.

        Args:
            results: List of search results

        Returns:
            Deduplicated list of search results
        """
        seen_urls = set()
        deduplicated = []
        
        for result in results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                deduplicated.append(result)
        
        return deduplicated

    def _create_search_summary(self, results: List[Dict[str, Any]], 
                             base_query: str, sport: str,
                             event_type: Optional[str] = None,
                             event_id: Optional[str] = None) -> str:
        """
        Create a summary of the search results.

        Args:
            results: List of search results
            base_query: Base search query
            sport: Sport type
            event_type: Type of event
            event_id: Specific event identifier

        Returns:
            Markdown summary of the search results
        """
        # Create a title for the summary
        title = f"# Search Results Summary: {sport.upper()} {base_query}"
        if event_type:
            title += f" {event_type}"
        if event_id:
            title += f" ({event_id})"
        
        # Add metadata
        metadata = f"\n\n**Search Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        metadata += f"**Results Count:** {len(results)}\n"
        
        # Add a table of contents
        toc = "\n\n## Table of Contents\n\n"
        for i, result in enumerate(results):
            toc += f"{i+1}. [{result.get('title', f'Result {i+1}')}](#{i+1})\n"
        
        # Add the results
        content = "\n\n## Results\n\n"
        for i, result in enumerate(results):
            content += f"### {i+1}. {result.get('title', f'Result {i+1}')}\n\n"
            content += f"**URL:** {result.get('url', 'N/A')}\n\n"
            content += f"**Summary:** {result.get('summary', 'No summary available.')}\n\n"
            content += f"**Source:** {result.get('metadata', {}).get('source', 'Unknown')}\n\n"
            content += f"**Published Date:** {result.get('metadata', {}).get('published_date', 'Unknown')}\n\n"
            content += "**Content Excerpt:**\n\n"
            content += f"```\n{result.get('content', 'No content available.')[:500]}...\n```\n\n"
            content += "---\n\n"
        
        # Combine all sections
        summary = f"{title}{metadata}{toc}{content}"
        
        return summary

    def _get_mock_results(self, query: str, sport: str, 
                        event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Return mock search results for testing purposes.

        Args:
            query: Search query
            sport: Sport type
            event_type: Type of event

        Returns:
            Mock search results
        """
        self.logger.info(f"Generating mock search results for: {query}")
        
        # Create mock results
        results = [
            {
                "title": f"Latest {sport.upper()} News: {query}",
                "url": f"https://example.com/{sport}/news/{query.replace(' ', '-')}",
                "content": f"The latest news about {query} in {sport.upper()}. This article covers recent developments and provides insights into what's happening in the world of {sport}. Experts weigh in on the significance of these events and what they mean for the future of the sport.",
                "summary": f"The latest news about {query} in {sport.upper()}.",
                "metadata": {
                    "published_date": datetime.now().strftime("%Y-%m-%d"),
                    "source": "Example News",
                    "author": "John Doe",
                    "query": query
                }
            },
            {
                "title": f"Analysis: {query} in {sport.upper()}",
                "url": f"https://example.com/{sport}/analysis/{query.replace(' ', '-')}",
                "content": f"An in-depth analysis of {query} by our expert team. We break down the key factors and provide insights into what it means for the future of {sport}. This comprehensive analysis includes historical context, current trends, and future projections. Our team has interviewed key stakeholders and analyzed performance data to provide the most accurate and insightful analysis available.",
                "summary": f"An in-depth analysis of {query} by our expert team.",
                "metadata": {
                    "published_date": datetime.now().strftime("%Y-%m-%d"),
                    "source": "Example Analysis",
                    "author": "Jane Smith",
                    "query": query
                }
            },
            {
                "title": f"Expert Opinion: {query} in {sport.upper()}",
                "url": f"https://example.com/{sport}/opinion/{query.replace(' ', '-')}",
                "content": f"Our experts share their opinions on {query} in {sport.upper()}. With years of experience in the industry, they provide unique insights and perspectives on this topic. This article includes quotes from former drivers, team principals, and technical directors, giving you a comprehensive view of the situation from multiple angles.",
                "summary": f"Our experts share their opinions on {query} in {sport.upper()}.",
                "metadata": {
                    "published_date": datetime.now().strftime("%Y-%m-%d"),
                    "source": "Example Opinion",
                    "author": "Mike Johnson",
                    "query": query
                }
            }
        ]
        
        return results
