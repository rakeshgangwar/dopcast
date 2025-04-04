"""
Enhanced YouTube Transcript tool for the Research Agent.
Provides improved transcript extraction and summarization capabilities.
"""

import logging
import os
import re
import json
import tempfile
from typing import Dict, Any, List, Optional
from datetime import datetime
import yt_dlp as yt_dlp
import asyncio

class EnhancedYouTubeTranscriptTool:
    """
    Enhanced tool for extracting and summarizing YouTube video transcripts.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the enhanced YouTube transcript tool.

        Args:
            config: Configuration parameters
        """
        self.logger = logging.getLogger("dopcast.research.enhanced_youtube_transcript")
        self.config = config or {}
        
        # Set default configuration
        self.max_videos = self.config.get("max_videos", 5)
        self.use_whisper = self.config.get("use_whisper", False)
        self.whisper_model = self.config.get("whisper_model", "base")
        
        # Set up results directory
        self.transcripts_dir = os.path.join("output", "research", "youtube_transcripts")
        os.makedirs(self.transcripts_dir, exist_ok=True)
        
        # Set up summaries directory
        self.summaries_dir = os.path.join("output", "research", "summaries")
        os.makedirs(self.summaries_dir, exist_ok=True)
        
        # Configure yt-dlp options
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
        }
        
        self.logger.info("Enhanced YouTube Transcript Tool initialized")

    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract the video ID from a YouTube URL.

        Args:
            url: YouTube URL

        Returns:
            Video ID or None if not found
        """
        # Match patterns like youtube.com/watch?v=VIDEO_ID or youtu.be/VIDEO_ID
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/v/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None

    async def search_and_extract_transcripts(self, query: str, sport: str, 
                                      max_videos: Optional[int] = None) -> Dict[str, Any]:
        """
        Search for YouTube videos and extract their transcripts.

        Args:
            query: Search query
            sport: Sport type for context
            max_videos: Maximum number of videos to process

        Returns:
            Dictionary with transcripts and summary
        """
        # Set max videos
        if max_videos is None:
            max_videos = self.max_videos
        
        # Enhance query with sport context
        enhanced_query = f"{sport} {query}"
        
        self.logger.info(f"Searching YouTube for: {enhanced_query}")
        
        # Search for videos
        videos = await self._search_videos(enhanced_query, max_videos)
        
        # Extract transcripts
        transcripts = []
        for video in videos:
            transcript = await self._extract_transcript(video)
            if transcript:
                transcripts.append(transcript)
        
        # Generate a timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save transcripts to file
        filename = f"youtube_transcripts_{sport}_{timestamp}.json"
        filepath = os.path.join(self.transcripts_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(transcripts, f, ensure_ascii=False, indent=2)
        
        # Create a summary of the transcripts
        summary = self._create_transcript_summary(transcripts, query, sport)
        
        # Save summary to file
        summary_filename = f"youtube_summary_{sport}_{timestamp}.md"
        summary_filepath = os.path.join(self.summaries_dir, summary_filename)
        
        with open(summary_filepath, "w", encoding="utf-8") as f:
            f.write(summary)
        
        self.logger.info(f"Extracted {len(transcripts)} transcripts for: {enhanced_query}")
        
        return {
            "transcripts": transcripts,
            "summary": summary,
            "transcripts_file": filepath,
            "summary_file": summary_filepath,
            "video_count": len(videos)
        }

    async def _search_videos(self, query: str, max_videos: int) -> List[Dict[str, Any]]:
        """
        Search for YouTube videos using yt-dlp.

        Args:
            query: Search query
            max_videos: Maximum number of videos to return

        Returns:
            List of video information
        """
        search_opts = {
            **self.ydl_opts,
            'format': 'best',
            'noplaylist': True,
            'extract_flat': True,
            'skip_download': True,
            'default_search': 'ytsearch',
            'max_downloads': max_videos
        }
        
        search_query = f"ytsearch{max_videos}:{query}"
        
        try:
            with yt_dlp.YoutubeDL(search_opts) as ydl:
                search_results = ydl.extract_info(search_query, download=False)
                
                if not search_results or 'entries' not in search_results:
                    self.logger.warning(f"No videos found for query: {query}")
                    return []
                
                videos = []
                for entry in search_results['entries']:
                    if entry:
                        video = {
                            "id": entry.get('id'),
                            "title": entry.get('title'),
                            "url": entry.get('url'),
                            "uploader": entry.get('uploader'),
                            "duration": entry.get('duration'),
                            "view_count": entry.get('view_count'),
                            "upload_date": entry.get('upload_date')
                        }
                        videos.append(video)
                
                return videos
        
        except Exception as e:
            self.logger.error(f"Error searching YouTube videos: {str(e)}")
            return []

    async def _extract_transcript(self, video: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract transcript for a YouTube video.

        Args:
            video: Video information

        Returns:
            Dictionary with transcript data or None if not available
        """
        video_id = video.get('id')
        if not video_id:
            self.logger.warning("No video ID provided")
            return None
        
        self.logger.info(f"Extracting transcript for video: {video.get('title', video_id)}")
        
        # Try to get transcript using yt-dlp
        transcript_data = await self._get_transcript_with_ytdlp(video_id)
        
        if transcript_data:
            # Add video metadata
            transcript_data.update({
                "video_title": video.get('title'),
                "video_url": f"https://www.youtube.com/watch?v={video_id}",
                "video_uploader": video.get('uploader'),
                "video_duration": video.get('duration'),
                "video_view_count": video.get('view_count'),
                "video_upload_date": video.get('upload_date')
            })
            
            return transcript_data
        
        return None

    async def _get_transcript_with_ytdlp(self, video_id: str, languages: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get the transcript for a YouTube video using yt-dlp.

        Args:
            video_id: YouTube video ID
            languages: List of language codes to try, in order of preference

        Returns:
            Dictionary with transcript data or None if not available
        """
        # Default to English if no languages specified
        if not languages:
            languages = ['en', 'en-US', 'en-GB']
        
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Configure yt-dlp options for transcript extraction
        transcript_opts = {
            **self.ydl_opts,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': languages,
            'skip_download': True,
            'subtitlesformat': 'json3',
        }
        
        try:
            # Use yt-dlp to extract subtitles
            with tempfile.TemporaryDirectory() as temp_dir:
                # Set the output directory to the temporary directory
                transcript_opts['paths'] = {'home': temp_dir}
                
                with yt_dlp.YoutubeDL(transcript_opts) as ydl:
                    # Extract video info including subtitles
                    info = ydl.extract_info(video_url, download=False)
                    
                    if not info:
                        self.logger.warning(f"Could not extract info for video ID: {video_id}")
                        return None
                    
                    # Check if subtitles are available
                    subtitles = info.get('subtitles', {})
                    auto_subtitles = info.get('automatic_captions', {})
                    
                    # Try to find subtitles in preferred languages
                    transcript_data = None
                    transcript_lang = None
                    
                    # First check manual subtitles
                    for lang in languages:
                        if lang in subtitles and subtitles[lang]:
                            transcript_lang = lang
                            # Download the subtitle file
                            ydl.params['writesubtitles'] = True
                            ydl.params['writeautomaticsub'] = False
                            ydl.params['subtitleslangs'] = [lang]
                            ydl.download([video_url])
                            break
                    
                    # If no manual subtitles, check automatic captions
                    if not transcript_lang:
                        for lang in languages:
                            if lang in auto_subtitles and auto_subtitles[lang]:
                                transcript_lang = lang
                                # Download the automatic caption file
                                ydl.params['writesubtitles'] = False
                                ydl.params['writeautomaticsub'] = True
                                ydl.params['subtitleslangs'] = [lang]
                                ydl.download([video_url])
                                break
                    
                    # If subtitles were found, process them
                    if transcript_lang:
                        # Look for the subtitle file in the temp directory
                        for file in os.listdir(temp_dir):
                            if file.endswith(f'.{transcript_lang}.json3'):
                                subtitle_path = os.path.join(temp_dir, file)
                                with open(subtitle_path, 'r', encoding='utf-8') as f:
                                    subtitle_data = json.load(f)
                                
                                # Extract text from subtitle data
                                transcript_text = self._extract_text_from_json3(subtitle_data)
                                
                                return {
                                    "video_id": video_id,
                                    "language": transcript_lang,
                                    "transcript": transcript_text,
                                    "is_auto_generated": transcript_lang in auto_subtitles,
                                    "extracted_at": datetime.now().isoformat()
                                }
                    
                    # If no subtitles were found but we have a description, use that
                    if info.get('description'):
                        self.logger.info(f"No transcript found, using video description for {video_id}")
                        return {
                            "video_id": video_id,
                            "language": "unknown",
                            "transcript": info.get('description'),
                            "is_auto_generated": False,
                            "is_description": True,
                            "extracted_at": datetime.now().isoformat()
                        }
            
            self.logger.warning(f"No transcript found for video ID: {video_id}")
            return None
        
        except Exception as e:
            self.logger.error(f"Error fetching transcript with yt-dlp: {str(e)}")
            return None

    def _extract_text_from_json3(self, subtitle_data: Dict[str, Any]) -> str:
        """
        Extract text from JSON3 subtitle data.

        Args:
            subtitle_data: JSON3 subtitle data

        Returns:
            Extracted transcript text
        """
        transcript_text = ""
        
        try:
            events = subtitle_data.get('events', [])
            
            for event in events:
                if 'segs' in event:
                    for seg in event['segs']:
                        if 'utf8' in seg:
                            transcript_text += seg['utf8'] + " "
            
            return transcript_text.strip()
        
        except Exception as e:
            self.logger.error(f"Error extracting text from JSON3: {str(e)}")
            return ""

    def _create_transcript_summary(self, transcripts: List[Dict[str, Any]], 
                                 query: str, sport: str) -> str:
        """
        Create a summary of the transcripts.

        Args:
            transcripts: List of transcripts
            query: Search query
            sport: Sport type

        Returns:
            Markdown summary of the transcripts
        """
        # Create a title for the summary
        title = f"# YouTube Transcript Summary: {sport.upper()} {query}\n\n"
        
        # Add metadata
        metadata = f"**Search Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        metadata += f"**Videos Processed:** {len(transcripts)}\n\n"
        
        # Add a table of contents
        toc = "## Table of Contents\n\n"
        for i, transcript in enumerate(transcripts):
            video_title = transcript.get('video_title', f"Video {i+1}")
            toc += f"{i+1}. [{video_title}](#{i+1})\n"
        
        # Add the transcripts
        content = "\n\n## Transcripts\n\n"
        for i, transcript in enumerate(transcripts):
            video_title = transcript.get('video_title', f"Video {i+1}")
            video_url = transcript.get('video_url', 'N/A')
            video_uploader = transcript.get('video_uploader', 'Unknown')
            video_duration = transcript.get('video_duration', 'Unknown')
            is_auto_generated = transcript.get('is_auto_generated', False)
            is_description = transcript.get('is_description', False)
            
            content += f"### {i+1}. {video_title}\n\n"
            content += f"**URL:** {video_url}\n\n"
            content += f"**Uploader:** {video_uploader}\n\n"
            content += f"**Duration:** {video_duration} seconds\n\n"
            
            if is_description:
                content += "**Note:** This is the video description, not a transcript.\n\n"
            else:
                content += f"**Auto-generated:** {'Yes' if is_auto_generated else 'No'}\n\n"
            
            content += "**Content:**\n\n"
            
            # Limit transcript length for readability
            transcript_text = transcript.get('transcript', 'No transcript available.')
            if len(transcript_text) > 1000:
                content += f"```\n{transcript_text[:1000]}...\n```\n\n"
                content += f"*Transcript truncated. Full length: {len(transcript_text)} characters.*\n\n"
            else:
                content += f"```\n{transcript_text}\n```\n\n"
            
            content += "---\n\n"
        
        # Combine all sections
        summary = f"{title}{metadata}{toc}{content}"
        
        return summary
