"""
Web scraper tool for the Research Agent.
Provides enhanced web scraping capabilities with async support and error handling.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
import aiohttp
from bs4 import BeautifulSoup
import os
from datetime import datetime
import json

class WebScraperTool:
    """
    Enhanced web scraper tool with async support and better error handling.
    """

    def __init__(self, data_dir: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the web scraper tool.

        Args:
            data_dir: Directory to store raw data
            config: Configuration parameters
        """
        self.logger = logging.getLogger("dopcast.research.web_scraper")
        self.data_dir = data_dir
        self.config = config or {}

        # Ensure raw data directory exists
        os.makedirs(os.path.join(self.data_dir, "raw"), exist_ok=True)

        # Initialize aiohttp session
        self.session = None

    async def setup(self):
        """Initialize the aiohttp session."""
        if self.session is None or self.session.closed:
            # Create a custom SSL context that bypasses verification
            ssl_context = None
            verify_ssl = not self.config.get("bypass_ssl_verification", True)  # Default to bypassing SSL verification

            if not verify_ssl:
                self.logger.warning("SSL verification is disabled. This should only be used for development.")
                import ssl
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

            # Create the session with the SSL context
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": "DopCast Research Agent/1.0"},
                timeout=aiohttp.ClientTimeout(total=30),
                connector=aiohttp.TCPConnector(ssl=ssl_context)
            )

    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def scrape_sources(self, sources: List[str], sport: str,
                           event_type: str, event_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scrape multiple sources concurrently.

        Args:
            sources: List of source URLs
            sport: Sport type (f1 or motogp)
            event_type: Type of event
            event_id: Specific event identifier

        Returns:
            List of collected data items
        """
        await self.setup()

        tasks = []
        for source in sources:
            tasks.append(self.scrape_source(source, sport, event_type, event_id))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log them
        collected_data = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error scraping {sources[i]}: {str(result)}")
            else:
                collected_data.extend(result)

        return collected_data

    async def scrape_source(self, source_url: str, sport: str,
                          event_type: str, event_id: Optional[str] = None) -> List[Dict[str, Any]]:
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
        try:
            # Ensure session is set up
            await self.setup()

            # Make async HTTP request
            async with self.session.get(source_url) as response:
                if response.status != 200:
                    self.logger.warning(f"Failed to fetch {source_url}: HTTP {response.status}")
                    return []

                html_content = await response.text()

                # Save raw data
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                source_name = source_url.split("//")[1].split("/")[0].replace(".", "_")
                raw_filename = f"{sport}_{source_name}_{timestamp}.html"

                with open(os.path.join(self.data_dir, "raw", raw_filename), "w", encoding="utf-8") as f:
                    f.write(html_content)

                # Parse with BeautifulSoup
                soup = BeautifulSoup(html_content, "html.parser")

                # Extract relevant information based on source and sport
                articles = []
                max_articles = self.config.get("max_articles_per_source", 10)

                # Implement source-specific extraction logic
                if "formula1.com" in source_url:
                    articles.extend(self._extract_formula1_articles(soup, max_articles))
                elif "motogp.com" in source_url:
                    articles.extend(self._extract_motogp_articles(soup, max_articles))
                else:
                    # Generic extraction for other sources
                    articles.extend(self._extract_generic_articles(soup, max_articles))

                # Add metadata to each article
                for article in articles:
                    article.update({
                        "source": source_url,
                        "sport": sport,
                        "collected_at": datetime.now().isoformat()
                    })

                return articles

        except Exception as e:
            self.logger.error(f"Error scraping {source_url}: {str(e)}")
            return []

    def _extract_formula1_articles(self, soup: BeautifulSoup, max_articles: int) -> List[Dict[str, Any]]:
        """Extract articles from Formula 1 website."""
        articles = []

        # Formula1.com specific selectors
        article_elements = soup.select(".f1-article, .f1-latest-listing--grid-item")[:max_articles]

        for element in article_elements:
            title_elem = element.select_one(".f1-article--title, .f1-latest-listing--title")
            summary_elem = element.select_one(".f1-article--summary, .f1-latest-listing--description")
            link_elem = element.select_one("a")
            date_elem = element.select_one(".f1-article--date, .f1-latest-listing--date")

            if title_elem:
                article = {
                    "title": title_elem.text.strip(),
                    "summary": summary_elem.text.strip() if summary_elem else "",
                    "url": link_elem["href"] if link_elem and "href" in link_elem.attrs else "",
                    "published_date": date_elem.text.strip() if date_elem else "",
                }
                articles.append(article)

        return articles

    def _extract_motogp_articles(self, soup: BeautifulSoup, max_articles: int) -> List[Dict[str, Any]]:
        """Extract articles from MotoGP website."""
        articles = []

        # MotoGP.com specific selectors
        article_elements = soup.select(".article-item, .news-item")[:max_articles]

        for element in article_elements:
            title_elem = element.select_one(".article-title, .news-title")
            summary_elem = element.select_one(".article-summary, .news-summary")
            link_elem = element.select_one("a")
            date_elem = element.select_one(".article-date, .news-date")

            if title_elem:
                article = {
                    "title": title_elem.text.strip(),
                    "summary": summary_elem.text.strip() if summary_elem else "",
                    "url": link_elem["href"] if link_elem and "href" in link_elem.attrs else "",
                    "published_date": date_elem.text.strip() if date_elem else "",
                }
                articles.append(article)

        return articles

    def _extract_generic_articles(self, soup: BeautifulSoup, max_articles: int) -> List[Dict[str, Any]]:
        """Extract articles using generic selectors for other websites."""
        articles = []

        # Generic selectors that work on many news sites
        article_elements = soup.select(".article, .news-item, .story, article, .post")[:max_articles]

        if not article_elements:
            # Try more generic selectors if specific ones don't match
            article_elements = soup.select("div.content > div, main > div")[:max_articles]

        for element in article_elements:
            title_elem = element.select_one("h1, h2, h3, .title, .headline")
            summary_elem = element.select_one("p, .summary, .description, .excerpt")
            link_elem = element.select_one("a")
            date_elem = element.select_one(".date, .time, .published, time")

            if title_elem:
                article = {
                    "title": title_elem.text.strip(),
                    "summary": summary_elem.text.strip() if summary_elem else "",
                    "url": link_elem["href"] if link_elem and "href" in link_elem.attrs else "",
                    "published_date": date_elem.text.strip() if date_elem else "",
                }
                articles.append(article)

        return articles

    def get_mock_data(self, sport: str, event_type: str) -> List[Dict[str, Any]]:
        """
        Return mock data for demonstration purposes.

        Args:
            sport: Sport type
            event_type: Type of event

        Returns:
            List of mock article data
        """
        # Create mock articles
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
            # Add more mock articles as needed
        ]

        return mock_data
