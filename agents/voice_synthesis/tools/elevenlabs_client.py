"""
ElevenLabs API client for the Voice Synthesis Agent.
Provides integration with ElevenLabs text-to-speech API using the official SDK.
"""

import logging
import os
import requests
import time
from typing import Dict, Any, Optional, List

# Import the official ElevenLabs Python SDK
from elevenlabs import VoiceSettings, save
from elevenlabs.client import ElevenLabs as ElevenLabsClient

class ElevenLabsWrapper:
    """
    Wrapper for the official ElevenLabs Python SDK.
    """

    # Voice categories for selection
    VOICE_CATEGORIES = {
        "male_american": [],
        "female_american": [],
        "male_british": [],
        "female_british": [],
        "other": []
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

        # Initialize voice storage
        self.available_voices = {}
        self.voice_details = {}
        self.default_voice = None

        # Cache available voices
        try:
            self._cache_available_voices()
            # Set default voice after caching
            if self.available_voices:
                # Try to get a male American voice as default
                if self.VOICE_CATEGORIES["male_american"]:
                    self.default_voice = self.VOICE_CATEGORIES["male_american"][0]
                # Fall back to any available voice
                else:
                    self.default_voice = next(iter(self.available_voices.values()))
                self.logger.info(f"Set default voice to: {self.default_voice}")
            else:
                self.logger.warning("No voices available from ElevenLabs")
        except Exception as e:
            self.logger.warning(f"Failed to cache available voices: {str(e)}")

    def _cache_available_voices(self):
        """
        Cache available voices from ElevenLabs API and categorize them.
        """
        if not self.api_key:
            self.logger.warning("No API key provided, cannot fetch voices")
            return

        try:
            # Get all available voices
            response = self.client.voices.get_all()

            # Reset categories
            for category in self.VOICE_CATEGORIES:
                self.VOICE_CATEGORIES[category] = []

            # Cache voices by name and ID, and categorize them
            for voice in response.voices:
                # Store in available_voices dictionary
                self.available_voices[voice.name] = voice.voice_id
                self.available_voices[voice.voice_id] = voice.voice_id

                # Store detailed information
                self.voice_details[voice.voice_id] = {
                    "name": voice.name,
                    "voice_id": voice.voice_id,
                    "preview_url": getattr(voice, "preview_url", None),
                    "description": getattr(voice, "description", ""),
                    "labels": getattr(voice, "labels", {})
                }

                # Categorize the voice based on name and labels
                voice_name = voice.name.lower()
                labels = getattr(voice, "labels", {})
                gender = labels.get("gender", "")
                accent = labels.get("accent", "")

                # Determine gender
                is_male = False
                if gender and "male" in gender.lower():
                    is_male = True
                elif any(male_term in voice_name for male_term in ["male", "man", "guy", "boy", "adam", "sam", "josh"]):
                    is_male = True

                # Determine accent
                is_british = False
                if accent and any(brit_term in accent.lower() for brit_term in ["british", "uk", "england"]):
                    is_british = True
                elif any(brit_term in voice_name for brit_term in ["british", "uk", "england", "sam", "emily"]):
                    is_british = True

                # Categorize
                if is_male and is_british:
                    self.VOICE_CATEGORIES["male_british"].append(voice.voice_id)
                elif is_male and not is_british:
                    self.VOICE_CATEGORIES["male_american"].append(voice.voice_id)
                elif not is_male and is_british:
                    self.VOICE_CATEGORIES["female_british"].append(voice.voice_id)
                elif not is_male and not is_british:
                    self.VOICE_CATEGORIES["female_american"].append(voice.voice_id)
                else:
                    self.VOICE_CATEGORIES["other"].append(voice.voice_id)

            # Log the results
            self.logger.info(f"Cached {len(response.voices)} voices from ElevenLabs")
            for category, voices in self.VOICE_CATEGORIES.items():
                self.logger.info(f"  - {category}: {len(voices)} voices")

        except Exception as e:
            self.logger.error(f"Error caching voices from ElevenLabs: {str(e)}")

    def validate_voice_id(self, voice_id: str) -> bool:
        """
        Validate if a voice ID is available and usable with the current API key.

        Args:
            voice_id: Voice ID to validate

        Returns:
            True if voice ID is valid, False otherwise
        """
        if not self.api_key:
            self.logger.error("ElevenLabs API key is required to validate voice ID")
            return False

        if not voice_id:
            self.logger.error("No voice ID provided for validation")
            return False

        try:
            # Try to get voice details using the API
            url = f"https://api.elevenlabs.io/v1/voices/{voice_id}"
            headers = {"xi-api-key": self.api_key}

            self.logger.info(f"Validating voice ID: {voice_id}")
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                voice_data = response.json()
                self.logger.info(f"Voice ID {voice_id} is valid: {voice_data.get('name', 'Unknown')}")
                return True
            elif response.status_code == 401 or response.status_code == 403:
                self.logger.error(f"Authentication error validating voice ID: {response.text}")
                return False
            elif response.status_code == 404:
                self.logger.error(f"Voice ID {voice_id} not found")
                return False
            else:
                self.logger.error(f"Error validating voice ID {voice_id}: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error validating voice ID {voice_id}: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error validating voice ID {voice_id}: {str(e)}")
            return False

    def get_voice_id(self, voice_name_or_id: str) -> str:
        """
        Get a valid voice ID from a name or ID.

        Args:
            voice_name_or_id: Voice name or ID, or a special identifier like 'male_american'

        Returns:
            Valid voice ID or default voice ID if not found
        """
        # If no voices are available, return None
        if not self.available_voices:
            self.logger.warning("No voices available from ElevenLabs")
            return None

        # If it's a language code like 'en', use the default voice
        if voice_name_or_id in ["en", "en-US", "en-GB"]:
            self.logger.info(f"Converting language code '{voice_name_or_id}' to default voice ID")
            return self.default_voice

        # Check if it's a category request
        if voice_name_or_id in self.VOICE_CATEGORIES and self.VOICE_CATEGORIES[voice_name_or_id]:
            # Return the first voice in the requested category
            voice_id = self.VOICE_CATEGORIES[voice_name_or_id][0]
            self.logger.info(f"Using voice ID '{voice_id}' from category '{voice_name_or_id}'")
            return voice_id

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
                      similarity_boost: float = 0.5,
                      max_retries: int = 2) -> Optional[bytes]:
        """
        Convert text to speech using ElevenLabs API.

        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID or name (defaults to default_voice)
            output_path: Path to save the audio file (if None, returns bytes)
            model: Model to use (defaults to default_model)
            stability: Voice stability (0.0 to 1.0)
            similarity_boost: Voice similarity boost (0.0 to 1.0)
            max_retries: Maximum number of retries for API calls

        Returns:
            Audio data as bytes if output_path is None, otherwise True/False for success/failure
        """
        # Add a small delay before making the API call to avoid rate limiting
        # This ensures we're not making too many concurrent requests
        time.sleep(0.5)

        if not self.api_key:
            self.logger.error("ElevenLabs API key is required for text-to-speech")
            return None

        # Ensure we have text to process
        if not text or len(text.strip()) == 0:
            self.logger.error("Empty text provided for text-to-speech")
            return None

        # Get a valid voice ID
        if voice_id:
            voice_id = self.get_voice_id(voice_id)
        else:
            voice_id = self.default_voice

        if not voice_id:
            self.logger.error("No valid voice ID available")
            return None

        # Validate the voice ID
        if not self.validate_voice_id(voice_id):
            self.logger.warning(f"Voice ID {voice_id} validation failed, falling back to default voice")
            voice_id = self.default_voice
            if not voice_id or not self.validate_voice_id(voice_id):
                self.logger.error("Default voice ID is also invalid, falling back to gTTS")
                return False  # Signal to fall back to gTTS

        model = model or self.default_model

        # Log that we're about to make an API call
        self.logger.info(f"Making ElevenLabs API call for text: '{text[:30]}...' with voice ID: {voice_id}")
        self.logger.info(f"Output will be saved to: {output_path if output_path else 'memory'}")

        # First try using the direct API approach for better error handling
        for retry in range(max_retries + 1):
            try:
                # Set up the API request
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                headers = {
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg"
                }
                data = {
                    "text": text,
                    "model_id": model,
                    "voice_settings": {
                        "stability": stability,
                        "similarity_boost": similarity_boost
                    }
                }

                retry_msg = f" (retry {retry}/{max_retries})" if retry > 0 else ""
                self.logger.info(f"Making direct API call to ElevenLabs{retry_msg} for text: '{text[:30]}...' using voice ID: {voice_id}")

                # Make the API request with timeout
                response = requests.post(url, json=data, headers=headers, timeout=30)

                # Check if the request was successful
                if response.status_code == 200:
                    audio = response.content

                    # Verify we got audio content
                    if not audio or len(audio) < 100:  # Arbitrary small size check
                        self.logger.error(f"Received empty or very small audio content from ElevenLabs{retry_msg}")
                        if retry < max_retries:
                            self.logger.info(f"Retrying in {(retry+1)*2} seconds...")
                            time.sleep((retry+1) * 2)  # Exponential backoff
                            continue
                        return False  # Signal to fall back to gTTS

                    # Save to file if output path is provided
                    if output_path:
                        try:
                            # Ensure the directory exists
                            os.makedirs(os.path.dirname(output_path), exist_ok=True)

                            # Save the audio file
                            with open(output_path, 'wb') as f:
                                f.write(audio)

                            # Verify the file was created
                            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                                self.logger.info(f"Successfully saved audio to {output_path} ({os.path.getsize(output_path)} bytes)")
                                return True
                            else:
                                self.logger.error(f"Failed to save audio to {output_path} or file is empty{retry_msg}")
                                if retry < max_retries:
                                    self.logger.info(f"Retrying in {(retry+1)*2} seconds...")
                                    time.sleep((retry+1) * 2)  # Exponential backoff
                                    continue
                                return False
                        except Exception as e:
                            self.logger.error(f"Error saving audio to {output_path}{retry_msg}: {str(e)}")
                            if retry < max_retries:
                                self.logger.info(f"Retrying in {(retry+1)*2} seconds...")
                                time.sleep((retry+1) * 2)  # Exponential backoff
                                continue
                            return False

                    # Return audio data if no output path
                    return audio
                elif response.status_code == 429:
                    self.logger.error(f"ElevenLabs API rate limit exceeded{retry_msg}: {response.text}")
                    if retry < max_retries:
                        wait_time = (retry+1) * 5  # Longer wait for rate limits
                        self.logger.info(f"Rate limited. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)  # Exponential backoff
                        continue
                    self.logger.error("Max retries exceeded for rate limit, falling back to gTTS")
                    return False  # Signal to fall back to gTTS
                elif response.status_code == 401 or response.status_code == 403:
                    self.logger.error(f"ElevenLabs API authentication error{retry_msg}: {response.text}")
                    # Don't retry auth errors
                    return False  # Signal to fall back to gTTS
                else:
                    self.logger.error(f"ElevenLabs API request failed with status code {response.status_code}{retry_msg}: {response.text}")
                    if retry < max_retries:
                        self.logger.info(f"Retrying in {(retry+1)*2} seconds...")
                        time.sleep((retry+1) * 2)  # Exponential backoff
                        continue
                    return False  # Signal to fall back to gTTS

            except requests.exceptions.Timeout:
                self.logger.error(f"ElevenLabs API request timed out{retry_msg}")
                if retry < max_retries:
                    self.logger.info(f"Retrying in {(retry+1)*2} seconds...")
                    time.sleep((retry+1) * 2)  # Exponential backoff
                    continue
                return False  # Signal to fall back to gTTS
            except requests.exceptions.RequestException as e:
                self.logger.error(f"ElevenLabs API request error{retry_msg}: {str(e)}")
                if retry < max_retries:
                    self.logger.info(f"Retrying in {(retry+1)*2} seconds...")
                    time.sleep((retry+1) * 2)  # Exponential backoff
                    continue
                return False  # Signal to fall back to gTTS
            except Exception as e:
                self.logger.error(f"Error with direct API approach{retry_msg}: {str(e)}")
                if retry < max_retries:
                    self.logger.info(f"Retrying in {(retry+1)*2} seconds...")
                    time.sleep((retry+1) * 2)  # Exponential backoff
                    continue
                break

        # Fall back to using the SDK as a backup
        self.logger.info("Falling back to SDK for ElevenLabs TTS")
        try:
            # Create voice settings
            voice_settings = VoiceSettings(
                stability=stability,
                similarity_boost=similarity_boost
            )

            # Generate audio using the official SDK
            audio = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id=model,
                voice_settings=voice_settings
            )

            # Save to file if output path is provided
            if output_path:
                try:
                    # Ensure the directory exists
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)

                    # Save the audio file
                    save(audio, output_path)

                    # Verify the file was created
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        self.logger.info(f"Saved audio to {output_path} using SDK")
                        return True
                    else:
                        self.logger.error(f"Failed to save audio to {output_path} or file is empty using SDK")
                        return False
                except Exception as e:
                    self.logger.error(f"Error saving audio to {output_path} using SDK: {str(e)}")
                    return False

            # Return audio data
            return audio

        except Exception as e:
            self.logger.error(f"Error generating speech with ElevenLabs SDK: {str(e)}")
            return False  # Signal to fall back to gTTS

    def get_voices(self) -> List[Dict[str, Any]]:
        """
        Get available voices from ElevenLabs.

        Returns:
            List of available voices
        """
        if not self.api_key:
            self.logger.error("ElevenLabs API key is required to get voices")
            return []

        # If we already have cached voices, return them
        if self.voice_details:
            return list(self.voice_details.values())

        # Otherwise, fetch them from the API
        try:
            # Get voices using the official SDK
            response = self.client.voices.get_all()

            # Convert to list of dictionaries
            voice_list = []
            for voice in response.voices:
                voice_dict = {
                    "voice_id": voice.voice_id,
                    "name": voice.name,
                    "category": getattr(voice, "category", ""),
                    "description": getattr(voice, "description", ""),
                    "preview_url": getattr(voice, "preview_url", ""),
                    "labels": getattr(voice, "labels", {})
                }
                voice_list.append(voice_dict)

            return voice_list

        except Exception as e:
            self.logger.error(f"Error getting voices from ElevenLabs: {str(e)}")
            return []

    def get_voices_by_category(self, category: str = None) -> List[Dict[str, Any]]:
        """
        Get available voices by category.

        Args:
            category: Category to filter by (male_american, female_american, male_british, female_british, other)
                     If None, returns all voices

        Returns:
            List of voice details dictionaries
        """
        # If no category specified, return all voices
        if category is None:
            return self.get_voices()

        # If category doesn't exist or is empty, return empty list
        if category not in self.VOICE_CATEGORIES or not self.VOICE_CATEGORIES[category]:
            self.logger.warning(f"No voices found in category '{category}'")
            return []

        # Return voices in the specified category
        voice_list = []
        for voice_id in self.VOICE_CATEGORIES[category]:
            if voice_id in self.voice_details:
                voice_list.append(self.voice_details[voice_id])

        return voice_list

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
