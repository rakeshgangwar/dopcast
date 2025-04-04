"""
Test script for the Enhanced Script Generation Agent.
"""

import asyncio
import logging
import os
import sys
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.script_generation import EnhancedScriptGenerationAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_enhanced_script_generation_agent():
    """Test the enhanced script generation agent."""
    logger.info("Testing Enhanced Script Generation Agent")

    # Create the agent
    agent = EnhancedScriptGenerationAgent()

    # Create mock content outline
    content_outline = {
        "title": "F1 Monaco Grand Prix Review",
        "description": "A detailed analysis of the Monaco Grand Prix, including key moments and driver performances.",
        "sport": "f1",
        "episode_type": "race_review",
        "duration": 1800,  # 30 minutes
        "technical_level": "mixed",
        "host_count": 2,
        "sections": [
            {
                "name": "race_summary",
                "duration": 180,
                "talking_points": [
                    {
                        "content": "Overview of the Monaco Grand Prix results",
                        "duration": 60,
                        "host": 0
                    },
                    {
                        "content": "Key moments from the start of the race",
                        "duration": 60,
                        "host": 1
                    },
                    {
                        "content": "Final podium positions and points standings",
                        "duration": 60,
                        "host": 0
                    }
                ]
            },
            {
                "name": "driver_performances",
                "duration": 240,
                "talking_points": [
                    {
                        "content": "Hamilton's dominant performance throughout the weekend",
                        "duration": 80,
                        "host": 1
                    },
                    {
                        "content": "Verstappen's aggressive strategy and its effectiveness",
                        "duration": 80,
                        "host": 0
                    },
                    {
                        "content": "Ferrari's struggles with tire management",
                        "duration": 80,
                        "host": 1
                    }
                ]
            },
            {
                "name": "technical_insights",
                "duration": 180,
                "talking_points": [
                    {
                        "content": "Mercedes' aerodynamic advantages on the tight Monaco circuit",
                        "duration": 90,
                        "host": 1
                    },
                    {
                        "content": "Red Bull's setup choices for maximum downforce",
                        "duration": 90,
                        "host": 0
                    }
                ]
            }
        ]
    }

    # Test input data
    input_data = {
        "content_outline": content_outline,
        "custom_parameters": {
            "script_style": "conversational",
            "humor_level": "moderate",
            "include_sound_effects": True,
            "include_transitions": True
        }
    }

    # Process the request
    logger.info(f"Processing script generation request for: {content_outline['title']}")
    result = await agent.process(input_data)

    # Save the result to a file for inspection
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "test_results")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"script_test_result_{timestamp}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    logger.info(f"Test result saved to {output_file}")

    # Print a summary of the result
    logger.info("Result summary:")
    logger.info(f"Title: {result.get('title')}")
    logger.info(f"Hosts: {', '.join(result.get('hosts', []))}")
    logger.info(f"Word count: {result.get('word_count')}")
    logger.info(f"Total duration: {result.get('total_duration')} seconds")
    logger.info(f"Number of sections: {len(result.get('sections', []))}")
    logger.info(f"Output formats: {', '.join(result.get('file_paths', {}).keys())}")

    return result

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_enhanced_script_generation_agent())
