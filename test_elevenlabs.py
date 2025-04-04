"""
Simple test script to verify ElevenLabs integration.
"""

import os
import logging
from dotenv import load_dotenv
from agents.voice_synthesis.tools.elevenlabs_client import ElevenLabsWrapper

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    """Test ElevenLabs integration."""
    # Get API key from environment
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        logger.error("No ElevenLabs API key found in environment variables")
        return
    
    logger.info(f"ElevenLabs API key found: {bool(api_key)}")
    
    # Initialize ElevenLabs client
    client = ElevenLabsWrapper(api_key=api_key)
    
    # List available voices
    logger.info("Listing available voices:")
    client.list_available_voices()
    
    # Test text-to-speech
    text = "Hello, this is a test of the ElevenLabs text-to-speech API."
    output_path = "output/test_elevenlabs.mp3"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    logger.info(f"Generating speech for text: '{text}'")
    result = client.text_to_speech(
        text=text,
        voice_id="Rachel",  # This should be converted to the actual voice ID
        output_path=output_path
    )
    
    if result:
        logger.info(f"Speech generated successfully and saved to {output_path}")
    else:
        logger.error("Failed to generate speech")

if __name__ == "__main__":
    main()
