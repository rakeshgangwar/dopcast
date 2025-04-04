"""
Test script for the Enhanced Voice Synthesis Agent.
"""

import asyncio
import logging
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
        "hosts": ["Adam", "Rachel"],
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
                        "speaker": "Adam",
                        "text": "Welcome to DopCast! I'm Adam, and today we're discussing the F1 Monaco Grand Prix Review."
                    },
                    {
                        "speaker": "Adam",
                        "text": "Joining me as always is Rachel. Great to have you here!"
                    },
                    {
                        "speaker": "Rachel",
                        "text": "Great to be here! We've got an exciting episode lined up today."
                    },
                    {
                        "speaker": "Adam",
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
                        "speaker": "Adam",
                        "text": "Let's move on to Race Summary. The Monaco Grand Prix was absolutely thrilling this year, with Hamilton securing a dominant victory."
                    },
                    {
                        "speaker": "Rachel",
                        "text": "That's right, and I'd add that there are multiple perspectives to consider here. Looking at this from a different angle, we should also consider how this affects the competitive balance and what it means for upcoming events."
                    },
                    {
                        "speaker": "Adam",
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

    # Test input data with gTTS provider
    input_data_gtts = {
        "script": script,
        "custom_parameters": {
            "audio_format": "mp3",
            "use_ssml": False,
            "provider": "gtts"
        }
    }

    # Process the request with gTTS
    logger.info(f"Processing voice synthesis request with gTTS for: {script['title']}")
    result_gtts = await agent.process(input_data_gtts)

    # Save the gTTS result to a file for inspection
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "test_results")
    os.makedirs(output_dir, exist_ok=True)
    output_file_gtts = os.path.join(output_dir, f"audio_test_result_gtts_{timestamp}.json")

    with open(output_file_gtts, "w", encoding="utf-8") as f:
        json.dump(result_gtts, f, indent=2)

    logger.info(f"gTTS test result saved to {output_file_gtts}")

    # Print a summary of the gTTS result
    logger.info("gTTS Result summary:")
    logger.info(f"Title: {result_gtts.get('title')}")
    logger.info(f"Main audio file: {result_gtts.get('main_file')}")
    logger.info(f"Total duration: {result_gtts.get('total_duration')} seconds")
    logger.info(f"Number of segments: {len(result_gtts.get('segment_files', []))}")

    # Check if ElevenLabs API key is available
    elevenlabs_api_key = os.environ.get("ELEVENLABS_API_KEY")
    logger.info(f"ElevenLabs API key available: {bool(elevenlabs_api_key)}")

    if elevenlabs_api_key:
        # Test input data with ElevenLabs provider
        input_data_elevenlabs = {
            "script": script,
            "custom_parameters": {
                "audio_format": "mp3",
                "use_ssml": True,
                "provider": "elevenlabs",
                "elevenlabs_api_key": elevenlabs_api_key,
                "debug": True
            }
        }

        # Process the request with ElevenLabs
        logger.info(f"Processing voice synthesis request with ElevenLabs for: {script['title']}")
        result_elevenlabs = await agent.process(input_data_elevenlabs)

        # Save the ElevenLabs result to a file for inspection
        output_file_elevenlabs = os.path.join(output_dir, f"audio_test_result_elevenlabs_{timestamp}.json")

        with open(output_file_elevenlabs, "w", encoding="utf-8") as f:
            json.dump(result_elevenlabs, f, indent=2)

        logger.info(f"ElevenLabs test result saved to {output_file_elevenlabs}")

        # Print a summary of the ElevenLabs result
        logger.info("ElevenLabs Result summary:")
        logger.info(f"Title: {result_elevenlabs.get('title')}")
        logger.info(f"Main audio file: {result_elevenlabs.get('main_file')}")
        logger.info(f"Total duration: {result_elevenlabs.get('total_duration')} seconds")
        logger.info(f"Number of segments: {len(result_elevenlabs.get('segment_files', []))}")

        # Return the ElevenLabs result if available
        return result_elevenlabs
    else:
        logger.warning("ElevenLabs API key not available, skipping ElevenLabs test")

    # Return the gTTS result
    return result_gtts

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_enhanced_voice_synthesis_agent())
