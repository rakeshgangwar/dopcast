"""
ElevenLabs API client for the Voice Synthesis Agent.
Provides integration with ElevenLabs text-to-speech API using the official SDK.
"""

import logging
import os
from typing import Dict, Any, Optional, List

# Import the official ElevenLabs Python SDK
from elevenlabs import VoiceSettings, save
from elevenlabs.client import ElevenLabs as ElevenLabsClient

class ElevenLabsWrapper:
    """
    Wrapper for the official ElevenLabs Python SDK.
    """

    # Default voice IDs for common voices
    DEFAULT_VOICES = {
        "Rachel": "21m00Tcm4TlvDq8ikWAM",  # Female, American
        "Adam": "pNInz6obpgDQGcFmaJgB",    # Male, American
        "Sam": "yoZ06aMxZJJ28mfd3POQ",     # Male, British
        "Emily": "EXAVITQu4vr4xnSDxMaL"    # Female, British
    }

    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the ElevenLabs API client.

        Args:
            api_key: ElevenLabs API key (defaults to ELEVENLABS_API_KEY env var)
            config: Configuration parameters
        """
        self.logger = logging.getLogger("dopcast.voice_synthesis.elevenlabs_client")
        self.config = config or {}

        # Get API key from config, parameter, or environment
        env_api_key = os.environ.get("ELEVENLABS_API_KEY", "")
        config_api_key = self.config.get("api_key", "")
        self.logger.info(f"ElevenLabs API key from env: {bool(env_api_key)}, from config: {bool(config_api_key)}")

        self.api_key = api_key or config_api_key or env_api_key
        if not self.api_key:
            self.logger.warning("No ElevenLabs API key provided. Set ELEVENLABS_API_KEY environment variable or pass in config.")
        else:
            self.logger.info("ElevenLabs API key found and will be used for requests")

        # Initialize the official ElevenLabs client
        self.client = ElevenLabsClient(api_key=self.api_key)

        # Default settings
        self.default_model = self.config.get("model", "eleven_multilingual_v2")
        self.default_voice = self.config.get("default_voice", self.DEFAULT_VOICES["Rachel"])  # Default voice ID (Rachel)

        # Cache available voices
        self.available_voices = {}
        try:
            self._cache_available_voices()
        except Exception as e:
            self.logger.warning(f"Failed to cache available voices: {str(e)}")

    def _cache_available_voices(self):
        """
        Cache available voices from ElevenLabs API.
        """
        if not self.api_key:
            return

        try:
            # Get all available voices
            response = self.client.voices.get_all()

            # Cache voices by name and ID
            for voice in response.voices:
                self.available_voices[voice.name] = voice.voice_id
                self.available_voices[voice.voice_id] = voice.voice_id

            self.logger.info(f"Cached {len(response.voices)} voices from ElevenLabs")
        except Exception as e:
            self.logger.error(f"Error caching voices from ElevenLabs: {str(e)}")

    def get_voice_id(self, voice_name_or_id: str) -> str:
        """
        Get a valid voice ID from a name or ID.

        Args:
            voice_name_or_id: Voice name or ID

        Returns:
            Valid voice ID or default voice ID if not found
        """
        # If it's a language code like 'en', use the default voice
        if voice_name_or_id in ["en", "en-US", "en-GB"]:
            self.logger.info(f"Converting language code '{voice_name_or_id}' to default voice ID")
            return self.default_voice

        # Check if it's in our default voices
        if voice_name_or_id in self.DEFAULT_VOICES:
            return self.DEFAULT_VOICES[voice_name_or_id]

        # Check if it's in our cached voices
        if voice_name_or_id in self.available_voices:
            return self.available_voices[voice_name_or_id]

        # If we can't find it, use the default voice
        self.logger.warning(f"Voice '{voice_name_or_id}' not found, using default voice")
        return self.default_voice

    def text_to_speech(self, text: str, voice_id: Optional[str] = None,
                      output_path: Optional[str] = None,
                      model: Optional[str] = None,
                      stability: float = 0.5,
                      similarity_boost: float = 0.5) -> Optional[bytes]:
        """
        Convert text to speech using ElevenLabs API.

        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID or name (defaults to default_voice)
            output_path: Path to save the audio file (if None, returns bytes)
            model: Model to use (defaults to default_model)
            stability: Voice stability (0.0 to 1.0)
            similarity_boost: Voice similarity boost (0.0 to 1.0)

        Returns:
            Audio data as bytes if output_path is None, otherwise None
        """
        if not self.api_key:
            self.logger.error("ElevenLabs API key is required for text-to-speech")
            return None

        # Get a valid voice ID
        if voice_id:
            voice_id = self.get_voice_id(voice_id)
        else:
            voice_id = self.default_voice

        model = model or self.default_model

        try:
            # Create voice settings
            voice_settings = VoiceSettings(
                stability=stability,
                similarity_boost=similarity_boost
            )

            # Generate audio using the official SDK
            self.logger.info(f"Generating speech with ElevenLabs for text: '{text[:30]}...' using voice ID: {voice_id}")

            audio = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id=model,
                voice_settings=voice_settings
            )

            # Save to file if output path is provided
            if output_path:
                save(audio, output_path)
                self.logger.info(f"Saved audio to {output_path}")
                return True

            # Return audio data
            return audio

        except Exception as e:
            self.logger.error(f"Error generating speech with ElevenLabs: {str(e)}")
            return None

    def get_voices(self) -> List[Dict[str, Any]]:
        """
        Get available voices from ElevenLabs.

        Returns:
            List of available voices
        """
        if not self.api_key:
            self.logger.error("ElevenLabs API key is required to get voices")
            return []

        try:
            # Get voices using the official SDK
            response = self.client.voices.get_all()

            # Convert to list of dictionaries
            voice_list = []
            for voice in response.voices:
                voice_dict = {
                    "voice_id": voice.voice_id,
                    "name": voice.name,
                    "category": voice.category,
                    "description": voice.description,
                    "preview_url": voice.preview_url,
                    "labels": voice.labels
                }
                voice_list.append(voice_dict)

            return voice_list

        except Exception as e:
            self.logger.error(f"Error getting voices from ElevenLabs: {str(e)}")
            return []

    def list_available_voices(self) -> None:
        """
        Print a list of available voices for debugging purposes.
        """
        if not self.api_key:
            self.logger.error("ElevenLabs API key is required to list voices")
            return

        try:
            # Get voices using the official SDK
            response = self.client.voices.get_all()

            # Print voice information
            self.logger.info(f"Available voices ({len(response.voices)}):\n")
            for voice in response.voices:
                self.logger.info(f"Name: {voice.name}")
                self.logger.info(f"ID: {voice.voice_id}")
                self.logger.info(f"Category: {voice.category}")
                self.logger.info(f"Description: {voice.description}")
                self.logger.info("---")

        except Exception as e:
            self.logger.error(f"Error listing voices from ElevenLabs: {str(e)}")

    def get_voice_settings(self, voice_id: str) -> Dict[str, Any]:
        """
        Get settings for a specific voice.

        Args:
            voice_id: ElevenLabs voice ID

        Returns:
            Voice settings
        """
        if not self.api_key:
            self.logger.error("ElevenLabs API key is required to get voice settings")
            return {}

        try:
            # Get voice settings using the official SDK
            settings = self.client.voices.get_settings(voice_id)

            # Convert to dictionary
            settings_dict = {
                "stability": settings.stability,
                "similarity_boost": settings.similarity_boost,
                "style": settings.style,
                "use_speaker_boost": settings.use_speaker_boost
            }

            return settings_dict

        except Exception as e:
            self.logger.error(f"Error getting voice settings from ElevenLabs: {str(e)}")
            return {}
