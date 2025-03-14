import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import pyttsx3
import shutil
import wave
import numpy as np

from agents.base_agent import BaseAgent

class AudioProductionAgent(BaseAgent):
    """
    Agent responsible for enhancing raw audio with production elements.
    Adds intro/outro music, sound effects, and balances audio levels.
    """
    
    def __init__(self, name: str = "audio_production", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the audio production agent.
        
        Args:
            name: Agent identifier
            config: Configuration parameters
        """
        default_config = {
            "audio_assets": {
                "intro_music": "assets/audio/intro_theme.mp3",
                "outro_music": "assets/audio/outro_theme.mp3",
                "transition_effects": [
                    "assets/audio/transition_1.mp3",
                    "assets/audio/transition_2.mp3"
                ],
                "sound_effects": {
                    "race": ["assets/audio/race_sounds.mp3"],
                    "crowd": ["assets/audio/crowd_sounds.mp3"],
                    "crash": ["assets/audio/crash_sound.mp3"]
                }
            },
            "audio_processing": {
                "normalize_volume": True,
                "target_loudness": -16.0,  # LUFS
                "dynamic_range": 8.0,      # dB
                "apply_eq": True,
                "apply_compression": True,
                "add_reverb": False
            },
            "output_formats": [
                {
                    "format": "mp3",
                    "bitrate": "192k",
                    "sample_rate": 44100
                },
                {
                    "format": "ogg",
                    "quality": 6,
                    "sample_rate": 44100
                }
            ],
            "metadata_tags": {
                "artist": "DopCast AI",
                "album": "Motorsport Podcasts",
                "genre": "Sports"
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
        os.makedirs(os.path.join(self.content_dir, "audio", "final"), exist_ok=True)
        
        # Ensure assets directory exists
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "audio")
        os.makedirs(assets_dir, exist_ok=True)
        
        # Initialize TTS engine for intro/outro
        self.engine = pyttsx3.init()
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process raw audio and enhance with production elements.
        
        Args:
            input_data: Input data containing:
                - audio_metadata: Metadata from the voice synthesis agent
                - script: Original script for reference
                - custom_parameters: Any custom parameters for production
        
        Returns:
            Information about the produced podcast files
        """
        audio_metadata = input_data.get("audio_metadata", {})
        script = input_data.get("script", {})
        custom_parameters = input_data.get("custom_parameters", {})
        
        # Validate input data
        if not audio_metadata:
            self.logger.error("No audio metadata provided")
            return {"error": "No audio metadata provided"}
        
        # Apply any custom parameters
        output_formats = custom_parameters.get("output_formats", self.config["output_formats"])
        
        # Produce the final podcast
        production_data = await self._produce_podcast(
            audio_metadata, script, output_formats
        )
        
        # Save metadata
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        title = script.get("title", "Untitled Episode")
        filename_base = title.lower().replace(" ", "_").replace(":", "") + f"_{timestamp}"
        
        metadata = {
            "title": title,
            "description": script.get("description", ""),
            "produced_at": datetime.now().isoformat(),
            "duration": production_data["duration"],
            "output_files": production_data["output_files"],
            "audio_processing": self.config["audio_processing"],
            "metadata_tags": self._generate_metadata_tags(script)
        }
        
        with open(os.path.join(self.content_dir, "audio", "final", f"{filename_base}_production.json"), "w") as f:
            json.dump(metadata, f, indent=2)
        
        return metadata
    
    async def _produce_podcast(self, audio_metadata: Dict[str, Any], 
                            script: Dict[str, Any],
                            output_formats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Produce the final podcast with all production elements.
        
        Args:
            audio_metadata: Metadata from voice synthesis
            script: Original script
            output_formats: List of output formats to generate
            
        Returns:
            Information about the produced podcast
        """
        title = script.get("title", "Untitled Episode")
        segment_files = audio_metadata.get("segment_files", [])
        total_duration = audio_metadata.get("total_duration", 0)
        main_file = audio_metadata.get("main_file", "")
        
        # Create a simple intro and outro with longer pauses
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        intro_filename = f"intro_{timestamp}.mp3"
        outro_filename = f"outro_{timestamp}.mp3"
        
        intro_path = os.path.join(self.content_dir, "audio", "segments", intro_filename)
        outro_path = os.path.join(self.content_dir, "audio", "segments", outro_filename)
        
        # Generate intro and outro with slower speech rate
        rate = self.engine.getProperty('rate')
        self.engine.setProperty('rate', int(rate * 0.4))  # 40% of normal speed
        
        # Create intro with music mention
        intro_text = f"Welcome to {title}. [PAUSE] Today we'll be exploring the latest developments in the world of motorsport. [PAUSE] Let's get started."
        self.engine.save_to_file(intro_text.replace("[PAUSE]", ""), intro_path)
        self.engine.runAndWait()
        
        # Create outro with longer thank you message
        outro_text = f"Thank you for listening to {title}. [PAUSE] We hope you enjoyed this episode and gained valuable insights. [PAUSE] Please subscribe for more episodes, and join us next time for more exciting discussions. [PAUSE] This has been a DopCast production."
        self.engine.save_to_file(outro_text.replace("[PAUSE]", ""), outro_path)
        self.engine.runAndWait()
        
        # Reset rate to normal
        self.engine.setProperty('rate', rate)
        
        # Add intro and outro to segment files list with longer durations
        intro_duration = len(intro_text.split()) / 150 * 60 * 2.5  # 2.5x longer for pauses
        outro_duration = len(outro_text.split()) / 150 * 60 * 2.5  # 2.5x longer for pauses
        
        segment_files = [
            {"filename": intro_filename, "type": "intro", "duration": intro_duration, "path": intro_path}
        ] + segment_files + [
            {"filename": outro_filename, "type": "outro", "duration": outro_duration, "path": outro_path}
        ]
        
        total_duration += intro_duration + outro_duration
        
        # Generate output files for each format
        output_files = []
        
        for format_spec in output_formats:
            format_type = format_spec.get("format", "mp3")
            filename = f"{title.lower().replace(' ', '_').replace(':', '')}_{timestamp}.{format_type}"
            filepath = os.path.join(self.content_dir, "audio", "final", filename)
            
            # For this implementation, we'll use the main file from voice synthesis if available,
            # otherwise we'll use the most substantial segment file
            main_file_path = os.path.join(self.content_dir, "audio", main_file) if main_file else ""
            
            if os.path.exists(main_file_path) and os.path.getsize(main_file_path) > 0:
                self.logger.info(f"Using main file for final podcast: {main_file}")
                shutil.copy(main_file_path, filepath)
            elif segment_files:
                self.logger.info(f"Creating podcast file from best available segment: {filename}")
                
                # Find the most substantial segment file (largest file size)
                best_segment = None
                largest_size = 0
                
                for segment in segment_files:
                    path = segment.get("path", "")
                    if os.path.exists(path):
                        size = os.path.getsize(path)
                        if size > largest_size:
                            largest_size = size
                            best_segment = segment
                
                if best_segment:
                    self.logger.info(f"Using segment: {best_segment.get('filename')} as final podcast")
                    shutil.copy(best_segment.get("path"), filepath)
                    
                    output_files.append({
                        "filename": filename,
                        "format": format_type,
                        "filepath": filepath,
                        "size_estimate": self._estimate_file_size(total_duration, format_spec),
                        "actual_size": os.path.getsize(filepath) if os.path.exists(filepath) else 0,
                        "note": f"Using best available segment: {best_segment.get('filename')}"
                    })
                else:
                    self.logger.warning(f"No valid segments found")
                    
                    # Create a placeholder file
                    placeholder_text = f"Welcome to {title}. This is a placeholder for the full podcast episode about {script.get('description', 'motorsport topics')}. The complete episode will feature in-depth discussions, expert analysis, and the latest news from the world of motorsport."
                    
                    self.engine.save_to_file(placeholder_text, filepath)
                    self.engine.runAndWait()
                    
                    placeholder_duration = len(placeholder_text.split()) / 150 * 60 * 1.2  # 20% longer for pauses
                    
                    output_files.append({
                        "filename": filename,
                        "format": format_type,
                        "filepath": filepath,
                        "size_estimate": self._estimate_file_size(placeholder_duration, format_spec),
                        "actual_size": os.path.getsize(filepath) if os.path.exists(filepath) else 0,
                        "note": "Placeholder audio. No valid segments were available."
                    })
            else:
                self.logger.warning(f"No audio files available to create final podcast")
                
                # Create a more substantial placeholder file
                placeholder_text = f"Welcome to {title}. This is a placeholder for the full podcast episode about {script.get('description', 'motorsport topics')}. The complete episode will feature in-depth discussions, expert analysis, and the latest news from the world of motorsport."
                
                self.engine.save_to_file(placeholder_text, filepath)
                self.engine.runAndWait()
                
                placeholder_duration = len(placeholder_text.split()) / 150 * 60 * 1.2  # 20% longer for pauses
                
                output_files.append({
                    "filename": filename,
                    "format": format_type,
                    "filepath": filepath,
                    "size_estimate": self._estimate_file_size(placeholder_duration, format_spec),
                    "actual_size": os.path.getsize(filepath) if os.path.exists(filepath) else 0,
                    "note": "Placeholder audio. No segments were available to create a full podcast."
                })
        
        # Return information about the production
        return {
            "duration": total_duration,
            "output_files": output_files
        }
    
    def _estimate_file_size(self, duration: float, format_spec: Dict[str, Any]) -> int:
        """
        Estimate file size based on duration and format.
        
        Args:
            duration: Audio duration in seconds
            format_spec: Format specification
            
        Returns:
            Estimated file size in bytes
        """
        # Simple estimation based on format and duration
        if format_spec.get("format") == "mp3":
            bitrate = format_spec.get("bitrate", "192k")
            bitrate_value = int(bitrate.replace("k", "")) * 1000
            return int((bitrate_value / 8) * duration)  # bytes per second * duration
        
        elif format_spec.get("format") == "ogg":
            # Rough estimate for Ogg Vorbis
            quality = format_spec.get("quality", 6)
            bitrate_estimate = 64000 + (quality * 32000)  # Rough mapping of quality to bitrate
            return int((bitrate_estimate / 8) * duration)  # bytes per second * duration
        
        # Default fallback
        return int(128000 / 8 * duration)  # Assume 128 kbps
    
    def _generate_metadata_tags(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate metadata tags for the podcast.
        
        Args:
            script: Original script
            
        Returns:
            Metadata tags
        """
        base_tags = self.config["metadata_tags"].copy()
        
        # Add script-specific tags
        base_tags.update({
            "title": script.get("title", "Untitled Episode"),
            "artist": base_tags.get("artist", "DopCast AI"),
            "album": script.get("series", base_tags.get("album", "Motorsport Podcasts")),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "comment": script.get("description", "")
        })
        
        # Add hosts as contributors
        hosts = script.get("hosts", [])
        if hosts:
            base_tags["composer"] = ", ".join(hosts)
        
        return base_tags
