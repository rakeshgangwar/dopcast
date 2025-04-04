#!/usr/bin/env python3
"""
Test script for the voice synthesis agent.
"""

import asyncio
import json
import os
import logging
from agents.voice_synthesis.enhanced_voice_synthesis_agent import EnhancedVoiceSynthesisAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_voice_synthesis")

# Sample script data
SAMPLE_SCRIPT = {
    "title": "Test Podcast Episode",
    "description": "A test episode to verify voice synthesis",
    "hosts": ["Host 1", "Host 2"],
    "sections": [
        {
            "name": "Introduction",
            "dialogue": [
                {"speaker": "Host 1", "text": "Welcome to our test podcast episode."},
                {"speaker": "Host 2", "text": "Today we're testing the voice synthesis agent."},
                {"speaker": "Host 1", "text": "Let's see if it can generate audio for all segments."}
            ],
            "sound_effects": [
                {"type": "transition", "description": "Short transition sound"}
            ]
        },
        {
            "name": "Main Content",
            "dialogue": [
                {"speaker": "Host 2", "text": "This is the main content section of our podcast."},
                {"speaker": "Host 1", "text": "We're testing if the voice synthesis agent can handle multiple sections."},
                {"speaker": "Host 2", "text": "And if it can generate audio for different speakers."}
            ]
        }
    ]
}

async def test_voice_synthesis():
    """
    Test the voice synthesis agent.
    """
    logger.info("Creating voice synthesis agent")
    agent = EnhancedVoiceSynthesisAgent()
    
    # Ensure output directories exist
    os.makedirs("output/audio/segments", exist_ok=True)
    
    # Prepare input data
    input_data = {
        "script": SAMPLE_SCRIPT,
        "custom_parameters": {
            "audio_format": "mp3",
            "use_ssml": False,
            "provider": "elevenlabs",  # Try with ElevenLabs first
            "default_intro_voice_id": "pNInz6obpgDQGcFmaJgB"  # Use a known voice ID
        }
    }
    
    logger.info("Processing voice synthesis request")
    result = await agent.process(input_data)
    
    # Print the result
    logger.info(f"Voice synthesis result: {json.dumps(result, indent=2)}")
    
    # Check if audio files were generated
    if "main_file" in result:
        main_file_path = os.path.join("output/audio", result["main_file"])
        if os.path.exists(main_file_path):
            logger.info(f"Main audio file generated: {main_file_path} (size: {os.path.getsize(main_file_path)} bytes)")
        else:
            logger.error(f"Main audio file not found: {main_file_path}")
    
    # Check segment files
    if "segment_files" in result:
        for segment in result["segment_files"]:
            segment_path = segment.get("path", "")
            if os.path.exists(segment_path):
                logger.info(f"Segment file generated: {segment_path} (size: {os.path.getsize(segment_path)} bytes)")
            else:
                logger.error(f"Segment file not found: {segment_path}")
    
    return result

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_voice_synthesis())
