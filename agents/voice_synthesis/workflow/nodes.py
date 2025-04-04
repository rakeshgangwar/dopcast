"""
Node functions for the Voice Synthesis Agent LangGraph workflow.
Each function represents a node in the voice synthesis workflow graph.
"""

import logging
import os
import asyncio
from typing import Dict, Any, List
from datetime import datetime

from ..tools.voice_generator import VoiceGeneratorTool
from ..tools.audio_processor import AudioProcessorTool
from ..tools.emotion_detector import EmotionDetectorTool
from ..memory.voice_memory import VoiceMemory
from ..memory.audio_memory import AudioMemory

from .state import SynthesisState

# Configure logging
logger = logging.getLogger(__name__)

# Initialize tools and memory components
# These will be properly initialized in the initialize_synthesis node
voice_generator = None
audio_processor = None
emotion_detector = None
voice_memory = None
audio_memory = None

def initialize_synthesis(state: SynthesisState) -> Dict[str, Any]:
    """
    Initialize the voice synthesis workflow.
    
    Args:
        state: Current state
        
    Returns:
        Updated state
    """
    global voice_generator, audio_processor, emotion_detector, voice_memory, audio_memory
    
    logger.info("Initializing voice synthesis workflow")
    
    try:
        input_data = state["input_data"]
        
        # Set up data directories
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        audio_dir = os.path.join(base_dir, "audio")
        
        # Ensure directories exist
        os.makedirs(audio_dir, exist_ok=True)
        
        # Initialize tools
        voice_generator = VoiceGeneratorTool(audio_dir)
        audio_processor = AudioProcessorTool(audio_dir)
        emotion_detector = EmotionDetectorTool()
        
        # Initialize memory components
        voice_memory = VoiceMemory(audio_dir)
        audio_memory = AudioMemory(audio_dir)
        
        # Extract configuration parameters
        custom_parameters = input_data.get("custom_parameters", {})
        
        # Set up configuration for the workflow
        config = {
            "audio_format": custom_parameters.get("audio_format", "mp3"),
            "use_ssml": custom_parameters.get("use_ssml", False),
            "emotion_mapping": {
                "excited": {"speaking_rate": 0.2, "pitch": 1.0},
                "happy": {"speaking_rate": 0.1, "pitch": 0.5},
                "sad": {"speaking_rate": -0.1, "pitch": -0.5},
                "angry": {"speaking_rate": 0.1, "pitch": -0.3},
                "surprised": {"speaking_rate": 0.2, "pitch": 0.7},
                "analytical": {"speaking_rate": -0.1, "pitch": -0.2},
                "neutral": {"speaking_rate": 0, "pitch": 0}
            }
        }
        
        return {"config": config}
    
    except Exception as e:
        logger.error(f"Error initializing voice synthesis: {e}", exc_info=True)
        return {"error_info": f"Voice synthesis initialization failed: {str(e)}"}

def prepare_script(state: SynthesisState) -> Dict[str, Any]:
    """
    Prepare the script for voice synthesis.
    
    Args:
        state: Current state
        
    Returns:
        Updated state with prepared script
    """
    logger.info("Preparing script for voice synthesis")
    
    try:
        input_data = state["input_data"]
        script = input_data.get("script", {})
        
        # Validate script
        if not script:
            logger.error("No script provided")
            return {"error_info": "No script provided"}
        
        logger.info(f"Prepared script for {script.get('title', 'Untitled Episode')}")
        
        return {"script": script}
    
    except Exception as e:
        logger.error(f"Error preparing script: {e}", exc_info=True)
        return {"error_info": f"Script preparation failed: {str(e)}"}

def map_voices(state: SynthesisState) -> Dict[str, Any]:
    """
    Map script speakers to voice profiles.
    
    Args:
        state: Current state
        
    Returns:
        Updated state with voice mapping
    """
    logger.info("Mapping speakers to voice profiles")
    
    try:
        script = state.get("script", {})
        
        # Get all speakers from the script
        speakers = set()
        for section in script.get("sections", []):
            for line in section.get("dialogue", []):
                speaker = line.get("speaker")
                if speaker and speaker not in ["INTRO", "OUTRO", "TRANSITION"]:
                    speakers.add(speaker)
        
        # Map each speaker to a voice profile
        voice_mapping = {}
        for speaker in speakers:
            # Try to find a matching voice profile
            voice_profile = voice_memory.get_voice(speaker)
            
            if not voice_profile:
                # Use a default voice if no matching profile found
                all_voices = voice_memory.get_all_voices()
                if all_voices:
                    # Get the first available voice
                    first_voice_name = next(iter(all_voices))
                    voice_profile = voice_memory.get_voice(first_voice_name)
                else:
                    # Create a generic voice profile
                    voice_profile = {
                        "name": speaker,
                        "voice_id": "en",
                        "gender": "neutral",
                        "speaking_rate": 1.0,
                        "pitch": 0.0,
                        "volume": 1.0
                    }
            
            voice_mapping[speaker] = voice_profile
        
        logger.info(f"Mapped {len(voice_mapping)} speakers to voice profiles")
        
        return {"voice_mapping": voice_mapping}
    
    except Exception as e:
        logger.error(f"Error mapping voices: {e}", exc_info=True)
        return {"error_info": f"Voice mapping failed: {str(e)}"}

