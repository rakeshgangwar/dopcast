"""
Research Summarizer tool for the Research Agent.
Provides comprehensive summarization of all research data.
"""

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import asyncio

class ResearchSummarizerTool:
    """
    Tool for summarizing and organizing all research data.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the research summarizer tool.

        Args:
            config: Configuration parameters
        """
        self.logger = logging.getLogger("dopcast.research.summarizer")
        self.config = config or {}
        
        # Set up summaries directory
        self.summaries_dir = os.path.join("output", "research", "summaries")
        os.makedirs(self.summaries_dir, exist_ok=True)
        
        self.logger.info("Research Summarizer Tool initialized")

    async def create_comprehensive_summary(self, 
                                    exa_results: Dict[str, Any],
                                    youtube_results: Dict[str, Any],
                                    firecrawl_results: Dict[str, Any],
                                    topic: str,
                                    sport: str,
                                    event_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a comprehensive summary of all research data.

        Args:
            exa_results: Results from Exa search
            youtube_results: Results from YouTube transcript extraction
            firecrawl_results: Results from Firecrawl
            topic: Research topic
            sport: Sport type
            event_type: Type of event

        Returns:
            Dictionary with comprehensive summary
        """
        self.logger.info(f"Creating comprehensive research summary for {sport} {topic}")
        
        # Generate a timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create the comprehensive summary
        summary = self._create_summary(
            exa_results, youtube_results, firecrawl_results,
            topic, sport, event_type
        )
        
        # Save summary to file
        summary_filename = f"comprehensive_summary_{sport}_{timestamp}.md"
        summary_filepath = os.path.join(self.summaries_dir, summary_filename)
        
        with open(summary_filepath, "w", encoding="utf-8") as f:
            f.write(summary)
        
        # Create a PDF version of the summary
        pdf_filepath = self._create_pdf_summary(summary, summary_filepath)
        
        # Create a JSON version with key findings
        key_findings = self._extract_key_findings(
            exa_results, youtube_results, firecrawl_results,
            topic, sport, event_type
        )
        
        json_filename = f"research_findings_{sport}_{timestamp}.json"
        json_filepath = os.path.join(self.summaries_dir, json_filename)
        
        with open(json_filepath, "w", encoding="utf-8") as f:
            json.dump(key_findings, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Created comprehensive research summary at {summary_filepath}")
        
        return {
            "summary": summary,
            "summary_file": summary_filepath,
            "pdf_file": pdf_filepath,
            "json_file": json_filepath,
            "key_findings": key_findings
        }

    def _create_summary(self, 
                      exa_results: Dict[str, Any],
                      youtube_results: Dict[str, Any],
                      firecrawl_results: Dict[str, Any],
                      topic: str,
                      sport: str,
                      event_type: Optional[str] = None) -> str:
        """
        Create a comprehensive markdown summary of all research data.

        Args:
            exa_results: Results from Exa search
            youtube_results: Results from YouTube transcript extraction
            firecrawl_results: Results from Firecrawl
            topic: Research topic
            sport: Sport type
            event_type: Type of event

        Returns:
            Markdown summary
        """
        # Create a title for the summary
        title = f"# Comprehensive Research Summary: {sport.upper()} {topic}"
        if event_type:
            title += f" {event_type}"
        
        # Add metadata
        metadata = f"\n\n**Research Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        metadata += f"**Sport:** {sport.upper()}\n"
        if event_type:
            metadata += f"**Event Type:** {event_type}\n"
        metadata += f"**Topic:** {topic}\n\n"
        
        # Add research statistics
        stats = "## Research Statistics\n\n"
        stats += "| Source | Items | Details |\n"
        stats += "|--------|-------|--------|\n"
        
        exa_count = len(exa_results.get("results", []))
        youtube_count = len(youtube_results.get("transcripts", []))
        firecrawl_count = len(firecrawl_results.get("results", []))
        
        stats += f"| Exa Search | {exa_count} | {exa_results.get('query_count', 0)} queries |\n"
        stats += f"| YouTube Transcripts | {youtube_count} | {youtube_results.get('video_count', 0)} videos |\n"
        stats += f"| Firecrawl | {firecrawl_count} | {firecrawl_results.get('url_count', 0)} URLs |\n"
        stats += f"| **Total** | **{exa_count + youtube_count + firecrawl_count}** | |\n\n"
        
        # Add executive summary
        exec_summary = "## Executive Summary\n\n"
        exec_summary += "This research summary combines information from web searches, YouTube video transcripts, "
        exec_summary += f"and targeted web crawling to provide a comprehensive overview of {sport.upper()} {topic}.\n\n"
        
        # Add key findings
        key_findings = "## Key Findings\n\n"
        
        # Add findings from Exa search
        if exa_count > 0:
            key_findings += "### From Web Search\n\n"
            for i, result in enumerate(exa_results.get("results", [])[:5]):  # Limit to top 5
                title = result.get("title", f"Result {i+1}")
                summary = result.get("summary", "No summary available.")
                key_findings += f"- **{title}**: {summary}\n"
            key_findings += "\n"
        
        # Add findings from YouTube transcripts
        if youtube_count > 0:
            key_findings += "### From YouTube Videos\n\n"
            for i, transcript in enumerate(youtube_results.get("transcripts", [])[:3]):  # Limit to top 3
                video_title = transcript.get("video_title", f"Video {i+1}")
                transcript_text = transcript.get("transcript", "No transcript available.")
                # Extract a short excerpt
                excerpt = transcript_text[:200] + "..." if len(transcript_text) > 200 else transcript_text
                key_findings += f"- **{video_title}**: {excerpt}\n"
            key_findings += "\n"
        
        # Add findings from Firecrawl
        if firecrawl_count > 0:
            key_findings += "### From Web Articles\n\n"
            for i, result in enumerate(firecrawl_results.get("results", [])[:3]):  # Limit to top 3
                title = result.get("title", f"Article {i+1}")
                content = result.get("content", "No content available.")
                # Extract a short excerpt
                excerpt = content[:200] + "..." if len(content) > 200 else content
                key_findings += f"- **{title}**: {excerpt}\n"
            key_findings += "\n"
        
        # Add detailed sections
        detailed = "## Detailed Research\n\n"
        
        # Add Exa search details
        if exa_count > 0:
            detailed += "### Web Search Results\n\n"
            for i, result in enumerate(exa_results.get("results", [])[:10]):  # Limit to top 10
                title = result.get("title", f"Result {i+1}")
                url = result.get("url", "N/A")
                summary = result.get("summary", "No summary available.")
                detailed += f"#### {i+1}. {title}\n\n"
                detailed += f"**URL:** {url}\n\n"
                detailed += f"**Summary:** {summary}\n\n"
                detailed += "---\n\n"
        
        # Add YouTube transcript details
        if youtube_count > 0:
            detailed += "### YouTube Video Transcripts\n\n"
            for i, transcript in enumerate(youtube_results.get("transcripts", [])[:5]):  # Limit to top 5
                video_title = transcript.get("video_title", f"Video {i+1}")
                video_url = transcript.get("video_url", "N/A")
                video_uploader = transcript.get("video_uploader", "Unknown")
                detailed += f"#### {i+1}. {video_title}\n\n"
                detailed += f"**URL:** {video_url}\n\n"
                detailed += f"**Uploader:** {video_uploader}\n\n"
                detailed += "**Transcript Excerpt:**\n\n"
                
                # Limit transcript length for readability
                transcript_text = transcript.get("transcript", "No transcript available.")
                if len(transcript_text) > 500:
                    detailed += f"```\n{transcript_text[:500]}...\n```\n\n"
                    detailed += f"*Transcript truncated. Full length: {len(transcript_text)} characters.*\n\n"
                else:
                    detailed += f"```\n{transcript_text}\n```\n\n"
                
                detailed += "---\n\n"
        
        # Add Firecrawl details
        if firecrawl_count > 0:
            detailed += "### Web Article Content\n\n"
            for i, result in enumerate(firecrawl_results.get("results", [])[:5]):  # Limit to top 5
                title = result.get("title", f"Article {i+1}")
                url = result.get("url", "N/A")
                source = result.get("metadata", {}).get("source", "Unknown")
                detailed += f"#### {i+1}. {title}\n\n"
                detailed += f"**URL:** {url}\n\n"
                detailed += f"**Source:** {source}\n\n"
                detailed += "**Content Excerpt:**\n\n"
                
                # Limit content length for readability
                content = result.get("content", "No content available.")
                if len(content) > 500:
                    detailed += f"```\n{content[:500]}...\n```\n\n"
                    detailed += f"*Content truncated. Full length: {len(content)} characters.*\n\n"
                else:
                    detailed += f"```\n{content}\n```\n\n"
                
                detailed += "---\n\n"
        
        # Add conclusion
        conclusion = "## Conclusion\n\n"
        conclusion += f"This comprehensive research on {sport.upper()} {topic} combines information from "
        conclusion += f"{exa_count} web search results, {youtube_count} YouTube video transcripts, and "
        conclusion += f"{firecrawl_count} web articles. The research provides a solid foundation for "
        conclusion += "creating an informative and engaging podcast episode.\n\n"
        
        # Combine all sections
        summary = f"{title}{metadata}{stats}{exec_summary}{key_findings}{detailed}{conclusion}"
        
        return summary

    def _create_pdf_summary(self, markdown_summary: str, markdown_path: str) -> str:
        """
        Create a PDF version of the summary.

        Args:
            markdown_summary: Markdown summary
            markdown_path: Path to the markdown file

        Returns:
            Path to the PDF file
        """
        # Replace .md with .pdf
        pdf_path = markdown_path.replace(".md", ".pdf")
        
        try:
            # Try to use a markdown to PDF converter
            # This is a placeholder - in a real implementation, you would use a library like WeasyPrint or Pandoc
            self.logger.info(f"PDF generation would save to {pdf_path}")
            
            # For now, just create a simple text file as a placeholder
            with open(pdf_path, "w", encoding="utf-8") as f:
                f.write("PDF version of the research summary would be generated here.\n")
                f.write("This is a placeholder file.\n")
            
            return pdf_path
        
        except Exception as e:
            self.logger.error(f"Error creating PDF summary: {str(e)}")
            return "PDF generation failed"

    def _extract_key_findings(self, 
                            exa_results: Dict[str, Any],
                            youtube_results: Dict[str, Any],
                            firecrawl_results: Dict[str, Any],
                            topic: str,
                            sport: str,
                            event_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract key findings from all research data.

        Args:
            exa_results: Results from Exa search
            youtube_results: Results from YouTube transcript extraction
            firecrawl_results: Results from Firecrawl
            topic: Research topic
            sport: Sport type
            event_type: Type of event

        Returns:
            Dictionary with key findings
        """
        # Create a dictionary for key findings
        key_findings = {
            "topic": topic,
            "sport": sport,
            "event_type": event_type,
            "research_date": datetime.now().isoformat(),
            "sources": {
                "web_search": {
                    "count": len(exa_results.get("results", [])),
                    "query_count": exa_results.get("query_count", 0)
                },
                "youtube": {
                    "count": len(youtube_results.get("transcripts", [])),
                    "video_count": youtube_results.get("video_count", 0)
                },
                "web_articles": {
                    "count": len(firecrawl_results.get("results", [])),
                    "url_count": firecrawl_results.get("url_count", 0)
                }
            },
            "findings": {
                "web_search": [],
                "youtube": [],
                "web_articles": []
            }
        }
        
        # Add findings from Exa search
        for i, result in enumerate(exa_results.get("results", [])[:10]):  # Limit to top 10
            key_findings["findings"]["web_search"].append({
                "title": result.get("title", f"Result {i+1}"),
                "url": result.get("url", "N/A"),
                "summary": result.get("summary", "No summary available."),
                "source": result.get("metadata", {}).get("source", "Unknown"),
                "published_date": result.get("metadata", {}).get("published_date", "Unknown")
            })
        
        # Add findings from YouTube transcripts
        for i, transcript in enumerate(youtube_results.get("transcripts", [])[:5]):  # Limit to top 5
            # Extract a short excerpt
            transcript_text = transcript.get("transcript", "No transcript available.")
            excerpt = transcript_text[:300] + "..." if len(transcript_text) > 300 else transcript_text
            
            key_findings["findings"]["youtube"].append({
                "title": transcript.get("video_title", f"Video {i+1}"),
                "url": transcript.get("video_url", "N/A"),
                "uploader": transcript.get("video_uploader", "Unknown"),
                "duration": transcript.get("video_duration", "Unknown"),
                "excerpt": excerpt
            })
        
        # Add findings from Firecrawl
        for i, result in enumerate(firecrawl_results.get("results", [])[:5]):  # Limit to top 5
            # Extract a short excerpt
            content = result.get("content", "No content available.")
            excerpt = content[:300] + "..." if len(content) > 300 else content
            
            key_findings["findings"]["web_articles"].append({
                "title": result.get("title", f"Article {i+1}"),
                "url": result.get("url", "N/A"),
                "source": result.get("metadata", {}).get("source", "Unknown"),
                "excerpt": excerpt
            })
        
        return key_findings
