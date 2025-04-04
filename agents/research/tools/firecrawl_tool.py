"""
Firecrawl tool for the Research Agent.
Provides enhanced web crawling capabilities using the Firecrawl API.
"""

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

# Import the firecrawl package
from firecrawl import FirecrawlApp
from langchain_community.document_loaders import FireCrawlLoader

class FirecrawlTool:
    """
    Enhanced web crawling tool using Firecrawl for high-quality content extraction.
    """

    def __init__(self, data_dir: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Firecrawl tool.

        Args:
            data_dir: Directory to store crawled data
            config: Configuration parameters
        """
        self.logger = logging.getLogger("dopcast.research.firecrawl")
        self.data_dir = data_dir
        self.config = config or {}

        # Get API key from config or environment
        self.api_key = self.config.get("firecrawl_api_key", os.environ.get("FIRECRAWL_API_KEY", ""))

        if not self.api_key:
            self.logger.warning("No Firecrawl API key provided. Set FIRECRAWL_API_KEY environment variable or pass in config.")
        else:
            self.logger.info("Firecrawl API key found and will be used for crawling")
            # Initialize the Firecrawl app
            self.app = FirecrawlApp(api_key=self.api_key)

        # Ensure crawled data directory exists
        self.crawl_dir = os.path.join(self.data_dir, "crawled")
        os.makedirs(self.crawl_dir, exist_ok=True)

    def crawl_url(self, url: str, sport: str, event_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Crawl a specific URL using Firecrawl.

        Args:
            url: URL to crawl
            sport: Sport type for context
            event_type: Type of event

        Returns:
            Extracted content from the URL
        """
        if not self.api_key:
            self.logger.error("Firecrawl API key is required for crawling")
            return self.get_mock_crawl_result(url, sport, event_type)

        self.logger.info(f"Crawling URL with Firecrawl: {url}")

        try:
            # Use the FireCrawlLoader from LangChain
            if self.api_key:
                try:
                    # First try using the LangChain loader
                    loader = FireCrawlLoader(
                        api_key=self.api_key,
                        url=url,  # Changed from urls=[url] to url=url
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
                            "url": url
                        }
                    else:
                        # If no documents were loaded, try using the FirecrawlApp directly
                        self.logger.info(f"No documents loaded with FireCrawlLoader, trying FirecrawlApp for {url}")
                        scrape_result = self.app.scrape_url(url, params={"formats": ["markdown"]})
                        data = {
                            "title": scrape_result.get("title", "Untitled"),
                            "content": scrape_result.get("markdown", ""),
                            "url": url
                        }
                except Exception as e:
                    self.logger.error(f"Error with FireCrawlLoader: {str(e)}")
                    # Try using the FirecrawlApp directly as fallback
                    try:
                        self.logger.info(f"Falling back to FirecrawlApp for {url}")
                        scrape_result = self.app.scrape_url(url, params={"formats": ["markdown"]})
                        data = {
                            "title": scrape_result.get("title", "Untitled"),
                            "content": scrape_result.get("markdown", ""),
                            "url": url
                        }
                    except Exception as e2:
                        self.logger.error(f"Firecrawl API error: {str(e2)}")
                        return self.get_mock_crawl_result(url, sport, event_type)
            else:
                self.logger.error("No Firecrawl API key available")
                return self.get_mock_crawl_result(url, sport, event_type)

            if not data or "content" not in data:
                self.logger.warning(f"No content extracted from URL: {url}")
                return self.get_mock_crawl_result(url, sport, event_type)

            # Create result with consistent format
            result = {
                "url": url,
                "title": data.get("title", "Untitled"),
                "content": data.get("content", ""),
                "summary": data.get("content", "")[:500] + "...",  # Create a summary from the content
                "metadata": {
                    "author": data.get("author", ""),
                    "description": data.get("description", ""),
                    "published_date": data.get("published_date", datetime.now().strftime("%Y-%m-%d")),
                    "language": data.get("language", "en"),
                    "source": "Firecrawl"
                },
                "sport": sport,
                "event_type": event_type,
                "crawled_at": datetime.now().isoformat()
            }

            # Save result to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"firecrawl_{sport}_{timestamp}.json"
            filepath = os.path.join(self.crawl_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Successfully crawled URL: {url}")
            return result

        except Exception as e:
            self.logger.error(f"Error crawling URL with Firecrawl: {str(e)}")
            return self.get_mock_crawl_result(url, sport, event_type)

    def crawl_urls(self, urls: List[str], sport: str, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Crawl multiple URLs using Firecrawl.

        Args:
            urls: List of URLs to crawl
            sport: Sport type for context
            event_type: Type of event

        Returns:
            List of extracted content from the URLs
        """
        results = []
        for url in urls:
            result = self.crawl_url(url, sport, event_type)
            results.append(result)

        return results

    def get_mock_crawl_result(self, url: str, sport: str, event_type: Optional[str] = None) -> Dict[str, Any]:
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

        # Create mock result
        mock_result = {
            "url": url,
            "title": f"{sport.upper()} News: Latest Updates",
            "content": f"This is a mock article about {sport}. It contains information about recent events and news. " +
                      f"The article discusses various aspects of {sport} including teams, drivers, and competitions. " +
                      f"Experts provide analysis and insights into the current state of {sport} and predictions for upcoming events.",
            "metadata": {
                "author": "Mock Author",
                "description": f"Latest news and updates about {sport}",
                "published_date": datetime.now().strftime("%Y-%m-%d"),
                "language": "en",
                "source": "Mock Firecrawl"
            },
            "sport": sport,
            "event_type": event_type,
            "crawled_at": datetime.now().isoformat()
        }

        return mock_result