async def generate_section_audio(state: SynthesisState) -> Dict[str, Any]:
    """
    Generate audio for each section of the script.
    
    Args:
        state: Current state
        
    Returns:
        Updated state with section audio
    """
    logger.info("Generating audio for script sections")
    
    try:
        script = state.get("script", {})
        voice_mapping = state.get("voice_mapping", {})
        config = state.get("config", {})
        
        # Extract parameters
        audio_format = config.get("audio_format", "mp3")
        use_ssml = config.get("use_ssml", False)
        
        # Generate audio for each section
        section_audio = []
        
        for section in script.get("sections", []):
            section_name = section.get("name", "unnamed_section")
            logger.info(f"Generating audio for section: {section_name}")
            
            # Generate audio for each dialogue line
            segment_files = []
            
            for line in section.get("dialogue", []):
                speaker = line.get("speaker")
                text = line.get("text", "")
                
                # Skip non-speech lines
                if speaker in ["INTRO", "OUTRO", "TRANSITION"]:
                    continue
                
                # Get voice profile for this speaker
                voice_profile = voice_mapping.get(speaker, {})
                
                # Detect emotion in the text
                emotion = emotion_detector.detect_emotion(text)
                
                # Adjust voice profile based on emotion
                adjusted_profile = audio_processor.adjust_audio_parameters(voice_profile, emotion)
                
                # Generate audio for this line
                audio_info = await voice_generator.generate_audio_for_line(
                    line, adjusted_profile, emotion, audio_format, use_ssml
                )
                
                if audio_info:
                    segment_files.append(audio_info)
            
            # Generate audio for sound effects
            for effect in section.get("sound_effects", []):
                effect_info = await voice_generator.generate_sound_effect(
                    effect, section_name, audio_format
                )
                
                if effect_info:
                    segment_files.append(effect_info)
            
            # Add section audio information
            section_audio.append({
                "name": section_name,
                "segment_files": segment_files,
                "duration": sum(segment.get("duration", 0) for segment in segment_files)
            })
        
        logger.info(f"Generated audio for {len(section_audio)} sections")
        
        return {"section_audio": section_audio}
    
    except Exception as e:
        logger.error(f"Error generating section audio: {e}", exc_info=True)
        return {"error_info": f"Section audio generation failed: {str(e)}"}

def combine_audio(state: SynthesisState) -> Dict[str, Any]:
    """
    Combine section audio into a complete episode.
    
    Args:
        state: Current state
        
    Returns:
        Updated state with combined audio
    """
    logger.info("Combining audio sections")
    
    try:
        script = state.get("script", {})
        section_audio = state.get("section_audio", [])
        config = state.get("config", {})
        
        # Extract parameters
        audio_format = config.get("audio_format", "mp3")
        
        # Generate intro audio
        title = script.get("title", "Untitled Episode")
        description = script.get("description", "")
        hosts = script.get("hosts", [])
        
        # Generate intro audio asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        intro_audio = loop.run_until_complete(
            voice_generator.generate_intro_audio(title, description, hosts, audio_format)
        )
        loop.close()
        
        # Combine all audio segments
        audio_metadata = audio_processor.combine_audio_segments(
            intro_audio, section_audio, title, audio_format
        )
        
        # Add episode metadata
        audio_metadata["title"] = title
        audio_metadata["description"] = description
        audio_metadata["hosts"] = hosts
        audio_metadata["created_at"] = datetime.now().isoformat()
        
        logger.info(f"Combined audio with total duration: {audio_metadata['total_duration']} seconds")
        
        return {"audio_metadata": audio_metadata}
    
    except Exception as e:
        logger.error(f"Error combining audio: {e}", exc_info=True)
        return {"error_info": f"Audio combination failed: {str(e)}"}

def finalize_audio(state: SynthesisState) -> Dict[str, Any]:
    """
    Finalize the audio and save metadata.
    
    Args:
        state: Current state
        
    Returns:
        Updated state with finalized audio
    """
    logger.info("Finalizing audio")
    
    try:
        audio_metadata = state.get("audio_metadata", {})
        
        # Add to audio memory
        audio_id = audio_memory.add_audio(audio_metadata)
        
        # Add audio ID to metadata
        audio_metadata["audio_id"] = audio_id
        
        logger.info(f"Finalized audio with ID: {audio_id}")
        
        return {"audio_metadata": audio_metadata}
    
    except Exception as e:
        logger.error(f"Error finalizing audio: {e}", exc_info=True)
        return {"error_info": f"Audio finalization failed: {str(e)}"}

# Helper function to run async functions in a synchronous context
def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
