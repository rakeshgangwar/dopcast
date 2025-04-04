"""
Test script for the Enhanced Voice Synthesis Agent.
"""

import asyncio
import logging
import os
import sys
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.voice_synthesis import EnhancedVoiceSynthesisAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_enhanced_voice_synthesis_agent():
    """Test the enhanced voice synthesis agent."""
    logger.info("Testing Enhanced Voice Synthesis Agent")

    # Create the agent
    agent = EnhancedVoiceSynthesisAgent()

    # Create mock script
    script = {
        "title": "F1 Monaco Grand Prix Review",
        "description": "A detailed analysis of the Monaco Grand Prix, including key moments and driver performances.",
        "hosts": ["Mukesh", "Rakesh"],
        "created_at": datetime.now().isoformat(),
        "script_style": "conversational",
        "humor_level": "moderate",
        "sections": [
            {
                "name": "intro",
                "duration": 60,
                "dialogue": [
                    {
                        "speaker": "INTRO",
                        "text": "[Theme music plays]"
                    },
                    {
                        "speaker": "Mukesh",
                        "text": "Welcome to DopCast! I'm Mukesh, and today we're discussing the F1 Monaco Grand Prix Review."
                    },
                    {
                        "speaker": "Mukesh",
                        "text": "Joining me as always is Rakesh. Great to have you here!"
                    },
                    {
                        "speaker": "Rakesh",
                        "text": "Great to be here! We've got an exciting episode lined up today."
                    },
                    {
                        "speaker": "Mukesh",
                        "text": "In today's episode: A detailed analysis of the Monaco Grand Prix, including key moments and driver performances."
                    }
                ],
                "sound_effects": [
                    {
                        "type": "intro",
                        "description": "Theme music",
                        "position": 0
                    }
                ],
                "word_count": 62
            },
            {
                "name": "race_summary",
                "duration": 180,
                "dialogue": [
                    {
                        "speaker": "Mukesh",
                        "text": "Let's move on to Race Summary. The Monaco Grand Prix was absolutely thrilling this year, with Hamilton securing a dominant victory."
                    },
                    {
                        "speaker": "Rakesh",
                        "text": "That's right, and I'd add that there are multiple perspectives to consider here. Looking at this from a different angle, we should also consider how this affects the competitive balance and what it means for upcoming events."
                    },
                    {
                        "speaker": "Mukesh",
                        "text": "Absolutely! I'm so glad you brought that up. It connects directly with what I was researching earlier about how these developments are changing the landscape of the sport."
                    }
                ],
                "sound_effects": [
                    {
                        "type": "ambient",
                        "description": "Crowd murmur",
                        "position": 1
                    }
                ],
                "word_count": 95
            }
        ],
        "total_duration": 240,
        "word_count": 157,
        "sport": "f1",
        "episode_type": "race_review"
    }

    # Test input data
    input_data = {
        "script": script,
        "custom_parameters": {
            "audio_format": "mp3",
            "use_ssml": False
        }
    }

    # Process the request
    logger.info(f"Processing voice synthesis request for: {script['title']}")
    result = await agent.process(input_data)

    # Save the result to a file for inspection
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "test_results")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"audio_test_result_{timestamp}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    logger.info(f"Test result saved to {output_file}")

    # Print a summary of the result
    logger.info("Result summary:")
    logger.info(f"Title: {result.get('title')}")
    logger.info(f"Main audio file: {result.get('main_file')}")
    logger.info(f"Total duration: {result.get('total_duration')} seconds")
    logger.info(f"Number of segments: {len(result.get('segment_files', []))}")

    return result

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_enhanced_voice_synthesis_agent())
