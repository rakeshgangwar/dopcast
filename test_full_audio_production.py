#!/usr/bin/env python3
"""
Full test for the enhanced audio production agent with FFmpeg support.
This script tests the complete audio production workflow using the EnhancedAudioProductionAgent.
"""

import os
import logging
import asyncio
from typing import Dict, Any
import time
import json

from agents.audio_production.enhanced_audio_production_agent import EnhancedAudioProductionAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_full_audio_production")

async def test_full_audio_production():
    """
    Test the full audio production workflow using the EnhancedAudioProductionAgent.
    """
    logger.info("Testing full audio production workflow")
    
    # Set up directories
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "output")
    
    # Create test audio metadata
    audio_metadata = {
        "title": "F1 Monaco Grand Prix Review",
        "description": "A comprehensive review of the Monaco Grand Prix",
        "hosts": ["Adam", "Rachel"],
        "main_file": "intro_33062.mp3",
        "segment_files": [
            {
                "speaker": "Adam",
                "audio_file": os.path.join(output_dir, "audio", "segments", "Adam_32824_7936.mp3"),
                "duration": 7.936
            },
            {
                "speaker": "Rachel",
                "audio_file": os.path.join(output_dir, "audio", "segments", "Rachel_32826_4490.mp3"),
                "duration": 4.49
            },
            {
                "speaker": "Adam",
                "audio_file": os.path.join(output_dir, "audio", "segments", "Adam_32894_5363.mp3"),
                "duration": 5.363
            },
            {
                "speaker": "Rachel",
                "audio_file": os.path.join(output_dir, "audio", "segments", "Rachel_32894_3835.mp3"),
                "duration": 3.835
            },
            {
                "speaker": "Adam",
                "audio_file": os.path.join(output_dir, "audio", "segments", "Adam_32897_647.mp3"),
                "duration": 0.647
            }
        ],
        "total_duration": 22.271  # Sum of all segment durations
    }
    
    # Custom parameters for the production
    custom_parameters = {
        "output_format": "mp3",
        "target_loudness": -16.0,
        "eq_settings": {
            "low_shelf": {"frequency": 100, "gain": 1.5},
            "high_shelf": {"frequency": 10000, "gain": 1.0}
        },
        "compression_settings": {
            "threshold": -24.0,
            "ratio": 4.0,
            "attack": 5.0,
            "release": 50.0
        },
        "episode_number": 42
    }
    
    # Create the input data for the agent
    input_data = {
        "audio_metadata": audio_metadata,
        "custom_parameters": custom_parameters
    }
    
    # Initialize the agent
    agent = EnhancedAudioProductionAgent()
    
    try:
        # Process the audio production request
        result = await agent.process(input_data)
        
        # Print the result
        logger.info("Audio production completed successfully")
        logger.info(f"Result: {json.dumps(result, indent=2)}")
        
        # Check if the mastered file exists
        if "mastered_path" in result and os.path.exists(result["mastered_path"]):
            logger.info(f"Mastered file exists: {result['mastered_path']}")
            logger.info(f"File size: {os.path.getsize(result['mastered_path'])} bytes")
        else:
            logger.warning("Mastered file not found or not specified in the result")
        
        return result
    except Exception as e:
        logger.error(f"Error during full audio production test: {e}")
        return None

async def main():
    """
    Run the full audio production test.
    """
    logger.info("Starting full audio production test")
    
    # Test the full audio production workflow
    result = await test_full_audio_production()
    
    # Print results
    logger.info("\n\n=== TEST RESULTS ===")
    if result and not result.get("error"):
        logger.info("Full audio production test: SUCCESS")
        logger.info(f"Production metadata: {json.dumps(result, indent=2)}")
    else:
        logger.info("Full audio production test: FAILED")
        if result and result.get("error"):
            logger.info(f"Error: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())
