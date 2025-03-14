import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import asyncio

from agents.base_agent import BaseAgent

class VoiceSynthesisAgent(BaseAgent):
    """
    Agent responsible for converting written scripts into natural-sounding audio.
    Uses text-to-speech with realistic intonation and emphasis.
    """
    
    def __init__(self, name: str = "voice_synthesis", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the voice synthesis agent.
        
        Args:
            name: Agent identifier
            config: Configuration parameters
        """
        default_config = {
            "voice_profiles": [
                {
                    "name": "Alex",
                    "voice_id": "en-US-Neural2-A",
                    "pitch": 0,
                    "speaking_rate": 1.0,
                    "volume_gain_db": 0
                },
                {
                    "name": "Sam",
                    "voice_id": "en-US-Neural2-D",
                    "pitch": -2,
                    "speaking_rate": 0.95,
                    "volume_gain_db": 0
                }
            ],
            "default_voice": {
                "voice_id": "en-US-Neural2-F",
                "pitch": 0,
                "speaking_rate": 1.0,
                "volume_gain_db": 0
            },
            "audio_format": "mp3",
            "sample_rate": 24000,
            "use_ssml": True,  # Use Speech Synthesis Markup Language for better control
            "emotion_mapping": {
                "excited": {"pitch": 2, "speaking_rate": 1.2},
                "serious": {"pitch": -1, "speaking_rate": 0.9},
                "neutral": {"pitch": 0, "speaking_rate": 1.0}
            }
        }
        
        # Merge default config with provided config
        merged_config = default_config.copy()
        if config:
            for key, value in config.items():
                if isinstance(value, dict) and key in merged_config and isinstance(merged_config[key], dict):
                    merged_config[key].update(value)
                else:
                    merged_config[key] = value
        
        super().__init__(name, merged_config)
        
        # Initialize content storage
        self.content_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "content")
        os.makedirs(os.path.join(self.content_dir, "audio"), exist_ok=True)
        os.makedirs(os.path.join(self.content_dir, "audio", "segments"), exist_ok=True)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process script and generate audio.
        
        Args:
            input_data: Input data containing:
                - script: Script from the script generation agent
                - custom_parameters: Any custom parameters for this synthesis
        
        Returns:
            Information about the generated audio files
        """
        script = input_data.get("script", {})
        custom_parameters = input_data.get("custom_parameters", {})
        
        # Validate input data
        if not script:
            self.logger.error("No script provided")
            return {"error": "No script provided"}
        
        # Apply any custom parameters
        audio_format = custom_parameters.get("audio_format", self.config["audio_format"])
        use_ssml = custom_parameters.get("use_ssml", self.config["use_ssml"])
        
        # Generate the audio
        audio_data = await self._generate_audio(script, audio_format, use_ssml)
        
        # Save metadata
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sport = script.get("title", "").split(":")[0] if ":" in script.get("title", "") else "unknown"
        filename_base = f"{sport.lower()}_{timestamp}"
        
        metadata = {
            "title": script.get("title", "Untitled Episode"),
            "description": script.get("description", ""),
            "created_at": datetime.now().isoformat(),
            "duration": audio_data["total_duration"],
            "format": audio_format,
            "sample_rate": self.config["sample_rate"],
            "main_file": audio_data["main_file"],
            "segment_files": audio_data["segment_files"]
        }
        
        with open(os.path.join(self.content_dir, "audio", f"{filename_base}_metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
        
        return metadata
    
    async def _generate_audio(self, script: Dict[str, Any], 
                           audio_format: str, use_ssml: bool) -> Dict[str, Any]:
        """
        Generate audio from the script.
        
        Args:
            script: Complete podcast script
            audio_format: Audio format to generate
            use_ssml: Whether to use SSML for better control
            
        Returns:
            Information about the generated audio files
        """
        title = script.get("title", "Untitled Episode")
        sections = script.get("sections", [])
        hosts = script.get("hosts", [])
        
        # Map hosts to voice profiles
        voice_mapping = self._map_hosts_to_voices(hosts)
        
        # Generate audio for each section
        section_tasks = []
        for section in sections:
            section_tasks.append(self._generate_section_audio(
                section, voice_mapping, audio_format, use_ssml
            ))
        
        # Wait for all sections to be processed
        section_results = await asyncio.gather(*section_tasks)
        
        # Combine sections into a complete episode
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        episode_filename = f"{title.lower().replace(' ', '_')}_{timestamp}.{audio_format}"
        episode_path = os.path.join(self.content_dir, "audio", episode_filename)
        
        # In a real implementation, this would use audio processing libraries
        # to combine the section files and add transitions
        
        # For this example, we'll just return the metadata
        segment_files = []
        total_duration = 0
        
        for section_result in section_results:
            segment_files.extend(section_result["segment_files"])
            total_duration += section_result["duration"]
        
        # Return information about the generated audio
        return {
            "main_file": episode_filename,
            "segment_files": segment_files,
            "total_duration": total_duration
        }
    
    async def _generate_section_audio(self, section: Dict[str, Any],
                                   voice_mapping: Dict[str, Dict[str, Any]],
                                   audio_format: str, use_ssml: bool) -> Dict[str, Any]:
        """
        Generate audio for a single script section.
        
        Args:
            section: Script section
            voice_mapping: Mapping of host names to voice profiles
            audio_format: Audio format to generate
            use_ssml: Whether to use SSML for better control
            
        Returns:
            Information about the generated audio files
        """
        section_name = section.get("name", "unnamed_section")
        dialogue = section.get("dialogue", [])
        sound_effects = section.get("sound_effects", [])
        
        # In a real implementation, this would use a TTS API or library
        # to generate audio for each dialogue line
        
        # For this example, we'll simulate the process
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        segment_files = []
        total_duration = 0
        
        for i, line in enumerate(dialogue):
            speaker = line.get("speaker", "Unknown")
            text = line.get("text", "")
            
            # Skip non-speech lines (like [Theme music plays])
            if speaker in ["INTRO", "OUTRO", "TRANSITION"]:
                continue
            
            # Get voice profile for the speaker
            voice_profile = voice_mapping.get(speaker, self.config["default_voice"])
            
            # Detect emotion from text (simplified)
            emotion = self._detect_emotion(text)
            
            # Apply emotion adjustments
            adjusted_profile = self._adjust_for_emotion(voice_profile, emotion)
            
            # Prepare text with SSML if enabled
            if use_ssml:
                processed_text = self._apply_ssml(text, adjusted_profile, emotion)
            else:
                processed_text = text
            
            # Generate filename for this segment
            segment_filename = f"{section_name}_{speaker}_{i}_{timestamp}.{audio_format}"
            segment_path = os.path.join(self.content_dir, "audio", "segments", segment_filename)
            
            # In a real implementation, this would call a TTS API or library
            # For now, we'll just log what would happen
            self.logger.info(f"Would generate audio for: {speaker} saying '{text[:30]}...'")
            self.logger.info(f"Using voice profile: {voice_profile['voice_id']} with adjustments for {emotion}")
            
            # Estimate duration based on word count and speaking rate
            # Average English speaker says about 150 words per minute at rate 1.0
            word_count = len(text.split())
            duration_seconds = (word_count / 150) * 60 / adjusted_profile["speaking_rate"]
            
            segment_files.append({
                "filename": segment_filename,
                "speaker": speaker,
                "duration": duration_seconds,
                "emotion": emotion
            })
            
            total_duration += duration_seconds
        
        # Process sound effects
        for effect in sound_effects:
            effect_type = effect.get("type", "unknown")
            description = effect.get("description", "")
            
            # Generate filename for this effect
            effect_filename = f"{section_name}_{effect_type}_{timestamp}.{audio_format}"
            
            # In a real implementation, this would use sound effect libraries or recordings
            self.logger.info(f"Would add sound effect: {effect_type} - {description}")
            
            # Estimate duration for sound effect
            effect_duration = 3.0  # Default 3 seconds for sound effects
            
            segment_files.append({
                "filename": effect_filename,
                "type": "sound_effect",
                "effect_type": effect_type,
                "duration": effect_duration
            })
            
            total_duration += effect_duration
        
        return {
            "section_name": section_name,
            "segment_files": segment_files,
            "duration": total_duration
        }
    
    def _map_hosts_to_voices(self, hosts: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Map host names to voice profiles.
        
        Args:
            hosts: List of host names
            
        Returns:
            Mapping of host names to voice profiles
        """
        voice_mapping = {}
        voice_profiles = self.config["voice_profiles"]
        
        for i, host in enumerate(hosts):
            # Find a matching profile by name
            matching_profile = next((p for p in voice_profiles if p["name"] == host), None)
            
            if matching_profile:
                voice_mapping[host] = matching_profile
            elif i < len(voice_profiles):
                # Use the corresponding profile by index
                voice_mapping[host] = voice_profiles[i]
            else:
                # Use the default voice with slight variations
                default = self.config["default_voice"].copy()
                default["pitch"] += (i % 3) - 1  # Slight pitch variation
                voice_mapping[host] = default
        
        return voice_mapping
    
    def _detect_emotion(self, text: str) -> str:
        """
        Detect the emotional tone from text.
        
        Args:
            text: Dialogue text
            
        Returns:
            Detected emotion
        """
        # In a real implementation, this would use NLP or ML to detect emotion
        # Simplified keyword-based approach for demonstration
        
        excited_keywords = ["wow", "amazing", "incredible", "fantastic", "exciting", "thrilling"]
        serious_keywords = ["serious", "concerning", "important", "critical", "significant"]
        
        text_lower = text.lower()
        
        for keyword in excited_keywords:
            if keyword in text_lower:
                return "excited"
        
        for keyword in serious_keywords:
            if keyword in text_lower:
                return "serious"
        
        return "neutral"
    
    def _adjust_for_emotion(self, voice_profile: Dict[str, Any], emotion: str) -> Dict[str, Any]:
        """
        Adjust voice parameters based on detected emotion.
        
        Args:
            voice_profile: Base voice profile
            emotion: Detected emotion
            
        Returns:
            Adjusted voice profile
        """
        adjusted_profile = voice_profile.copy()
        
        # Apply emotion adjustments if available
        emotion_mapping = self.config["emotion_mapping"]
        if emotion in emotion_mapping:
            for param, value in emotion_mapping[emotion].items():
                if param in adjusted_profile:
                    adjusted_profile[param] = value
        
        return adjusted_profile
    
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
        # In a real implementation, this would apply appropriate SSML tags
        # based on the text content, punctuation, and detected emotion
        
        # Simple example for demonstration
        ssml = f"<speak>\n"
        
        # Apply prosody based on emotion
        if emotion == "excited":
            ssml += f"<prosody rate=\"fast\" pitch=\"high\">\n"
        elif emotion == "serious":
            ssml += f"<prosody rate=\"slow\" pitch=\"low\">\n"
        else:
            ssml += f"<prosody rate=\"medium\" pitch=\"medium\">\n"
        
        # Add breaks at punctuation
        processed_text = ""
        for char in text:
            if char == ".":
                processed_text += ".<break time=\"0.7s\"/>"
            elif char == ",":
                processed_text += ",<break time=\"0.3s\"/>"
            elif char == "?":
                processed_text += "?<break time=\"0.7s\"/>"
            elif char == "!":
                processed_text += "!<break time=\"0.7s\"/>"
            else:
                processed_text += char
        
        ssml += processed_text
        ssml += "\n</prosody>\n</speak>"
        
        return ssml
