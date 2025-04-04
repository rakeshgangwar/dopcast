"""
Data processor tool for the Research Agent.
Provides enhanced data processing capabilities with structured output.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd
import json
import os

class DataProcessorTool:
    """
    Enhanced data processor tool with structured output support.
    """

    def __init__(self, data_dir: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the data processor tool.

        Args:
            data_dir: Directory to store processed data
            config: Configuration parameters
        """
        self.logger = logging.getLogger("dopcast.research.data_processor")
        self.data_dir = data_dir
        self.config = config or {}

        # Ensure processed data directory exists
        os.makedirs(os.path.join(self.data_dir, "processed"), exist_ok=True)

    def process_data(self, collected_data: List[Dict[str, Any]], sport: str, event_type: str, event_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process and structure the collected data.

        Args:
            collected_data: Raw collected data
            sport: Sport type
            event_type: Type of event
            event_id: Specific event identifier (e.g., australian_gp_2024)

        Returns:
            Processed and structured data
        """
        self.logger.info(f"Processing {len(collected_data)} articles for {sport} {event_type}")

        # Convert to DataFrame for easier processing
        df = pd.DataFrame(collected_data)

        # Filter by event_id if provided
        if event_id and not df.empty:
            self.logger.info(f"Filtering content for event ID: {event_id}")
            df = self._filter_by_event_id(df, event_id)

        # Deduplicate articles based on title similarity
        if not df.empty and 'title' in df.columns:
            df = self._deduplicate_articles(df)

        # Process the data
        processed = {
            "sport": sport,
            "event_type": event_type,
            "processed_at": datetime.now().isoformat(),
            "article_count": len(df),
            "articles": df.to_dict('records') if not df.empty else [],
            "metadata": {
                "sources": df['source'].unique().tolist() if not df.empty and 'source' in df.columns else [],
                "date_range": self._get_date_range(df) if not df.empty and 'published_date' in df.columns else {},
                "processing_version": "2.0"
            }
        }

        # Add event-specific data if available
        if event_type == "race" and not df.empty:
            processed["race_data"] = self._extract_race_data(df, sport)

        # Save processed data to disk
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{sport}_{event_type}_{timestamp}.json"
        filepath = os.path.join(self.data_dir, "processed", filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(processed, f, indent=2)

        self.logger.info(f"Saved processed data to {filepath}")

        return processed

    def _deduplicate_articles(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Deduplicate articles based on title similarity.

        Args:
            df: DataFrame of articles

        Returns:
            Deduplicated DataFrame
        """
        # Simple deduplication based on exact title match
        df = df.drop_duplicates(subset=['title'])

        # More sophisticated deduplication could use text similarity metrics
        # For example, using fuzzy matching or embeddings

        return df

    def _filter_by_event_id(self, df: pd.DataFrame, event_id: str) -> pd.DataFrame:
        """
        Filter content by event ID.

        Args:
            df: DataFrame of articles
            event_id: Event identifier (e.g., australian_gp_2024)

        Returns:
            Filtered DataFrame
        """
        # Extract year from event_id if it contains a year
        year = None
        if '_' in event_id:
            parts = event_id.split('_')
            for part in parts:
                if part.isdigit() and len(part) == 4:
                    year = int(part)
                    break

        # If no year found, try to extract from the last 4 characters
        if not year and len(event_id) >= 4 and event_id[-4:].isdigit():
            year = int(event_id[-4:])

        # Extract event name (remove year and common separators)
        event_name = event_id.lower()
        if year:
            event_name = event_name.replace(str(year), '').strip('_-')

        # Clean up event name
        event_name = event_name.replace('_', ' ').replace('-', ' ').strip()

        self.logger.info(f"Filtering for event: {event_name}, year: {year}")

        # Filter by content
        filtered_df = df.copy()

        # Filter by year in published_date if available
        if year and 'published_date' in filtered_df.columns:
            try:
                # Convert to datetime if not already
                filtered_df['published_date'] = pd.to_datetime(filtered_df['published_date'], errors='coerce')

                # Filter by year
                year_mask = filtered_df['published_date'].dt.year == year
                if year_mask.any():
                    filtered_df = filtered_df[year_mask]
                    self.logger.info(f"Filtered {len(filtered_df)} articles by year {year}")
            except Exception as e:
                self.logger.warning(f"Error filtering by date: {e}")

        # Filter by event name in title or content
        if event_name:
            # Check title
            if 'title' in filtered_df.columns:
                title_mask = filtered_df['title'].str.lower().str.contains(event_name, na=False)
                if title_mask.any():
                    filtered_df = filtered_df[title_mask]
                    self.logger.info(f"Filtered {len(filtered_df)} articles by title containing '{event_name}'")

            # If no matches in title, check content
            if len(filtered_df) == 0 and 'content' in filtered_df.columns:
                content_mask = filtered_df['content'].str.lower().str.contains(event_name, na=False)
                if content_mask.any():
                    filtered_df = filtered_df[content_mask]
                    self.logger.info(f"Filtered {len(filtered_df)} articles by content containing '{event_name}'")

        # If no matches, return original dataframe with a warning
        if len(filtered_df) == 0:
            self.logger.warning(f"No articles matched event ID {event_id}, using all collected data")
            return df

        return filtered_df

    def _get_date_range(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Get the date range of the articles.

        Args:
            df: DataFrame of articles

        Returns:
            Dictionary with earliest and latest dates
        """
        try:
            # Try to parse dates
            dates = pd.to_datetime(df['published_date'], errors='coerce')
            valid_dates = dates.dropna()

            if len(valid_dates) > 0:
                return {
                    "earliest": valid_dates.min().isoformat(),
                    "latest": valid_dates.max().isoformat()
                }
        except Exception as e:
            self.logger.warning(f"Error parsing dates: {e}")

        return {}

    def _extract_race_data(self, df: pd.DataFrame, sport: str) -> Dict[str, Any]:
        """
        Extract structured race data from articles.

        Args:
            df: DataFrame of articles
            sport: Sport type

        Returns:
            Structured race data
        """
        race_data = {
            "results": [],
            "fastest_lap": None,
            "pole_position": None,
            "championship_impact": {}
        }

        # In a real implementation, this would parse race results tables,
        # extract structured data about positions, times, points, etc.

        # For F1, we could use the fastf1 package to get official results
        if sport == "f1" and self.config.get("use_fastf1", False):
            try:
                import fastf1
                # Implementation would go here
                pass
            except ImportError:
                self.logger.warning("fastf1 package not available for F1 data extraction")

        return race_data
