"""
Enhanced Firecrawl tool for the Research Agent.
Provides improved web crawling capabilities with targeted URL selection.
"""

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import asyncio
import re

# Try to import Firecrawl
try:
    from langchain_community.document_loaders import FireCrawlLoader
    from firecrawl import FirecrawlApp
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False

class EnhancedFirecrawlTool:
    """
    Enhanced web crawling tool using Firecrawl for targeted content extraction.
    """

    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the enhanced Firecrawl tool.

        Args:
            api_key: Firecrawl API key
            config: Configuration parameters
        """
        self.logger = logging.getLogger("dopcast.research.enhanced_firecrawl")
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        self.config = config or {}
        
        # Set default configuration
        self.max_depth = self.config.get("max_depth", 2)
        self.max_urls = self.config.get("max_urls", 5)
        
        # Set up results directory
        self.results_dir = os.path.join("output", "research", "firecrawl")
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Set up summaries directory
        self.summaries_dir = os.path.join("output", "research", "summaries")
        os.makedirs(self.summaries_dir, exist_ok=True)
        
        # Initialize Firecrawl if available
        if FIRECRAWL_AVAILABLE and self.api_key:
            self.app = FirecrawlApp(api_key=self.api_key)
            self.logger.info("Enhanced Firecrawl Tool initialized with API key")
        else:
            self.app = None
            if not FIRECRAWL_AVAILABLE:
                self.logger.warning("Firecrawl not available. Install with: pip install firecrawl")
            else:
                self.logger.warning("No Firecrawl API key provided")

    def is_targeted_url(self, url: str) -> bool:
        """
        Check if a URL is a targeted source (news article, Wikipedia, blog post, etc.).

        Args:
            url: URL to check

        Returns:
            True if the URL is a targeted source, False otherwise
        """
        # List of patterns for targeted sources
        targeted_patterns = [
            # News sites
            r'news\.', r'\.news', r'/news/', r'/article/', r'/articles/',
            # Wikipedia
            r'wikipedia\.org', r'wiki/',
            # Blogs
            r'blog\.', r'/blog/', r'blogs\.',
            # Sports news sites
            r'espn\.com', r'skysports\.com', r'autosport\.com', r'motorsport\.com',
            r'formula1\.com', r'motogp\.com', r'crash\.net', r'the-race\.com',
            # Forums and discussion sites
            r'forum\.', r'/forum/', r'forums\.',
            # Official team sites
            r'redbullracing\.com', r'mercedesamgf1\.com', r'ferrari\.com', r'mclaren\.com',
            r'astonmartinf1\.com', r'alpinecars\.com', r'williamsf1\.com', r'alphatauri\.com',
            r'sauber-group\.com', r'haasf1team\.com',
            # MotoGP team sites
            r'ducati\.com', r'yamahamotogp\.com', r'honda\.racing', r'suzuki-racing\.com',
            r'ktmfactoryracing\.com', r'aprilia\.com'
        ]
        
        # Check if the URL matches any of the patterns
        for pattern in targeted_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        return False

    async def crawl_targeted_urls(self, urls: List[str], sport: str, 
                           event_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Crawl a list of URLs, filtering for targeted sources.

        Args:
            urls: List of URLs to crawl
            sport: Sport type for context
            event_type: Type of event

        Returns:
            Dictionary with crawl results and summary
        """
        # Filter for targeted URLs
        targeted_urls = [url for url in urls if self.is_targeted_url(url)]
        
        if not targeted_urls:
            self.logger.warning(f"No targeted URLs found in the list of {len(urls)} URLs")
            return {
                "results": [],
                "summary": "No targeted URLs found.",
                "results_file": None,
                "summary_file": None,
                "url_count": 0
            }
        
        self.logger.info(f"Found {len(targeted_urls)} targeted URLs out of {len(urls)} total URLs")
        
        # Crawl each targeted URL
        results = []
        for url in targeted_urls[:self.max_urls]:  # Limit to max_urls
            result = await self._crawl_url(url, sport, event_type)
            if result:
                results.append(result)
        
        # Generate a timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save results to file
        filename = f"firecrawl_{sport}_{timestamp}.json"
        filepath = os.path.join(self.results_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # Create a summary of the crawl results
        summary = self._create_crawl_summary(results, targeted_urls, sport, event_type)
        
        # Save summary to file
        summary_filename = f"firecrawl_summary_{sport}_{timestamp}.md"
        summary_filepath = os.path.join(self.summaries_dir, summary_filename)
        
        with open(summary_filepath, "w", encoding="utf-8") as f:
            f.write(summary)
        
        self.logger.info(f"Crawled {len(results)} targeted URLs for {sport}")
        
        return {
            "results": results,
            "summary": summary,
            "results_file": filepath,
            "summary_file": summary_filepath,
            "url_count": len(targeted_urls)
        }

    async def _crawl_url(self, url: str, sport: str, 
                   event_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Crawl a single URL using Firecrawl.

        Args:
            url: URL to crawl
            sport: Sport type for context
            event_type: Type of event

        Returns:
            Dictionary with crawl result or None if failed
        """
        self.logger.info(f"Crawling URL: {url}")
        
        if not FIRECRAWL_AVAILABLE or not self.api_key:
            self.logger.warning("Firecrawl not available or no API key provided")
            return self._get_mock_crawl_result(url, sport, event_type)
        
        try:
            # Use the FireCrawlLoader from LangChain
            loader = FireCrawlLoader(
                api_key=self.api_key,
                url=url,
                mode="scrape"  # Use scrape mode for single URLs
            )
            
            # Load the documents
            documents = loader.load()
            
            if documents:
                # Process the first document
                doc = documents[0]
                data = {
                    "title": doc.metadata.get("title", "Untitled"),
                    "content": doc.page_content,
                    "url": url,
                    "metadata": {
                        "source": self._extract_domain(url),
                        "crawled_at": datetime.now().isoformat(),
                        "sport": sport,
                        "event_type": event_type
                    }
                }
                
                return data
            else:
                # If no documents were loaded, try using the FirecrawlApp directly
                self.logger.info(f"No documents loaded with FireCrawlLoader, trying FirecrawlApp for {url}")
                scrape_result = self.app.scrape_url(url, params={"formats": ["markdown"]})
                
                data = {
                    "title": scrape_result.get("title", "Untitled"),
                    "content": scrape_result.get("markdown", ""),
                    "url": url,
                    "metadata": {
                        "source": self._extract_domain(url),
                        "crawled_at": datetime.now().isoformat(),
                        "sport": sport,
                        "event_type": event_type
                    }
                }
                
                return data
        
        except Exception as e:
            self.logger.error(f"Error crawling URL {url}: {str(e)}")
            return self._get_mock_crawl_result(url, sport, event_type)

    def _extract_domain(self, url: str) -> str:
        """
        Extract the domain from a URL.

        Args:
            url: URL to extract domain from

        Returns:
            Domain name
        """
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if match:
            return match.group(1)
        return "unknown"

    def _create_crawl_summary(self, results: List[Dict[str, Any]], 
                            targeted_urls: List[str], sport: str,
                            event_type: Optional[str] = None) -> str:
        """
        Create a summary of the crawl results.

        Args:
            results: List of crawl results
            targeted_urls: List of targeted URLs
            sport: Sport type
            event_type: Type of event

        Returns:
            Markdown summary of the crawl results
        """
        # Create a title for the summary
        title = f"# Firecrawl Results Summary: {sport.upper()}"
        if event_type:
            title += f" {event_type}"
        
        # Add metadata
        metadata = f"\n\n**Crawl Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        metadata += f"**URLs Processed:** {len(results)} of {len(targeted_urls)} targeted URLs\n\n"
        
        # Add a table of contents
        toc = "## Table of Contents\n\n"
        for i, result in enumerate(results):
            toc += f"{i+1}. [{result.get('title', f'Result {i+1}')}](#{i+1})\n"
        
        # Add the results
        content = "\n\n## Results\n\n"
        for i, result in enumerate(results):
            content += f"### {i+1}. {result.get('title', f'Result {i+1}')}\n\n"
            content += f"**URL:** {result.get('url', 'N/A')}\n\n"
            content += f"**Source:** {result.get('metadata', {}).get('source', 'Unknown')}\n\n"
            content += "**Content Excerpt:**\n\n"
            
            # Limit content length for readability
            result_content = result.get('content', 'No content available.')
            if len(result_content) > 1000:
                content += f"```\n{result_content[:1000]}...\n```\n\n"
                content += f"*Content truncated. Full length: {len(result_content)} characters.*\n\n"
            else:
                content += f"```\n{result_content}\n```\n\n"
            
            content += "---\n\n"
        
        # Combine all sections
        summary = f"{title}{metadata}{toc}{content}"
        
        return summary

    def _get_mock_crawl_result(self, url: str, sport: str, 
                             event_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Return mock crawl result for testing purposes.

        Args:
            url: URL that would have been crawled
            sport: Sport type
            event_type: Type of event

        Returns:
            Mock crawl result
        """
        self.logger.info(f"Generating mock crawl result for: {url}")
        
        domain = self._extract_domain(url)
        
        # Create a mock result
        result = {
            "title": f"Mock Article: {sport.upper()} {event_type or 'News'} from {domain}",
            "content": f"This is a mock article about {sport} {event_type or 'news'} from {domain}. It contains information that would have been extracted from the URL: {url}. The content includes details about recent events, analysis, and expert opinions. This is placeholder text that would normally be replaced with the actual content from the webpage.",
            "url": url,
            "metadata": {
                "source": domain,
                "crawled_at": datetime.now().isoformat(),
                "sport": sport,
                "event_type": event_type,
                "is_mock": True
            }
        }
        
        return result
