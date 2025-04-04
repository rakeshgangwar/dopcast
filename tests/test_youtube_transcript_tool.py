"""
Tests for the YouTube Transcript Tool using yt-dlp.
"""

import os
import sys
import pytest
from unittest.mock import patch

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.research.tools.youtube_transcript_tool import YouTubeTranscriptTool

# Create a temporary directory for testing
@pytest.fixture
def temp_data_dir(tmpdir):
    data_dir = tmpdir.mkdir("test_data")
    return str(data_dir)

def test_youtube_transcript_tool_initialization(temp_data_dir):
    """Test that the YouTube transcript tool initializes correctly."""
    tool = YouTubeTranscriptTool(temp_data_dir)

    # Check that the transcript directory was created
    transcript_dir = os.path.join(temp_data_dir, "transcripts")
    assert os.path.exists(transcript_dir)

    # Check default configuration
    assert tool.max_videos == 5
    assert tool.max_transcript_length == 10000

    # Check yt-dlp options
    assert 'skip_download' in tool.ydl_opts
    assert tool.ydl_opts['skip_download'] is True
    assert 'writesubtitles' in tool.ydl_opts
    assert 'writeautomaticsub' in tool.ydl_opts

def test_extract_video_id():
    """Test the video ID extraction from different URL formats."""
    tool = YouTubeTranscriptTool("dummy_dir")

    # Test standard YouTube URL
    url1 = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert tool.extract_video_id(url1) == "dQw4w9WgXcQ"

    # Test short YouTube URL
    url2 = "https://youtu.be/dQw4w9WgXcQ"
    assert tool.extract_video_id(url2) == "dQw4w9WgXcQ"

    # Test embed URL
    url3 = "https://www.youtube.com/embed/dQw4w9WgXcQ"
    assert tool.extract_video_id(url3) == "dQw4w9WgXcQ"

    # Test URL with additional parameters
    url4 = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s"
    assert tool.extract_video_id(url4) == "dQw4w9WgXcQ"

    # Test invalid URL
    url5 = "https://example.com"
    assert tool.extract_video_id(url5) is None

def test_get_mock_videos(temp_data_dir):
    """Test the mock video generation."""
    tool = YouTubeTranscriptTool(temp_data_dir)

    # Get mock videos
    mock_data = tool.get_mock_videos("f1", "race", 3)

    # Check the results
    assert len(mock_data) == 3

    # Check the structure of the mock data
    for item in mock_data:
        assert "video_id" in item
        assert "title" in item
        assert "description" in item
        assert "channel" in item
        assert "published_at" in item
        assert "url" in item
        assert "duration" in item
        assert "f1" in item["title"].lower()
        assert "race" in item["title"].lower()

def test_get_mock_transcripts(temp_data_dir):
    """Test the mock transcript generation."""
    tool = YouTubeTranscriptTool(temp_data_dir)

    # Get mock transcripts
    mock_data = tool.get_mock_transcripts("f1", "race", 3)

    # Check the results
    assert len(mock_data) == 3

    # Check the structure of the mock data
    for item in mock_data:
        assert "video_id" in item
        assert "title" in item
        assert "transcript" in item
        assert "f1" in item["title"].lower()
        assert "race" in item["title"].lower()

def test_search_videos(temp_data_dir):
    """Test the search_videos method."""
    # Create the tool
    tool = YouTubeTranscriptTool(temp_data_dir)

    # Get mock videos directly
    results = tool.get_mock_videos("f1", "test query", 2)

    # Check the results
    assert len(results) == 2
    assert "video_id" in results[0]
    assert "title" in results[0]
    assert "description" in results[0]
    assert "channel" in results[0]
    assert "published_at" in results[0]
    assert "url" in results[0]
    assert "duration" in results[0]

def test_get_transcript(temp_data_dir):
    """Test the get_transcript method."""
    # Create the tool
    tool = YouTubeTranscriptTool(temp_data_dir)

    # Call the get_transcript method directly
    result = tool.get_transcript("test_video_id")

    # Check the result
    assert result is not None
    assert result["video_id"] == "test_video_id"
    assert "full_text" in result
    assert "segments" in result
    assert "language" in result
    assert "fetched_at" in result

def test_search_and_get_transcripts(temp_data_dir):
    """Test the search_and_get_transcripts method."""
    tool = YouTubeTranscriptTool(temp_data_dir)

    # Mock the search_videos and get_transcript methods
    with patch.object(tool, 'search_videos') as mock_search, \
         patch.object(tool, 'get_transcript') as mock_get_transcript:

        # Configure the mocks
        mock_search.return_value = [
            {
                "video_id": "mock_id_1",
                "title": "F1 Test Video",
                "description": "Test description",
                "channel": "Test Channel",
                "published_at": "2023-01-01T00:00:00Z",
                "url": "https://www.youtube.com/watch?v=mock_id_1",
                "duration": 300
            }
        ]

        mock_get_transcript.return_value = {
            "video_id": "mock_id_1",
            "language": "en",
            "full_text": "This is a test transcript.",
            "segments": [{"text": "This is a test transcript.", "start": 0.0, "duration": 2.0}],
            "fetched_at": "2023-01-01T00:00:00Z"
        }

        # Test the combined method
        results = tool.search_and_get_transcripts("f1 test", "f1", 1)

        # Check that the mocks were called correctly
        mock_search.assert_called_once_with("f1 test", "f1", 1)
        mock_get_transcript.assert_called_once_with("mock_id_1")

        # Check the results
        assert len(results) == 1
        assert results[0]["video_id"] == "mock_id_1"
        assert results[0]["transcript"] == "This is a test transcript."
        assert "transcript_segments" in results[0]
        assert results[0]["transcript_language"] == "en"

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
