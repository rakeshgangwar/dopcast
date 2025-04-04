"""
Node functions for the Audio Production Agent LangGraph workflow.
Each function represents a node in the audio production workflow graph.
"""

import logging
import os
from typing import Dict, Any, List
from datetime import datetime

from ..tools.audio_mixer import AudioMixerTool
from ..tools.audio_enhancer import AudioEnhancerTool
from ..tools.metadata_generator import MetadataGeneratorTool
from ..memory.production_memory import ProductionMemory

from .state import ProductionState

# Configure logging
logger = logging.getLogger(__name__)

# Initialize tools and memory components
# These will be properly initialized in the initialize_production node
audio_mixer = None
audio_enhancer = None
metadata_generator = None
production_memory = None

def initialize_production(state: ProductionState) -> Dict[str, Any]:
    """
    Initialize the audio production workflow.

    Args:
        state: Current state

    Returns:
        Updated state
    """
    global audio_mixer, audio_enhancer, metadata_generator, production_memory

    logger.info("Initializing audio production workflow")

    try:
        input_data = state["input_data"]

        # Set up data directories
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        output_dir = os.path.join(base_dir, "output")
        production_dir = os.path.join(output_dir, "production")

        # Ensure directories exist
        os.makedirs(production_dir, exist_ok=True)

        # Initialize tools
        audio_mixer = AudioMixerTool(production_dir)
        audio_enhancer = AudioEnhancerTool(production_dir)
        metadata_generator = MetadataGeneratorTool()

        # Initialize memory components
        production_memory = ProductionMemory(production_dir)

        # Extract configuration parameters
        custom_parameters = input_data.get("custom_parameters", {})

        # Set up configuration for the workflow
        config = {
            "output_format": custom_parameters.get("output_format", "mp3"),
            "target_loudness": custom_parameters.get("target_loudness", -16.0),
            "eq_settings": custom_parameters.get("eq_settings", {
                "low_shelf": {"frequency": 100, "gain": 1.0},
                "high_shelf": {"frequency": 10000, "gain": 1.0}
            }),
            "compression_settings": custom_parameters.get("compression_settings", {
                "threshold": -24.0,
                "ratio": 4.0,
                "attack": 5.0,
                "release": 50.0
            }),
            "episode_number": custom_parameters.get("episode_number", 1)
        }

        return {"config": config}

    except Exception as e:
        logger.error(f"Error initializing audio production: {e}", exc_info=True)
        return {"error_info": f"Audio production initialization failed: {str(e)}"}

def prepare_audio_metadata(state: ProductionState) -> Dict[str, Any]:
    """
    Prepare audio metadata for production.

    Args:
        state: Current state

    Returns:
        Updated state with prepared audio metadata
    """
    logger.info("Preparing audio metadata")

    try:
        input_data = state["input_data"]
        audio_metadata = input_data.get("audio_metadata", {})

        # Validate audio metadata
        if not audio_metadata:
            logger.error("No audio metadata provided")
            return {"error_info": "No audio metadata provided"}

        logger.info(f"Prepared audio metadata for {audio_metadata.get('title', 'Untitled Episode')}")

        return {"audio_metadata": audio_metadata}

    except Exception as e:
        logger.error(f"Error preparing audio metadata: {e}", exc_info=True)
        return {"error_info": f"Audio metadata preparation failed: {str(e)}"}

def enhance_audio(state: ProductionState) -> Dict[str, Any]:
    """
    Enhance audio segments with noise reduction, EQ, and compression.

    Args:
        state: Current state

    Returns:
        Updated state with enhanced audio segments
    """
    logger.info("Enhancing audio segments")

    try:
        audio_metadata = state.get("audio_metadata", {})

        # Get segment files from audio metadata
        segment_files = audio_metadata.get("segment_files", [])

        # Enhance audio segments
        processed_segments = audio_enhancer.enhance_audio_segments(audio_metadata, segment_files)

        logger.info(f"Enhanced {len(processed_segments)} audio segments")

        return {"processed_segments": processed_segments}

    except Exception as e:
        logger.error(f"Error enhancing audio: {e}", exc_info=True)
        return {"error_info": f"Audio enhancement failed: {str(e)}"}

