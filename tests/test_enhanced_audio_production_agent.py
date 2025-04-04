"""
Test script for the Enhanced Audio Production Agent.
"""

import asyncio
import logging
import os
import sys
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.audio_production import EnhancedAudioProductionAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_enhanced_audio_production_agent():
    """Test the enhanced audio production agent."""
    logger.info("Testing Enhanced Audio Production Agent")
    
    # Create the agent
    agent = EnhancedAudioProductionAgent()
    
    # Create mock audio metadata
    audio_metadata = {
        "title": "F1 Monaco Grand Prix Review",
        "description": "A detailed analysis of the Monaco Grand Prix, including key moments and driver performances.",
        "hosts": ["Mukesh", "Rakesh"],
        "created_at": datetime.now().isoformat(),
        "main_file": "f1_monaco_gp_review_12345678.mp3",
        "segment_files": [
            {
                "filename": "mukesh_12345678_1234.mp3",
                "speaker": "Mukesh",
                "duration": 30.0,
                "emotion": "neutral",
                "path": "/path/to/segments/mukesh_12345678_1234.mp3"
            },
            {
                "filename": "rakesh_12345678_5678.mp3",
                "speaker": "Rakesh",
                "duration": 45.0,
                "emotion": "excited",
                "path": "/path/to/segments/rakesh_12345678_5678.mp3"
            }
        ],
        "total_duration": 75.0
    }
    
    # Test input data
    input_data = {
        "audio_metadata": audio_metadata,
        "custom_parameters": {
            "output_format": "mp3",
            "target_loudness": -16.0,
            "episode_number": 42
        }
    }
    
    # Process the request
    logger.info(f"Processing audio production request for: {audio_metadata['title']}")
    result = await agent.process(input_data)
    
    # Save the result to a file for inspection
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"production_test_result_{timestamp}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Test result saved to {output_file}")
    
    # Print a summary of the result
    logger.info("Result summary:")
    logger.info(f"Title: {result.get('title')}")
    logger.info(f"Production ID: {result.get('production_id')}")
    logger.info(f"File: {result.get('file', {}).get('filename')}")
    logger.info(f"Duration: {result.get('duration')} seconds")
    
    return result

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_enhanced_audio_production_agent())
