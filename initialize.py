#!/usr/bin/env python

import os
import sys
import json
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("dopcast.initialize")

def create_directory_structure():
    """
    Create the DopCast directory structure.
    """
    directories = [
        "agents",
        "pipeline",
        "data",
        "data/cache",
        "content",
        "content/scripts",
        "content/audio",
        "content/audio/assets",
        "api",
        "web",
        "docs",
        "logs",
        "config",
        "config/sports",
        "tests"
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")

def create_default_configs():
    """
    Create default configuration files.
    """
    # Import here to avoid circular imports
    from config import create_default_configs as create_configs
    create_configs()
    logger.info("Created default configuration files")

def create_env_file():
    """
    Create a template .env file.
    """
    if os.path.exists(".env"):
        logger.info(".env file already exists, skipping")
        return

    env_content = """\
# DopCast Environment Variables

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Web UI Settings
WEB_HOST=0.0.0.0
WEB_PORT=8501

# Redis Settings (optional)
REDIS_ENABLED=false
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
#REDIS_PASSWORD=

# OpenAI API Settings
#OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4

# ElevenLabs API Settings
#ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Audio Settings
DEFAULT_AUDIO_FORMAT=mp3
DEFAULT_SAMPLE_RATE=44100
DEFAULT_BITRATE=192k
DEFAULT_VOICE_PROVIDER=gtts  # Options: gtts, elevenlabs

# Research Settings
RESEARCH_SOURCES=official,news,social
MAX_RESEARCH_DEPTH=3
"""

    with open(".env", "w") as f:
        f.write(env_content)

    logger.info("Created template .env file")

def download_audio_assets():
    """
    Download default audio assets for podcast production.
    This is a placeholder - in a real implementation, this would
    download actual audio files from a repository or CDN.
    """
    assets_dir = "content/audio/assets"
    os.makedirs(assets_dir, exist_ok=True)

    # Create placeholder files for demo purposes
    assets = [
        "intro_music.mp3",
        "outro_music.mp3",
        "transition.mp3",
        "highlight.mp3",
        "applause.mp3",
        "race_sounds.mp3"
    ]

    for asset in assets:
        asset_path = os.path.join(assets_dir, asset)
        if not os.path.exists(asset_path):
            # In a real implementation, this would download the file
            # For now, just create an empty file as a placeholder
            with open(asset_path, "wb") as f:
                f.write(b"")
            logger.info(f"Created placeholder for audio asset: {asset}")

def check_dependencies():
    """
    Check if all required dependencies are installed.
    """
    try:
        import dotenv
        import fastapi
        import uvicorn
        import openai
        import langchain
        import transformers
        import pandas
        import requests
        import bs4
        import pyttsx3
        import speech_recognition
        import librosa
        import pydub
        import streamlit
        import pytest

        logger.info("All required dependencies are installed")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {str(e)}")
        logger.error("Please install all dependencies with: pip install -r requirements.txt")
        return False

def initialize_system(force=False):
    """
    Initialize the DopCast system.

    Args:
        force: Force reinitialization even if the system is already initialized
    """
    # Check if system is already initialized
    if os.path.exists(".initialized") and not force:
        logger.info("DopCast system is already initialized. Use --force to reinitialize.")
        return

    logger.info("Initializing DopCast system...")

    # Create directory structure
    create_directory_structure()

    # Create default configurations
    create_default_configs()

    # Create .env file template
    create_env_file()

    # Download audio assets
    download_audio_assets()

    # Check dependencies
    if not check_dependencies():
        logger.warning("Some dependencies are missing. System may not function correctly.")

    # Mark as initialized
    with open(".initialized", "w") as f:
        f.write(datetime.now().isoformat())

    logger.info("DopCast system initialized successfully")

def main():
    parser = argparse.ArgumentParser(description="Initialize the DopCast system")
    parser.add_argument("--force", action="store_true", help="Force reinitialization")
    args = parser.parse_args()

    initialize_system(args.force)

if __name__ == "__main__":
    main()