def mix_audio(state: ProductionState) -> Dict[str, Any]:
    """
    Mix audio segments with proper transitions and balancing.

    Args:
        state: Current state

    Returns:
        Updated state with mixed audio
    """
    logger.info("Mixing audio segments")

    try:
        audio_metadata = state.get("audio_metadata", {})
        processed_segments = state.get("processed_segments", [])
        config = state.get("config", {})

        # Extract parameters
        output_format = config.get("output_format", "mp3")

        # Mix audio segments
        mixed_audio = audio_mixer.mix_audio_segments(audio_metadata, processed_segments, output_format)

        # Apply transitions
        transition_points = []  # Would be determined from the script in a real implementation
        mixed_audio = audio_mixer.apply_transitions(mixed_audio, transition_points)

        # Normalize audio levels
        target_level = config.get("target_loudness", -16.0)
        mixed_audio = audio_mixer.normalize_audio_levels(mixed_audio, target_level)

        logger.info(f"Mixed audio with total duration: {mixed_audio['total_duration']} seconds")

        return {"mixed_audio": mixed_audio}

    except Exception as e:
        logger.error(f"Error mixing audio: {e}", exc_info=True)
        return {"error_info": f"Audio mixing failed: {str(e)}"}

def master_audio(state: ProductionState) -> Dict[str, Any]:
    """
    Master the audio for final production.

    Args:
        state: Current state

    Returns:
        Updated state with mastered audio
    """
    logger.info("Mastering audio")

    try:
        mixed_audio = state.get("mixed_audio", {})
        config = state.get("config", {})

        # Extract parameters
        eq_settings = config.get("eq_settings", {})
        compression_settings = config.get("compression_settings", {})

        # Apply equalization
        mixed_audio = audio_enhancer.apply_equalization(mixed_audio, eq_settings)

        # Apply compression
        mixed_audio = audio_enhancer.apply_compression(mixed_audio, compression_settings)

        # Master the audio
        mastering_settings = {
            "limiter_threshold": 0.95,  # Changed from -1.0 to 0.95 to be within valid range [0.0625 - 1]
            "limiter_release": 100.0
        }
        mastered_audio = audio_enhancer.master_audio(mixed_audio, mastering_settings)

        logger.info(f"Mastered audio: {mastered_audio['mastered_file']}")

        # Update mixed_audio with mastered audio information
        mixed_audio.update(mastered_audio)

        return {"mixed_audio": mixed_audio}

    except Exception as e:
        logger.error(f"Error mastering audio: {e}", exc_info=True)
        return {"error_info": f"Audio mastering failed: {str(e)}"}

def generate_metadata(state: ProductionState) -> Dict[str, Any]:
    """
    Generate metadata for the production.

    Args:
        state: Current state

    Returns:
        Updated state with production metadata
    """
    logger.info("Generating production metadata")

    try:
        audio_metadata = state.get("audio_metadata", {})
        mixed_audio = state.get("mixed_audio", {})
        config = state.get("config", {})

        # Extract parameters
        episode_number = config.get("episode_number", 1)

        # Generate ID3 tags
        id3_tags = metadata_generator.generate_id3_tags(audio_metadata, mixed_audio)

        # Generate podcast RSS entry
        rss_entry = metadata_generator.generate_podcast_rss(audio_metadata, mixed_audio, episode_number)

        # Generate complete production metadata
        production_metadata = metadata_generator.generate_production_metadata(
            audio_metadata, mixed_audio, id3_tags, rss_entry
        )

        # Add to production memory
        production_id = production_memory.add_production(production_metadata)

        # Add production ID to metadata
        production_metadata["production_id"] = production_id

        logger.info(f"Generated production metadata with ID: {production_id}")

        return {"production_metadata": production_metadata}

    except Exception as e:
        logger.error(f"Error generating metadata: {e}", exc_info=True)
        return {"error_info": f"Metadata generation failed: {str(e)}"}
