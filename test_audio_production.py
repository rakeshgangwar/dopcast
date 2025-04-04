#!/usr/bin/env python3
"""
Test script for the enhanced audio production agent with FFmpeg support.
This script tests the audio stitching and mastering capabilities using real audio files.
"""

import os
import logging
import asyncio
from typing import Dict, Any, List
import time

from agents.audio_production.tools.ffmpeg_processor import FFmpegProcessor
from agents.audio_production.tools.audio_mixer import AudioMixerTool
from agents.audio_production.tools.audio_enhancer import AudioEnhancerTool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_audio_production")

async def test_audio_stitching():
    """
    Test the audio stitching functionality using the FFmpegProcessor directly.
    """
    logger.info("Testing audio stitching with FFmpegProcessor")
    
    # Set up directories
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "output")
    test_output_dir = os.path.join(output_dir, "test_results")
    os.makedirs(test_output_dir, exist_ok=True)
    
    # Initialize the FFmpeg processor
    ffmpeg_processor = FFmpegProcessor(test_output_dir)
    
    # Select some audio files to stitch
    audio_files = [
        os.path.join(output_dir, "audio", "intro_33062.mp3"),
        os.path.join(output_dir, "audio", "segments", "Adam_32824_7936.mp3"),
        os.path.join(output_dir, "audio", "segments", "Rachel_32826_4490.mp3"),
        os.path.join(output_dir, "audio", "segments", "Adam_32894_5363.mp3")
    ]
    
    # Check if files exist
    for file in audio_files:
        if not os.path.exists(file):
            logger.error(f"Audio file not found: {file}")
            return
    
    # Stitch the audio files
    output_path = os.path.join(test_output_dir, f"stitched_test_{int(time.time())}.mp3")
    try:
        stitched_file = ffmpeg_processor.stitch_audio_files(audio_files, output_path)
        logger.info(f"Successfully stitched audio files to: {stitched_file}")
        
        # Get audio information
        audio_info = ffmpeg_processor.get_audio_info(stitched_file)
        logger.info(f"Stitched audio info: {audio_info}")
        
        # Normalize the audio
        normalized_path = os.path.join(test_output_dir, f"normalized_test_{int(time.time())}.mp3")
        normalized_file = ffmpeg_processor.normalize_audio(stitched_file, normalized_path)
        logger.info(f"Successfully normalized audio to: {normalized_file}")
        
        return stitched_file, normalized_file
    except Exception as e:
        logger.error(f"Error during audio stitching test: {e}")
        return None, None

async def test_audio_production_tools():
    """
    Test the audio production tools (AudioMixerTool and AudioEnhancerTool).
    """
    logger.info("Testing audio production tools")
    
    # Set up directories
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "output")
    test_output_dir = os.path.join(output_dir, "test_results")
    production_dir = os.path.join(test_output_dir, "production")
    os.makedirs(production_dir, exist_ok=True)
    
    # Initialize the tools
    audio_mixer = AudioMixerTool(production_dir)
    audio_enhancer = AudioEnhancerTool(production_dir)
    
    # Create test audio metadata
    audio_metadata = {
        "title": "Test Podcast Episode",
        "description": "A test episode for the audio production agent",
        "main_file": "intro_33062.mp3",
        "segments": [
            {"path": os.path.join(output_dir, "audio", "segments", "Adam_32824_7936.mp3")},
            {"path": os.path.join(output_dir, "audio", "segments", "Rachel_32826_4490.mp3")},
            {"path": os.path.join(output_dir, "audio", "segments", "Adam_32894_5363.mp3")}
        ],
        "total_duration": 0  # Will be calculated by the mixer
    }
    
    # Process the audio
    try:
        # Mix audio segments
        mixed_audio = audio_mixer.mix_audio_segments(audio_metadata, [], "mp3")
        logger.info(f"Mixed audio: {mixed_audio}")
        
        # Normalize audio levels
        mixed_audio = audio_mixer.normalize_audio_levels(mixed_audio, -16.0)
        logger.info(f"Normalized audio: {mixed_audio}")
        
        # Master the audio
        mastering_settings = {
            "limiter_threshold": -1.0,
            "limiter_release": 100.0
        }
        mastered_audio = audio_enhancer.master_audio(mixed_audio, mastering_settings)
        logger.info(f"Mastered audio: {mastered_audio}")
        
        return mastered_audio
    except Exception as e:
        logger.error(f"Error during audio production tools test: {e}")
        return None

async def main():
    """
    Run all tests.
    """
    logger.info("Starting audio production tests")
    
    # Test direct FFmpeg stitching
    stitched_file, normalized_file = await test_audio_stitching()
    
    # Test audio production tools
    mastered_audio = await test_audio_production_tools()
    
    # Print results
    logger.info("\n\n=== TEST RESULTS ===")
    if stitched_file and normalized_file:
        logger.info(f"FFmpeg stitching test: SUCCESS")
        logger.info(f"Stitched file: {stitched_file}")
        logger.info(f"Normalized file: {normalized_file}")
    else:
        logger.info(f"FFmpeg stitching test: FAILED")
    
    if mastered_audio:
        logger.info(f"Audio production tools test: SUCCESS")
        logger.info(f"Mastered file: {mastered_audio['mastered_path']}")
    else:
        logger.info(f"Audio production tools test: FAILED")

if __name__ == "__main__":
    asyncio.run(main())
