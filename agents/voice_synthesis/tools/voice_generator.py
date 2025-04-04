"""
Voice generator tool for the Voice Synthesis Agent.
Provides enhanced voice generation capabilities.
"""

import logging
import os
import asyncio
from typing import Dict, Any, List, Optional
from gtts import gTTS
import tempfile

class VoiceGeneratorTool:
    """
    Enhanced voice generator tool for creating natural-sounding speech.
    """
    
    def __init__(self, audio_dir: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the voice generator tool.
        
        Args:
            audio_dir: Directory to store audio files
            config: Configuration parameters
        """
        self.logger = logging.getLogger("dopcast.voice_synthesis.voice_generator")
        self.audio_dir = audio_dir
        self.config = config or {}
        
        # Ensure audio directories exist
        os.makedirs(os.path.join(self.audio_dir, "segments"), exist_ok=True)
    
    async def generate_audio_for_line(self, line: Dict[str, Any], 
                                   voice_profile: Dict[str, Any],
                                   emotion: str, audio_format: str,
                                   use_ssml: bool) -> Dict[str, Any]:
        """
        Generate audio for a single dialogue line.
        
        Args:
            line: Dialogue line
            voice_profile: Voice profile to use
            emotion: Detected emotion
            audio_format: Audio format to generate
            use_ssml: Whether to use SSML for better control
            
        Returns:
            Information about the generated audio
        """
        speaker = line.get("speaker", "Unknown")
        text = line.get("text", "")
        
        # Skip non-speech lines (like [Theme music plays])
        if speaker in ["INTRO", "OUTRO", "TRANSITION"]:
            return None
        
        # Skip empty text
        if not text.strip():
            return None
        
        # Make sure the text is substantial enough
        if len(text.split()) < 5:
            text = f"{text} Let me elaborate on that point a bit more."
        
        # Generate filename for this segment
        timestamp = asyncio.get_event_loop().time()
        segment_filename = f"{speaker}_{int(timestamp)}_{hash(text) % 10000}.{audio_format}"
        segment_path = os.path.join(self.audio_dir, "segments", segment_filename)
        
        # Actually generate the audio using gTTS
        try:
            # Get language from voice profile
            lang = voice_profile["voice_id"]
            
            self.logger.info(f"Generating audio for {speaker} using gTTS")
            self.logger.info(f"Generating audio for: {speaker} saying '{text[:30]}...'")
            
            # Apply SSML if enabled
            if use_ssml:
                text = self._apply_ssml(text, voice_profile, emotion)
            
            # Generate audio with gTTS
            tts = gTTS(text, lang=lang, slow=False)
            tts.save(segment_path)
            
            # Estimate duration based on word count and speaking rate
            word_count = len(text.split())
            # Adjust duration calculation to account for pauses and speech
            duration_seconds = (word_count / 150) * 60 / voice_profile["speaking_rate"]
            
            return {
                "filename": segment_filename,
                "speaker": speaker,
                "duration": duration_seconds,
                "emotion": emotion,
                "path": segment_path
            }
            
        except Exception as e:
            self.logger.error(f"Error generating audio for segment: {str(e)}")
            return None
    
    async def generate_sound_effect(self, effect: Dict[str, Any], 
                                 section_name: str, audio_format: str) -> Dict[str, Any]:
        """
        Generate a sound effect.
        
        Args:
            effect: Sound effect specification
            section_name: Name of the section
            audio_format: Audio format to generate
            
        Returns:
            Information about the generated sound effect
        """
        effect_type = effect.get("type", "unknown")
        description = effect.get("description", "")
        
        # Generate filename for this effect
        timestamp = asyncio.get_event_loop().time()
        effect_filename = f"{section_name}_{effect_type}_{int(timestamp)}.{audio_format}"
        effect_path = os.path.join(self.audio_dir, "segments", effect_filename)
        
        # Create a simple sound effect file (just silence for now)
        self.logger.info(f"Would add sound effect: {effect_type} - {description}")
        
        # Create an empty file for now
        with open(effect_path, "w") as f:
            f.write("")
        
        # Estimate duration for sound effect
        effect_duration = 3.0  # Default 3 seconds for sound effects
        
        return {
            "filename": effect_filename,
            "type": "sound_effect",
            "effect_type": effect_type,
            "duration": effect_duration,
            "path": effect_path
        }
    
    async def generate_intro_audio(self, title: str, description: str, 
                                hosts: List[str], audio_format: str) -> Dict[str, Any]:
        """
        Generate audio for the episode introduction.
        
        Args:
            title: Episode title
            description: Episode description
            hosts: List of host names
            audio_format: Audio format to generate
            
        Returns:
            Information about the generated audio
        """
        # Generate a longer intro for the main episode file
        intro_text = f"Welcome to {title}. In this episode, we'll be discussing {description}. "
        
        if hosts:
            if len(hosts) == 1:
                intro_text += f"Join our host {hosts[0]} as they explore the latest developments and share their insights."
            else:
                intro_text += f"Join our hosts {', '.join(hosts[:-1])} and {hosts[-1]} as they explore the latest developments and share their insights."
        
        self.logger.info(f"Generating main episode intro")
        
        # Generate filename for the intro
        timestamp = asyncio.get_event_loop().time()
        intro_filename = f"intro_{int(timestamp)}.{audio_format}"
        intro_path = os.path.join(self.audio_dir, intro_filename)
        
        # Generate intro audio with gTTS
        tts = gTTS(intro_text, lang='en', slow=False)
        tts.save(intro_path)
        
        # Estimate duration based on word count
        intro_duration = len(intro_text.split()) / 150 * 60  # Estimate based on word count
        
        return {
            "filename": intro_filename,
            "type": "intro",
            "duration": intro_duration,
            "path": intro_path
        }
    
    def _apply_ssml(self, text: str, voice_profile: Dict[str, Any], emotion: str) -> str:
        """
        Apply Speech Synthesis Markup Language for better control.
        
        Args:
            text: Raw text
            voice_profile: Voice profile
            emotion: Detected emotion
            
        Returns:
            Text with SSML markup
        """
        # In a real implementation, this would add SSML tags for better speech control
        # For gTTS, we'll just return the original text as it doesn't support SSML
        return text
